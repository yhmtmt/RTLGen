import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.eval.probe_attention_score32_exact_banked_finalized_tree import build_report
from npu.rtlgen.gen_attention_score32_exact_banked_finalized_tree import generate
from npu.sim.perf.attention_exact_partial import (
    ExactPartialBeat,
    merge_balanced_partial_streams,
    partial_stream_from_blocks,
    simulate_exact_banked_finalizer,
)


def _rtl_tools_available() -> bool:
    return bool(shutil.which("iverilog") and shutil.which("vvp") and shutil.which("verilator"))


def _tool(name: str) -> str:
    path = shutil.which(name)
    if path:
        return path
    fallback = Path("/oss-cad-suite/bin") / name
    if fallback.exists():
        return str(fallback)
    raise RuntimeError(f"required tool unavailable: {name}")


def _config(finalizer_banks: int, *, clusters: int = 16, divider_lanes: int = 8) -> dict[str, object]:
    return {
        "top_name": f"attention_score32_exact_banked_finalized_tree_c{clusters}_r2_l{divider_lanes}_b{finalizer_banks}",
        "attention_score32_exact_banked_finalized_tree": {
            "clusters": clusters,
            "radix": 2,
            "value_slices": 16,
            "head_id_bits": 5,
            "divider_lanes": divider_lanes,
            "finalizer_banks": finalizer_banks,
        },
    }


def _commands(heads: int) -> tuple[dict[str, int], ...]:
    return tuple({"command_id": 0x5A00 + head_index, "head_id": head_index} for head_index in range(heads))


def _score_rows(leaf: int, command_index: int) -> tuple[tuple[int, ...], ...]:
    return tuple(
        tuple(
            ((leaf * 43 + command_index * 29 + block * 17 + lane * 11) % 255) - 127 + (14 if lane == block else 0)
            for lane in range(8)
        )
        for block in range(3)
    )


def _value_blocks(leaf: int, command_index: int) -> tuple[tuple[tuple[tuple[int, ...], ...], ...], ...]:
    return tuple(
        tuple(
            tuple(
                tuple(
                    ((leaf * 59 + command_index * 31 + block * 23 + value_slice * 13 + row * 7 + lane * 5) % 255)
                    - 127
                    for lane in range(8)
                )
                for row in range(8)
            )
            for value_slice in range(16)
        )
        for block in range(3)
    )


def _leaf_stream(leaf: int, *, heads: int) -> tuple[ExactPartialBeat, ...]:
    beats: list[ExactPartialBeat] = []
    for command_index, command in enumerate(_commands(heads)):
        beats.extend(
            partial_stream_from_blocks(
                command_id=int(command["command_id"]),
                head_id=int(command["head_id"]),
                score_rows=_score_rows(leaf, command_index),
                value_blocks=_value_blocks(leaf, command_index),
            )
        )
    return tuple(beats)


@pytest.mark.skipif(not _rtl_tools_available(), reason="RTL tools unavailable")
def test_banked_finalized_tree_manifest_and_verilator_lint(tmp_path: Path) -> None:
    cfg = _config(59, clusters=16, divider_lanes=8)
    generate(cfg, tmp_path / "rtl")

    manifest = json.loads(
        (tmp_path / "rtl" / "attention_score32_exact_banked_finalized_tree_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert manifest["finalizer_banks"] == 59
    assert manifest["order_fifo_depth"] == 59
    assert manifest["actual_finalizer_accept_interval_cycles"] == 59
    assert manifest["service_model"]["minimum_banks_for_wrap_free_lane8_service"] == 59
    assert manifest["direct_328bit_links_unclosed"] is True
    assert manifest["final_divider_embodied"] is True
    assert manifest["noc_closure"] is False
    assert manifest["sram_closure"] is False

    lint = subprocess.run(
        [
            _tool("verilator"),
            "--lint-only",
            "--top-module",
            str(cfg["top_name"]),
            str(tmp_path / "rtl" / "top.v"),
        ],
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert lint.returncode == 0, lint.stderr


def test_banked_finalized_tree_rejects_invalid_bank_counts(tmp_path: Path) -> None:
    for banks in (0, 65):
        with pytest.raises(SystemExit, match="finalizer_banks must be in \\[1, 64\\]"):
            generate(_config(banks), tmp_path / f"rtl_{banks}")


@pytest.mark.skipif(not _rtl_tools_available(), reason="RTL tools unavailable")
@pytest.mark.parametrize("finalizer_banks", [1, 16, 32, 57, 58, 59, 64])
def test_banked_finalized_tree_small_probe_all_checked_in_bank_counts(finalizer_banks: int) -> None:
    report = build_report(clusters=2, heads=1, divider_lanes=8, finalizer_banks=finalizer_banks)

    assert report["passed"] is True
    assert report["outputs"] == 16
    assert report["finalizer_accepted_count"] == 16
    assert report["tree_root_completed_count"] == 16
    assert report["per_bank_accept_interval_cycles"] == 59
    assert report["measured_workload_manifest"]["minimum_banks_for_wrap_free_lane8_service"] == 59


@pytest.mark.skipif(not _rtl_tools_available(), reason="RTL tools unavailable")
@pytest.mark.parametrize("finalizer_banks", [1, 59])
def test_banked_finalized_tree_full_c16_heads32_exact_regression(finalizer_banks: int) -> None:
    report = build_report(
        clusters=16,
        heads=32,
        divider_lanes=8,
        finalizer_banks=finalizer_banks,
        saturated=True,
        output_ready_pattern=(True,),
    )

    assert report["passed"] is True
    assert report["outputs"] == 512
    assert report["finalizer_accepted_count"] == 512
    assert report["tree_root_completed_count"] == 512
    assert report["leaf_accept_count"] == [512] * 16
    assert report["measured_workload_manifest"]["measured_heads"] == 32
    assert report["measured_workload_manifest"]["total_leaf_beats"] == 8192
    assert report["observed_root_hash"] == "027dd06c1e4e1bc77636eb4041aa7efd4fd6e55a090b337a6d33f78da89f65bd"


@pytest.mark.skipif(not _rtl_tools_available(), reason="RTL tools unavailable")
def test_banked_finalized_tree_root_backpressure_order_stress() -> None:
    report = build_report(
        clusters=4,
        heads=4,
        divider_lanes=8,
        finalizer_banks=57,
        saturated=True,
        output_ready_pattern=(True, False, True, True, False, True, False, True, True, True),
    )

    assert report["passed"] is True
    assert report["protocol_error"] is False
    assert report["order_protocol_error"] is False
    assert report["finalizer_protocol_error"] is False


@pytest.mark.skipif(not _rtl_tools_available(), reason="RTL tools unavailable")
def test_banked_finalized_tree_non_power_of_two_pointer_wrap() -> None:
    report = build_report(
        clusters=4,
        heads=4,
        divider_lanes=8,
        finalizer_banks=57,
        saturated=True,
        output_ready_pattern=(True,),
    )

    assert report["passed"] is True
    assert report["outputs"] == 64
    assert report["order_fifo_high_watermark"] <= 57


@pytest.mark.skipif(not _rtl_tools_available(), reason="RTL tools unavailable")
def test_bank59_is_first_wrap_free_lane8_point_under_saturated_no_stall() -> None:
    bank57 = build_report(
        clusters=2,
        heads=5,
        divider_lanes=8,
        finalizer_banks=57,
        saturated=True,
        output_ready_pattern=(True,),
    )
    bank58 = build_report(
        clusters=2,
        heads=5,
        divider_lanes=8,
        finalizer_banks=58,
        saturated=True,
        output_ready_pattern=(True,),
    )
    bank59 = build_report(
        clusters=2,
        heads=5,
        divider_lanes=8,
        finalizer_banks=59,
        saturated=True,
        output_ready_pattern=(True,),
    )
    bank64 = build_report(
        clusters=2,
        heads=5,
        divider_lanes=8,
        finalizer_banks=64,
        saturated=True,
        output_ready_pattern=(True,),
    )

    for report in (bank57, bank58, bank59, bank64):
        assert report["passed"] is True

    interval57 = bank57["measured_workload_manifest"]["measured_root_output_interval_cycles"]
    interval58 = bank58["measured_workload_manifest"]["measured_root_output_interval_cycles"]
    interval59 = bank59["measured_workload_manifest"]["measured_root_output_interval_cycles"]
    interval64 = bank64["measured_workload_manifest"]["measured_root_output_interval_cycles"]

    assert interval57 > interval58 > interval59
    assert interval59 == interval64


def test_bank_wrap_boundary_full_wave_perf_model() -> None:
    merged = merge_balanced_partial_streams([_leaf_stream(leaf, heads=32) for leaf in range(16)])
    bank57 = simulate_exact_banked_finalizer(merged, divider_lanes=8, finalizer_banks=57, output_ready_pattern=(True,))
    bank58 = simulate_exact_banked_finalizer(merged, divider_lanes=8, finalizer_banks=58, output_ready_pattern=(True,))
    bank59 = simulate_exact_banked_finalizer(merged, divider_lanes=8, finalizer_banks=59, output_ready_pattern=(True,))
    bank64 = simulate_exact_banked_finalizer(merged, divider_lanes=8, finalizer_banks=64, output_ready_pattern=(True,))

    assert bank57["completed_count"] == 512
    assert bank58["completed_count"] == 512
    assert bank59["completed_count"] == 512
    assert bank64["completed_count"] == 512
    assert bank57["result_events"][-1]["cycle"] - bank57["result_events"][0]["cycle"] == 527
    assert bank58["result_events"][-1]["cycle"] - bank58["result_events"][0]["cycle"] == 519
    assert bank59["result_events"][-1]["cycle"] - bank59["result_events"][0]["cycle"] == 511
    assert bank64["result_events"][-1]["cycle"] - bank64["result_events"][0]["cycle"] == 511


@pytest.mark.skipif(not _rtl_tools_available(), reason="RTL tools unavailable")
def test_banked_probe_script_runs_without_pythonpath() -> None:
    env = {key: value for key, value in os.environ.items() if key != "PYTHONPATH"}
    run = subprocess.run(
        [
            sys.executable,
            "npu/eval/probe_attention_score32_exact_banked_finalized_tree.py",
            "--clusters",
            "2",
            "--heads",
            "1",
            "--divider-lanes",
            "8",
            "--finalizer-banks",
            "59",
            "--json",
        ],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=240,
    )
    assert run.returncode == 0, run.stderr
    payload = json.loads(run.stdout)
    assert payload["passed"] is True
    assert payload["finalizer_banks"] == 59
