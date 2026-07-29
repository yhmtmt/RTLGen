import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.eval import probe_attention_score32_exact_local16_global_tree_gqa8 as full_probe
from npu.eval.probe_attention_score32_exact_local16_global_tree_cluster_sram_gqa8 import (
    DIAGNOSTIC_TAIL_LIMIT,
    MARKDOWN_DIAGNOSTIC_TAIL_LIMIT,
    COMPOSITIONAL_ICARUS_BACKEND,
    DEFAULT_ROOT_READY_PATTERN,
    DEFAULT_SIM_BACKEND,
    DEFAULT_SUBPROCESS_TIMEOUT_SEC,
    DEFAULT_VERILATOR_COMPILE_TIMEOUT_SEC,
    EXPECTED_PER_CLUSTER,
    EXPECTED_TOTALS,
    FINE_COMPOSITIONAL_ICARUS_BACKEND,
    ROWS_PER_BUFFER,
    SIM_BACKEND_CHOICES,
    TB_TIMEOUT_CYCLES,
    VERILATOR_BUILD_JOBS,
    VERILATOR_HIERARCHICAL_BACKEND,
    build_report,
    _evaluate_observations,
    _failure_classification,
    _fill_rows_for_wave,
    _hierarchical_module_names,
    _icarus_compile_command,
    _parse_stdout,
    _render_text,
    _testbench,
    _verilator_control_file_text,
    _verilator_hierarchical_compile_command,
    _write_memh_sidecars,
    compare_compositional_rows,
    compare_full_rows,
    expected_counts,
    expected_schedule_prefix,
    main,
)
from npu.eval.gqa8_compositional_exact import (
    BACKEND as COMPOSITIONAL_RUNNER_BACKEND,
    _pack_global_row,
    _run_process,
    _write_global_sidecar,
    cluster_testbench,
    extract_module_family,
    global_testbench,
)
from npu.eval.gqa8_fine_compositional_exact import (
    BACKEND as FINE_COMPOSITIONAL_RUNNER_BACKEND,
    _check_request_metadata,
    _check_sram_responses,
    _parse_producer,
    _parse_reducer,
    component_module_names,
    producer_testbench,
    sram_testbench,
)
from npu.rtlgen.gen_attention_score32_exact_local16_global_tree_cluster_sram_gqa8 import _validate
from npu.sim.perf.attention_exact_partial import (
    ExactPartialBeat,
    finalize_partial_beats,
    merge_balanced_partial_streams,
    pack_final_values,
    pack_numerators,
)


def _design_dir() -> Path:
    return (
        REPO_ROOT
        / "runs"
        / "designs"
        / "npu_blocks"
        / "attention_score32_exact_local16_global_tree_cluster_sram_gqa8_p54x8_p53x8_c16_r2_l8_b59"
    )


def _rtl_dir() -> Path:
    return _design_dir() / "verilog"


def _sample_rows() -> list[dict[str, object]]:
    return [
        {
            "command_id": 0x8200,
            "head_id": 3,
            "slice": 7,
            "last": False,
            "global_max": -11,
            "exp_sum": 991,
            "value": [3, -2, 7, 0, 19, -5, 4, 8],
        },
        {
            "command_id": 0x8200,
            "head_id": 3,
            "slice": 8,
            "last": False,
            "global_max": -8,
            "exp_sum": 1012,
            "value": [4, -1, 8, 1, 20, -4, 5, 9],
        },
    ]


def test_full_row_comparator_accepts_exact_rows_and_rejects_one_field_mismatch() -> None:
    expected = _sample_rows()
    exact = compare_full_rows(expected, copy.deepcopy(expected))
    assert exact["passed"] is True
    assert exact["first_mismatch"] is None

    mismatched = copy.deepcopy(expected)
    mismatched[1]["exp_sum"] = 1013
    rejected = compare_full_rows(expected, mismatched)
    assert rejected["passed"] is False
    assert rejected["first_mismatch"] == {
        "row": 1,
        "field": "exp_sum",
        "expected": 1012,
        "observed": 1013,
    }
    assert rejected["expected_hash"] != rejected["observed_hash"]


def test_compositional_comparator_requires_all_cluster_and_root_rows() -> None:
    cluster_rows = [[{"cluster": cluster, "value": cluster}] for cluster in range(16)]
    root_rows = [{"command_id": 1, "head_id": 0, "slice": 0, "last": True, "value": [1] * 16}]
    exact = compare_compositional_rows(
        expected_cluster_rows=cluster_rows,
        observed_cluster_rows=copy.deepcopy(cluster_rows),
        expected_root_rows=root_rows,
        observed_root_rows=copy.deepcopy(root_rows),
    )
    assert exact["passed"] is True

    observed_clusters = copy.deepcopy(cluster_rows)
    observed_clusters[9][0]["value"] = -1
    rejected = compare_compositional_rows(
        expected_cluster_rows=cluster_rows,
        observed_cluster_rows=observed_clusters,
        expected_root_rows=root_rows,
        observed_root_rows=root_rows,
    )
    assert rejected["passed"] is False
    assert rejected["clusters"][9]["first_mismatch"]["field"] == "value"


def test_schedule_prefix_is_group_major_and_wraps_cleanly() -> None:
    schedule = expected_schedule_prefix(command_count=12)
    assert schedule[:8] == ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6), (0, 7))
    assert schedule[8:12] == ((8, 0), (8, 1), (8, 2), (8, 3))
    assert expected_schedule_prefix(command_count=32)[31] == (24, 7)
    assert expected_schedule_prefix(command_count=33)[32] == (0, 0)


def test_expected_counts_scale_to_four_head_groups() -> None:
    scaled = expected_counts(logical_head_groups=4)
    assert scaled["totals"] == {
        "fill_target_accept_count": 512,
        "fill_row_accept_count": 1048576,
        "producer_handshake_count": 32768,
        "sram_request_accept_count": 1048576,
        "sram_response_accept_count": 1048576,
        "cluster_row_count": 8192,
        "root_row_count": 512,
    }
    assert scaled["per_cluster"][0] == {
        "wave_command_accept_count": 32,
        "completed_command_count": 4,
        "emitted_beat_count": 512,
        "fill_target_accept_count": 32,
        "fill_row_accept_count": 65536,
        "request_accept_count": 65536,
        "response_accept_count": 65536,
        "command_accept_count": 32,
        "command_release_count": 32,
    }


def test_generated_testbench_is_real_memh_backed_composed_traffic() -> None:
    tb = _testbench(
        top_name="attention_score32_exact_local16_global_tree_cluster_sram_gqa8_test",
    )

    assert 'localparam integer CLUSTERS = 16;' in tb
    assert 'localparam integer WAVES = 8;' in tb
    assert 'localparam integer TOTAL_PRODUCERS = 856;' in tb
    assert 'localparam integer TB_TIMEOUT_CYCLES = 50000;' in tb
    assert '$readmemh("query.memh", query_mem);' in tb
    assert '$readmemh("key.memh", key_mem);' in tb
    assert '$readmemh("fill.memh", fill_mem);' in tb
    assert "input_valid[producer_index] = 1'b1;" in tb
    assert "input_query = '0;" in tb
    assert "input_key = '0;" in tb
    assert "109568'd0" not in tb
    assert "input_query[(producer_index * 128) +: 128] = query_mem[flat_index];" in tb
    assert "input_key[(producer_index * 128) +: 128] = key_mem[flat_index];" in tb
    assert "input_valid[producer_index] && input_ready[producer_index]" in tb
    assert "$countones(input_valid & input_ready)" in tb
    assert "fill_target_valid[cluster_index] = 1'b1;" in tb
    assert "fill_target_buffer_sel[cluster_index] = wave_index_mem[fill_command_index[cluster_index]][0];" in tb
    assert "fill_valid[cluster_index] = 1'b1;" in tb
    assert "fill_data[(cluster_index * 512) +: 512] = fill_mem[fill_flat_index];" in tb
    assert "fill_target_valid[cluster_index] && fill_target_ready[cluster_index]" in tb
    assert "fill_valid[cluster_index] && fill_ready[cluster_index]" in tb
    assert "fill_command_index[cluster_index] < ((WAVE_COMMANDS < 2) ? WAVE_COMMANDS : 2)" in tb
    assert "fill_command_index[cluster_index] <= prefetch_limit_index" in tb
    assert "command_id = command_valid ? command_id_mem[issued_commands] : 16'd0;" in tb
    assert "command_head_base = command_valid ? head_base_mem[issued_commands] : 5'd0;" in tb
    assert "issued_commands < WAVE_COMMANDS" in tb
    assert "dut.cluster_out_valid_w" in tb
    assert "dut.cluster_out_ready_w" in tb
    assert "ROOT_RESULT" in tb
    assert "CLUSTER_RESULT" in tb
    assert "if (cycle >= TB_TIMEOUT_CYCLES)" in tb
    assert "root_ready_mem[0] = 1'b1;" in tb
    assert "root_ready_mem[1] = 1'b1;" in tb
    assert "root_ready_mem[2] = 1'b0;" in tb
    assert "root_ready_mem[3] = 1'b1;" in tb


def test_generated_testbench_supports_four_group_rotation_schedule() -> None:
    tb = _testbench(
        top_name="attention_score32_exact_local16_global_tree_cluster_sram_gqa8_test",
        logical_head_groups=4,
    )

    assert "localparam integer WAVE_COMMANDS = 32;" in tb
    assert "localparam integer EXPECTED_ROOT_ROWS = 512;" in tb
    assert "localparam integer TB_TIMEOUT_CYCLES = 200000;" in tb
    assert "command_id_mem[0] = 16'h8200;" in tb
    assert "command_id_mem[8] = 16'h8201;" in tb
    assert "command_id_mem[16] = 16'h8202;" in tb
    assert "command_id_mem[24] = 16'h8203;" in tb
    assert "head_base_mem[8] = 5'd8;" in tb
    assert "head_base_mem[16] = 5'd16;" in tb
    assert "head_base_mem[24] = 5'd24;" in tb
    assert "cmd_beat_limit_mem[31][855]" in tb
    assert "fill_mem [0:(CLUSTERS*WAVE_COMMANDS*ROWS_PER_TARGET)-1];" in tb
    assert "fill_command_index[cluster_index] <= prefetch_limit_index" in tb


def test_fill_sidecar_layout_uses_exact_p54_and_p53_block_slots(monkeypatch: Any) -> None:
    def fake_value_blocks(*, producer: int, block_count: int, **_: object) -> tuple[object, ...]:
        return tuple(
            tuple(
                tuple(
                    tuple((producer * 2) + block for _lane in range(8))
                    for _row in range(8)
                )
                for _slice in range(16)
            )
            for block in range(block_count)
        )

    monkeypatch.setattr(
        "npu.eval.probe_attention_score32_exact_local16_global_tree_gqa8._value_blocks",
        fake_value_blocks,
    )
    p54 = _fill_rows_for_wave(cluster=0, wave=0)
    p53 = _fill_rows_for_wave(cluster=8, wave=0)

    assert len(p54) == 2048
    assert len(p53) == 2048
    low_byte = lambda rows, slot: rows[slot * 16] & 0xFF
    assert [low_byte(p54, slot) for slot in (0, 1, 18, 19, 20)] == [0, 1, 18, 19, 20]
    assert [low_byte(p53, slot) for slot in (0, 1, 20, 21, 22)] == [0, 1, 20, 21, 22]


def test_fill_sidecar_uses_cluster_major_wave_command_order(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    fake_wave_commands = tuple(
        {"head_base": head_base, "wave_index": wave_index}
        for head_base in (0, 8)
        for wave_index in range(8)
    )
    monkeypatch.setattr(
        "npu.eval.probe_attention_score32_exact_local16_global_tree_cluster_sram_gqa8._driver_data",
        lambda **_: {
            "wave_commands": fake_wave_commands,
            "query_words": [0],
            "key_words": [0],
            "max_beats_per_producer": 1,
            "beat_limits": [[0]],
        },
    )

    def fake_fill_rows_for_wave(*, cluster: int, wave: int, head_base: int = 0) -> list[int]:
        sentinel = ((head_base & 0x1F) << 16) | ((cluster & 0xFF) << 8) | (wave & 0xFF)
        return [sentinel] * ROWS_PER_BUFFER

    monkeypatch.setattr(
        "npu.eval.probe_attention_score32_exact_local16_global_tree_cluster_sram_gqa8._fill_rows_for_wave",
        fake_fill_rows_for_wave,
    )
    sidecars = _write_memh_sidecars(tmp_path, logical_head_groups=2)
    fill_lines = (tmp_path / sidecars["fill"]).read_text(encoding="ascii").splitlines()

    def line_value(index: int) -> int:
        return int(fill_lines[index], 16)

    assert line_value(0) == 0x000000
    assert line_value(ROWS_PER_BUFFER) == 0x000001
    assert line_value(8 * ROWS_PER_BUFFER) == 0x080000
    assert line_value(16 * ROWS_PER_BUFFER) == 0x000100


def _audit_fixture() -> tuple[
    dict[str, object],
    dict[str, int],
    list[dict[str, int]],
    list[list[dict[str, object]]],
    list[dict[str, object]],
]:
    cluster_rows = [[{"cluster": cluster, "value": [cluster]}] for cluster in range(16)]
    root_rows = [{"command_id": 0x8200, "value": [1] * 16}]
    reference: dict[str, object] = {
        "cluster_rows": copy.deepcopy(cluster_rows),
        "root_rows": copy.deepcopy(root_rows),
        "cluster_hashes": ["expected"] * 16,
        "root_hash": "expected",
    }
    summary = dict(EXPECTED_TOTALS)
    summary.update(
        {
            "command_accept_count": 8,
            "cadence_command_accept_count": 8,
            "protocol_error": 0,
        }
    )
    cluster_summaries = [
        {"cluster": cluster, **EXPECTED_PER_CLUSTER, "errors": 0}
        for cluster in range(16)
    ]
    return reference, summary, cluster_summaries, cluster_rows, root_rows


def _minimal_probe_config() -> dict[str, object]:
    return {
        "top_name": "fake_top",
        "attention_score32_exact_local16_global_tree_cluster_sram_gqa8": {
            "cluster_producers": [54] * 8 + [53] * 8
        },
    }


def test_verilator_control_file_marks_exact_hierarchical_modules() -> None:
    assert _hierarchical_module_names("score32_top") == {
        "p54_cluster": "score32_top__cluster_p54",
        "p53_cluster": "score32_top__cluster_p53",
        "global_tree": "score32_top__global_tree",
    }
    assert _verilator_control_file_text("score32_top") == "\n".join(
        [
            "`verilator_config",
            'hier_block -module "score32_top__cluster_p54"',
            'hier_block -module "score32_top__cluster_p53"',
            'hier_block -module "score32_top__global_tree"',
            "",
        ]
    )


def test_verilator_hierarchical_command_uses_bounded_parallelism_and_control_file(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        "npu.eval.probe_attention_score32_exact_local16_global_tree_cluster_sram_gqa8._tool",
        lambda name: f"/tools/{name}",
    )

    command = _verilator_hierarchical_compile_command(
        rtl_dir=tmp_path / "rtl",
        fakeram_path=tmp_path / "fakeram45_2048x39.v",
        tb_path=tmp_path / "tb.v",
        control_path=tmp_path / "verilator_hier.vlt",
        obj_dir=tmp_path / "obj_dir",
    )

    assert command[:7] == [
        "/tools/verilator",
        "--binary",
        "--timing",
        "--hierarchical",
        "-Wno-fatal",
        "-j",
        str(VERILATOR_BUILD_JOBS),
    ]
    assert "--Mdir" in command
    assert "--top-module" in command
    assert "tb" in command
    assert str(tmp_path / "verilator_hier.vlt") in command
    assert str(tmp_path / "rtl" / "top.v") in command
    assert str(tmp_path / "tb.v") in command


def test_icarus_command_remains_the_default_compilation_path(monkeypatch: Any, tmp_path: Path) -> None:
    monkeypatch.setattr(
        "npu.eval.probe_attention_score32_exact_local16_global_tree_cluster_sram_gqa8._tool",
        lambda name: f"/tools/{name}",
    )

    command = _icarus_compile_command(
        rtl_dir=tmp_path / "rtl",
        fakeram_path=tmp_path / "fakeram45_2048x39.v",
        tb_path=tmp_path / "tb.v",
        sim_path=tmp_path / "sim.out",
    )

    assert command == [
        "/tools/iverilog",
        "-g2012",
        "-s",
        "tb",
        "-o",
        str(tmp_path / "sim.out"),
        str(tmp_path / "rtl" / "top.v"),
        str(tmp_path / "fakeram45_2048x39.v"),
        str(tmp_path / "tb.v"),
    ]


def test_compositional_cluster_testbenches_use_concrete_rtl_and_local_sidecars() -> None:
    p54 = cluster_testbench(top_name="score32_top__cluster_p54", producers=54, logical_head_groups=1)
    p53 = cluster_testbench(top_name="score32_top__cluster_p53", producers=53, logical_head_groups=4)

    assert COMPOSITIONAL_RUNNER_BACKEND == COMPOSITIONAL_ICARUS_BACKEND
    assert "score32_top__cluster_p54 dut (" in p54
    assert "localparam integer PRODUCERS = 54;" in p54
    assert ".sram_fill_row_accept_count(fill_rows)" in p54
    assert ".sram_release_guard_error(release_guard_error)" in p54
    assert ".out_valid(out_valid), .out_ready(out_ready)" in p54
    assert "if (out_valid && out_ready)" in p54
    assert "$readmemh(\"query.memh\", query_mem)" in p54
    assert "$readmemh(\"fill.memh\", fill_mem)" in p54
    assert "input_query = '0" in p54
    assert "score32_top__cluster_p53 dut (" in p53
    assert "localparam integer PRODUCERS = 53;" in p53
    assert "localparam integer COMMANDS = 32;" in p53


def test_compositional_source_split_keeps_only_exact_generated_module_family() -> None:
    rtl = "\n".join(
        [
            "module score__p54__leaf;\nendmodule",
            "module score__p54;\n  score__p54__leaf u();\nendmodule",
            "module score__p53;\nendmodule",
        ]
    )

    family = extract_module_family(rtl, prefix="score__p54")

    assert "module score__p54__leaf" in family
    assert "module score__p54;" in family
    assert "score__p53" not in family


def test_compositional_source_split_selects_checked_concrete_rtl_families() -> None:
    config = json.loads((_design_dir() / "config.json").read_text(encoding="utf-8"))
    top_name = str(config["top_name"])
    rtl = (_rtl_dir() / "top.v").read_text(encoding="utf-8")

    p54 = extract_module_family(rtl, prefix=f"{top_name}__cluster_p54")
    p53 = extract_module_family(rtl, prefix=f"{top_name}__cluster_p53")
    global_tree = extract_module_family(rtl, prefix=f"{top_name}__global_tree")

    assert f"module {top_name}__cluster_p54 (" in p54
    assert f"module {top_name}__cluster_p53 (" not in p54
    assert f"module {top_name}__cluster_p53 (" in p53
    assert f"module {top_name}__cluster_p54 (" not in p53
    assert f"module {top_name}__global_tree (" in global_tree
    assert f"module {top_name}__global_tree__root_finalizer (" in global_tree


def test_compositional_global_testbench_drives_exact_structured_cluster_rows() -> None:
    tb = global_testbench(
        top_name="score32_top__global_tree",
        rows_per_cluster=128,
        output_ready_pattern=(True, False),
        timeout_cycles=50_000,
    )

    assert "score32_top__global_tree dut (" in tb
    assert "reg [418:0] row_mem" in tb
    assert ".leaf_global_max(leaf_global_max)" in tb
    assert ".tree_protocol_error(tree_error)" in tb
    assert "$readmemh(\"global_rows.memh\",row_mem)" in tb
    assert "ROOT_RESULT" in tb
    assert "GLOBAL_SUMMARY" in tb

    numerators = [
        (1 << 35) + 5,
        -((1 << 34) + 7),
        (1 << 40) - 1,
        -(1 << 40),
        (1 << 32) + 0xABCDEF,
        -((1 << 33) + 0x12345),
        17,
        -19,
    ]
    row = {
        "command_id": 0x8200,
        "head_id": 7,
        "global_max": -3,
        "exp_sum": 123,
        "slice": 9,
        "last": True,
        "value": numerators,
    }
    packed = _pack_global_row(row)
    assert packed & 0xFFFF == 0x8200
    assert (packed >> 16) & 0x1F == 7
    assert (packed >> 21) & 0xFFFF_FFFF == 0xFFFF_FFFD
    assert (packed >> 53) & ((1 << 33) - 1) == 123
    assert (packed >> 86) & 0xF == 9
    assert (packed >> 90) & 1 == 1
    decoded = []
    for lane in range(8):
        raw = (packed >> (91 + lane * 41)) & ((1 << 41) - 1)
        decoded.append(raw - (1 << 41) if raw & (1 << 40) else raw)
    assert decoded == numerators
    assert packed.bit_length() <= 419


def test_concrete_global_tree_matches_canonical_sidecar_rows() -> None:
    if shutil.which("iverilog") is None or shutil.which("vvp") is None:
        pytest.skip("Icarus tools are unavailable")

    streams: list[list[ExactPartialBeat]] = []
    cluster_rows: list[list[dict[str, object]]] = []
    for cluster in range(16):
        beats = []
        rows = []
        for head in range(8):
            for value_slice in range(16):
                numerators = tuple(
                    (
                        (1 << 33)
                        + cluster * 10_000
                        + head * 1_000
                        + value_slice * 10
                        + lane
                    )
                    * (-1 if (cluster + lane) % 2 else 1)
                    for lane in range(8)
                )
                beat = ExactPartialBeat(
                    command_id=0x8200,
                    head_id=head,
                    slice_index=value_slice,
                    last=value_slice == 15,
                    max_score=cluster - 8,
                    exp_sum=1_000 + cluster,
                    numerators=numerators,
                )
                beats.append(beat)
                rows.append(
                    {
                        "cluster": cluster,
                        "command_id": beat.command_id,
                        "head_id": beat.head_id,
                        "slice": beat.slice_index,
                        "last": beat.last,
                        "global_max": beat.max_score,
                        "exp_sum": beat.exp_sum,
                        "value": list(beat.numerators),
                    }
                )
        streams.append(beats)
        cluster_rows.append(rows)
    expected = [
        {
            "command_id": beat.command_id,
            "head_id": beat.head_id,
            "slice": beat.slice_index,
            "last": beat.last,
            "value": list(beat.values),
        }
        for beat in finalize_partial_beats(merge_balanced_partial_streams(streams))
    ]

    config = json.loads((_design_dir() / "config.json").read_text(encoding="utf-8"))
    top_name = f"{config['top_name']}__global_tree"
    generated_rtl = (_rtl_dir() / "top.v").read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory(prefix="gqa8_global_sidecar_test_") as temp_name:
        work_dir = Path(temp_name)
        rtl_dir = work_dir / "rtl"
        rtl_dir.mkdir()
        (rtl_dir / "top.v").write_text(
            extract_module_family(generated_rtl, prefix=top_name),
            encoding="utf-8",
        )
        sidecar = _write_global_sidecar(work_dir, cluster_rows)
        assert sidecar["row_bits"] == 419
        assert sidecar["value_offset"] == 91
        assert sidecar["numerator_lanes"] == 8
        assert sidecar["numerator_bits"] == 41
        assert sidecar["value_packing"] == "canonical_pack_numerators"
        tb_path = work_dir / "tb.v"
        tb_path.write_text(
            global_testbench(
                top_name=top_name,
                rows_per_cluster=int(sidecar["rows_per_cluster"]),
                output_ready_pattern=(True, True, False, True),
                timeout_cycles=TB_TIMEOUT_CYCLES,
            ),
            encoding="ascii",
        )
        fakeram_path = work_dir / "fakeram45_2048x39.v"
        fakeram_path.write_text(full_probe._FAKERAM_MODEL, encoding="ascii")
        sim_path = work_dir / "sim.out"
        compile_result = subprocess.run(
            _icarus_compile_command(
                rtl_dir=rtl_dir,
                fakeram_path=fakeram_path,
                tb_path=tb_path,
                sim_path=sim_path,
            ),
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert compile_result.returncode == 0, compile_result.stderr
        run_result = subprocess.run(
            [shutil.which("vvp") or "vvp", str(sim_path)],
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert run_result.returncode == 0, run_result.stderr

    _, _, _, observed, timeout_cycle = _parse_stdout(run_result.stdout)
    audit = compare_full_rows(expected, observed)
    assert timeout_cycle is None
    assert audit["passed"] is True, audit


def test_fine_compositional_boundary_names_are_exact() -> None:
    names = component_module_names("score32_top")

    assert FINE_COMPOSITIONAL_RUNNER_BACKEND == FINE_COMPOSITIONAL_ICARUS_BACKEND
    assert names == {
        "p54_producer": "score32_top__cluster_p54__compute_cluster__producer",
        "p53_producer": "score32_top__cluster_p53__compute_cluster__producer",
        "p54_reducer": "score32_top__cluster_p54__compute_cluster__reducer",
        "p53_reducer": "score32_top__cluster_p53__compute_cluster__reducer",
        "p54_sram": "score32_top__cluster_p54__sram_endpoint",
        "p53_sram": "score32_top__cluster_p53__sram_endpoint",
        "global_tree": "score32_top__global_tree",
    }


def test_fine_compositional_producer_harness_uses_one_real_producer_and_sidecars() -> None:
    case = {
        "commands": [{"command_id": 1}],
        "query_words": [0],
        "expected_rows": [{"command_id": 1}],
        "total_blocks": 1,
    }

    tb = producer_testbench(
        top_name="score32_top__cluster_p54__compute_cluster__producer",
        case=case,
        cluster=2,
        producer=7,
    )

    assert "score32_top__cluster_p54__compute_cluster__producer dut (" in tb
    assert "u_producer_" not in tb
    assert "__cluster_p54 dut" not in tb
    assert '$readmemh("producer_commands.memh",command_mem);' in tb
    assert '$readmemh("value.memh",value_mem);' in tb
    assert "PRODUCER_REQUEST" in tb
    assert "PRODUCER_RESULT cluster=2 producer=7" in tb


def test_fine_compositional_sram_harness_uses_real_endpoint_and_observed_requests() -> None:
    sidecar = {
        "commands": [{"command_id": 0x8200, "head_base": 0, "wave_index": 0}],
        "counts": [[1, 0]],
        "max_requests": 1,
        "request_count": 1,
    }

    tb = sram_testbench(
        top_name="score32_top__cluster_p54__sram_endpoint",
        producers=1,
        sidecar=sidecar,
    )

    assert "score32_top__cluster_p54__sram_endpoint dut (" in tb
    assert "__compute_cluster" not in tb
    assert '$readmemh("sram_requests.memh",req_mem);' in tb
    assert '$readmemh("sram_fill.memh",fill_mem);' in tb
    assert "SRAM_RESPONSE" in tb
    assert "SRAM_SUMMARY" in tb


def test_fine_compositional_request_metadata_requires_every_block_and_slice() -> None:
    requests = [
        [{"command": 0, "address": block, "slice": value_slice} for block in range(2) for value_slice in range(16)],
        [{"command": 0, "address": block, "slice": value_slice} for block in range(2) for value_slice in range(16)],
    ]

    assert _check_request_metadata(requests, [2]) == {"passed": True}
    requests[0].pop()
    rejected = _check_request_metadata(requests, [2])
    assert rejected["passed"] is False
    assert rejected["stream"] == 0
    assert rejected["command"] == 0


def test_fine_compositional_producer_parser_decodes_hexadecimal_value() -> None:
    numerators = [10, 11, 12, 13, 14, 15, 26, -1]
    packed = pack_numerators(numerators)
    stdout = (
        "PRODUCER_RESULT cluster=2 producer=7 cmd=33280 head=3 slice=9 "
        f"last=0 max=-11 sum=991 value={packed:082x}\n"
    )
    assert any(character in f"{packed:082x}" for character in "abcdef")

    rows, requests, summary = _parse_producer(stdout)

    assert rows == [
        {
            "command_id": 33280,
            "head_id": 3,
            "slice": 9,
            "last": False,
            "global_max": -11,
            "exp_sum": 991,
            "value": numerators,
        }
    ]
    assert requests == [[], []]
    assert summary is None


def test_fine_compositional_reducer_parser_decodes_hexadecimal_value() -> None:
    numerators = [15, 14, 13, 12, 11, 10, 31, -2]
    packed = pack_numerators(numerators)
    stdout = (
        "RESULT idx=0 cmd=33280 head=3 slice=9 last=1 max=-8 sum=1012 "
        f"value={packed:082x} cycle=77\n"
    )

    rows, summary = _parse_reducer(stdout, cluster=4)

    assert rows == [
        {
            "cluster": 4,
            "command_id": 33280,
            "head_id": 3,
            "slice": 9,
            "last": True,
            "global_max": -8,
            "exp_sum": 1012,
            "value": numerators,
        }
    ]
    assert summary is None


def test_composed_stdout_parser_decodes_hexadecimal_cluster_and_root_values() -> None:
    cluster_values = [10, 11, 12, 13, 14, 15, 26, -1]
    root_values = [15, 14, 13, 12, 11, 10, 31, -2]
    stdout = "\n".join(
        [
            (
                "CLUSTER_RESULT cluster=2 cmd=33280 head=3 slice=9 last=0 max=-11 sum=991 "
                f"value={pack_numerators(cluster_values):082x} cycle=44"
            ),
            (
                "ROOT_RESULT cmd=33280 head=3 slice=9 last=1 "
                f"value={pack_final_values(root_values):016x} cycle=77"
            ),
        ]
    )

    summary, cluster_summaries, cluster_rows, root_rows, timeout_cycle = _parse_stdout(stdout)

    assert summary == {}
    assert cluster_summaries == []
    assert cluster_rows[2][0]["value"] == cluster_values
    assert root_rows[0]["value"] == root_values
    assert timeout_cycle is None


def test_fine_compositional_sram_audit_checks_metadata_data_and_tag() -> None:
    command = 0
    lane = 0
    address = 0
    value_slice = 0
    fill_rows = _fill_rows_for_wave(cluster=0, head_base=0, wave=0)
    response = {
        "command": command,
        "lane": lane,
        "address": address,
        "slice": value_slice,
        "data": fill_rows[0],
        "tag": 0,
    }
    expected = [{key: response[key] for key in ("command", "lane", "address", "slice")}]

    assert _check_sram_responses(
        cluster=0,
        logical_head_groups=1,
        responses=[response],
        expected_responses=expected,
    ) == {"passed": True}

    wrong_data = dict(response)
    wrong_data["data"] = int(response["data"]) ^ 1
    rejected = _check_sram_responses(
        cluster=0,
        logical_head_groups=1,
        responses=[wrong_data],
        expected_responses=expected,
    )
    assert rejected["passed"] is False
    assert rejected["response"] == 0


def test_compositional_subprocess_resource_kill_stays_inconclusive(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        "npu.eval.gqa8_compositional_exact.subprocess.run",
        lambda *_args, **_kwargs: __import__("subprocess").CompletedProcess(
            args=["iverilog"],
            returncode=137,
            stdout="",
            stderr="Killed\n",
        ),
    )

    _, failure = _run_process(
        ["iverilog"],
        cwd=tmp_path,
        timeout_sec=1,
        phase="compile_p54_cluster",
    )

    assert failure is not None
    assert failure["status"] == "resource_failure"
    assert failure["returncode"] == 137


def test_compositional_subprocess_syntax_error_stays_conclusive(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        "npu.eval.gqa8_compositional_exact.subprocess.run",
        lambda *_args, **_kwargs: __import__("subprocess").CompletedProcess(
            args=["iverilog"],
            returncode=2,
            stdout="",
            stderr="tb.v:12: syntax error\n",
        ),
    )

    _, failure = _run_process(
        ["iverilog"],
        cwd=tmp_path,
        timeout_sec=1,
        phase="compile_global_tree",
    )

    assert failure is not None
    assert failure["status"] == "compile_failed"
    assert failure["returncode"] == 2


def test_compositional_subprocess_bad_alloc_stays_inconclusive(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        "npu.eval.gqa8_compositional_exact.subprocess.run",
        lambda *_args, **_kwargs: __import__("subprocess").CompletedProcess(
            args=["iverilog"],
            returncode=255,
            stdout="",
            stderr="terminate called after throwing an instance of 'std::bad_alloc'\n",
        ),
    )

    _, failure = _run_process(
        ["iverilog"],
        cwd=tmp_path,
        timeout_sec=1,
        phase="compile_p54_component",
    )

    assert failure is not None
    assert failure["status"] == "resource_failure"
    assert failure["returncode"] == 255


def test_observation_evaluator_validates_every_exact_total_and_row() -> None:
    reference, summary, cluster_summaries, cluster_rows, root_rows = _audit_fixture()
    result = _evaluate_observations(
        reference=reference,
        summary=summary,
        cluster_summaries=cluster_summaries,
        observed_cluster_rows=cluster_rows,
        observed_root_rows=root_rows,
    )
    assert result["passed"] is True
    assert result["classification"] == "passed"
    assert result["counts_passed"] is True
    assert "observed_cluster_rows" not in result
    assert "expected_cluster_rows" not in result
    assert "observed_root_rows" not in result
    assert "expected_root_rows" not in result
    assert expected_counts()["totals"] == {
        "fill_target_accept_count": 128,
        "fill_row_accept_count": 262144,
        "producer_handshake_count": 8192,
        "sram_request_accept_count": 262144,
        "sram_response_accept_count": 262144,
        "cluster_row_count": 2048,
        "root_row_count": 128,
    }
    assert expected_counts()["per_cluster"][0] == {
        "wave_command_accept_count": 8,
        "completed_command_count": 1,
        "emitted_beat_count": 128,
        "fill_target_accept_count": 8,
        "fill_row_accept_count": 16384,
        "request_accept_count": 16384,
        "response_accept_count": 16384,
        "command_accept_count": 8,
        "command_release_count": 8,
    }


def test_observation_evaluator_rejects_incomplete_and_mismatched_rows_conclusively() -> None:
    reference, summary, cluster_summaries, cluster_rows, root_rows = _audit_fixture()
    incomplete = copy.deepcopy(cluster_rows)
    incomplete[4] = []
    incomplete_result = _evaluate_observations(
        reference=reference,
        summary=summary,
        cluster_summaries=cluster_summaries,
        observed_cluster_rows=incomplete,
        observed_root_rows=root_rows,
    )
    assert incomplete_result["passed"] is False
    assert incomplete_result["classification"] == "failed_conclusive"
    assert incomplete_result["full_row_audit"]["clusters"][4]["first_mismatch"]["field"] == "__row_count__"

    mismatched_root = copy.deepcopy(root_rows)
    mismatched_root[0]["value"][7] = 2
    mismatch_result = _evaluate_observations(
        reference=reference,
        summary=summary,
        cluster_summaries=cluster_summaries,
        observed_cluster_rows=cluster_rows,
        observed_root_rows=mismatched_root,
    )
    assert mismatch_result["passed"] is False
    assert mismatch_result["classification"] == "failed_conclusive"
    assert mismatch_result["full_row_audit"]["root"]["first_mismatch"]["field"] == "value"

    protocol_summary = dict(summary)
    protocol_summary["protocol_error"] = 1
    protocol_result = _evaluate_observations(
        reference=reference,
        summary=protocol_summary,
        cluster_summaries=cluster_summaries,
        observed_cluster_rows=cluster_rows,
        observed_root_rows=root_rows,
    )
    assert protocol_result["passed"] is False
    assert protocol_result["classification"] == "failed_conclusive"


def test_failure_classification_marks_timeouts_oom_and_kills_inconclusive() -> None:
    assert DEFAULT_ROOT_READY_PATTERN == (True, True, False, True)
    assert TB_TIMEOUT_CYCLES == 50000
    assert DEFAULT_SUBPROCESS_TIMEOUT_SEC == 900
    for returncode in (124, 125, 137, -9):
        assert _failure_classification(
            simulation_status="run_failed",
            returncode=returncode,
            stderr="",
            tb_timeout_cycle=None,
            passed=False,
        ) == "failed_inconclusive"
    assert _failure_classification(
        simulation_status="resource_failure",
        returncode=1,
        stderr="out of memory",
        tb_timeout_cycle=None,
        passed=False,
    ) == "failed_inconclusive"
    assert _failure_classification(
        simulation_status="ok",
        returncode=0,
        stderr="",
        tb_timeout_cycle=50000,
        passed=False,
    ) == "failed_inconclusive"
    for simulation_status in ("compile_failed", "run_failed"):
        assert _failure_classification(
            simulation_status=simulation_status,
            returncode=1,
            stderr="top.v:10: syntax error",
            tb_timeout_cycle=None,
            passed=False,
        ) == "failed_conclusive"


def test_build_report_classifies_compile_sigkill_resource_failures_inconclusive(
    monkeypatch: Any,
) -> None:
    reference, summary, cluster_summaries, cluster_rows, root_rows = _audit_fixture()

    monkeypatch.setattr(
        "npu.eval.probe_attention_score32_exact_local16_global_tree_cluster_sram_gqa8.generate",
        lambda _config, rtl_dir: (rtl_dir.mkdir(parents=True, exist_ok=True), (rtl_dir / "top.v").write_text("module top; endmodule\n", encoding="ascii")),
    )
    monkeypatch.setattr(
        "npu.eval.probe_attention_score32_exact_local16_global_tree_cluster_sram_gqa8._write_memh_sidecars",
        lambda *_args, **_kwargs: {},
    )
    monkeypatch.setattr(
        "npu.eval.probe_attention_score32_exact_local16_global_tree_cluster_sram_gqa8._reference",
        lambda **_kwargs: reference,
    )
    monkeypatch.setattr(
        "npu.eval.probe_attention_score32_exact_local16_global_tree_cluster_sram_gqa8._parse_stdout",
        lambda _stdout: (summary, cluster_summaries, cluster_rows, root_rows, None),
    )
    monkeypatch.setattr(
        "npu.eval.probe_attention_score32_exact_local16_global_tree_cluster_sram_gqa8._tool",
        lambda _name: "/bin/true",
    )

    for returncode, stdout, stderr in (
        (137, "", "Killed\n"),
        (-9, "Killed\n", ""),
    ):
        monkeypatch.setattr(
            "npu.eval.probe_attention_score32_exact_local16_global_tree_cluster_sram_gqa8.subprocess.run",
            lambda *_args, **_kwargs: __import__("subprocess").CompletedProcess(
                args=["iverilog"],
                returncode=returncode,
                stdout=stdout,
                stderr=stderr,
            ),
        )
        report = build_report(config=_minimal_probe_config(), timeout_sec=1)
        assert report["passed"] is False
        assert report["simulation_status"] == "resource_failure"
        assert report["classification"] == "failed_inconclusive"
        assert report["returncode"] == returncode
        assert report["normalized_returncode"] == 137
        assert "Killed" in report["stderr_tail"]


def test_build_report_keeps_compile_syntax_errors_conclusive_and_bounded(
    monkeypatch: Any,
) -> None:
    reference, summary, cluster_summaries, cluster_rows, root_rows = _audit_fixture()
    long_stderr = ("noise\n" * 2000) + "top.v:10: syntax error\n"

    monkeypatch.setattr(
        "npu.eval.probe_attention_score32_exact_local16_global_tree_cluster_sram_gqa8.generate",
        lambda _config, rtl_dir: (rtl_dir.mkdir(parents=True, exist_ok=True), (rtl_dir / "top.v").write_text("module top; endmodule\n", encoding="ascii")),
    )
    monkeypatch.setattr(
        "npu.eval.probe_attention_score32_exact_local16_global_tree_cluster_sram_gqa8._write_memh_sidecars",
        lambda *_args, **_kwargs: {},
    )
    monkeypatch.setattr(
        "npu.eval.probe_attention_score32_exact_local16_global_tree_cluster_sram_gqa8._reference",
        lambda **_kwargs: reference,
    )
    monkeypatch.setattr(
        "npu.eval.probe_attention_score32_exact_local16_global_tree_cluster_sram_gqa8._parse_stdout",
        lambda _stdout: (summary, cluster_summaries, cluster_rows, root_rows, None),
    )
    monkeypatch.setattr(
        "npu.eval.probe_attention_score32_exact_local16_global_tree_cluster_sram_gqa8._tool",
        lambda _name: "/bin/true",
    )
    monkeypatch.setattr(
        "npu.eval.probe_attention_score32_exact_local16_global_tree_cluster_sram_gqa8.subprocess.run",
        lambda *_args, **_kwargs: __import__("subprocess").CompletedProcess(
            args=["iverilog"],
            returncode=2,
            stdout="",
            stderr=long_stderr,
        ),
    )

    report = build_report(config=_minimal_probe_config(), timeout_sec=1)

    assert report["passed"] is False
    assert report["simulation_status"] == "compile_failed"
    assert report["classification"] == "failed_conclusive"
    assert report["returncode"] == 2
    assert report["normalized_returncode"] == 2
    assert len(report["stderr_tail"]) <= DIAGNOSTIC_TAIL_LIMIT + 64
    assert "top.v:10: syntax error" in report["stderr_tail"]


def test_markdown_failure_report_keeps_bounded_subprocess_diagnostics() -> None:
    stderr_tail = "first meaningful error\n" + ("warning\n" * 400) + "Killed\n"
    report = {
        "passed": False,
        "classification": "failed_inconclusive",
        "simulation_status": "resource_failure",
        "sim_backend": VERILATOR_HIERARCHICAL_BACKEND,
        "compile_timeout_sec": 1200,
        "simulation_timeout_sec": 900,
        "returncode": -9,
        "normalized_returncode": 137,
        "stderr_tail": stderr_tail,
        "summary": {},
        "observed_root_hash": "",
        "expected_root_hash": "",
    }

    rendered = _render_text(report)

    assert "- returncode: `-9`" in rendered
    assert "- normalized_returncode: `137`" in rendered
    assert "- stderr_tail:" in rendered
    assert "first meaningful error" in rendered
    assert "...[middle omitted]..." in rendered
    assert "Killed" in rendered
    assert stderr_tail not in rendered
    diagnostic = rendered.split("```text\n", 1)[1].rsplit("\n```", 1)[0]
    assert len(diagnostic) <= MARKDOWN_DIAGNOSTIC_TAIL_LIMIT + 64


def test_markdown_pass_report_omits_failure_diagnostics() -> None:
    report = {
        "passed": True,
        "classification": "passed",
        "simulation_status": "ok",
        "sim_backend": DEFAULT_SIM_BACKEND,
        "compile_timeout_sec": 900,
        "simulation_timeout_sec": 900,
        "returncode": 0,
        "normalized_returncode": 0,
        "stderr_tail": "",
        "summary": {},
        "observed_root_hash": "expected",
        "expected_root_hash": "expected",
    }

    rendered = _render_text(report)

    assert "returncode" not in rendered
    assert "stderr_tail" not in rendered


def test_build_report_records_verilator_backend_metadata_and_command(
    monkeypatch: Any,
) -> None:
    reference, summary, cluster_summaries, cluster_rows, root_rows = _audit_fixture()
    calls: list[list[str]] = []

    monkeypatch.setattr(
        "npu.eval.probe_attention_score32_exact_local16_global_tree_cluster_sram_gqa8.generate",
        lambda _config, rtl_dir: (
            rtl_dir.mkdir(parents=True, exist_ok=True),
            (rtl_dir / "top.v").write_text("module top; endmodule\n", encoding="ascii"),
        ),
    )
    monkeypatch.setattr(
        "npu.eval.probe_attention_score32_exact_local16_global_tree_cluster_sram_gqa8._write_memh_sidecars",
        lambda *_args, **_kwargs: {},
    )
    monkeypatch.setattr(
        "npu.eval.probe_attention_score32_exact_local16_global_tree_cluster_sram_gqa8._reference",
        lambda **_kwargs: reference,
    )
    monkeypatch.setattr(
        "npu.eval.probe_attention_score32_exact_local16_global_tree_cluster_sram_gqa8._parse_stdout",
        lambda _stdout: (summary, cluster_summaries, cluster_rows, root_rows, None),
    )
    monkeypatch.setattr(
        "npu.eval.probe_attention_score32_exact_local16_global_tree_cluster_sram_gqa8._tool",
        lambda name: f"/tools/{name}",
    )

    def fake_run(command: list[str], **_kwargs: object) -> Any:
        calls.append(list(command))
        if len(calls) == 1:
            return __import__("subprocess").CompletedProcess(args=command, returncode=0, stdout="", stderr="")
        return __import__("subprocess").CompletedProcess(args=command, returncode=0, stdout="", stderr="")

    monkeypatch.setattr(
        "npu.eval.probe_attention_score32_exact_local16_global_tree_cluster_sram_gqa8.subprocess.run",
        fake_run,
    )

    report = build_report(
        config=_minimal_probe_config(),
        timeout_sec=1,
        sim_backend=VERILATOR_HIERARCHICAL_BACKEND,
    )

    assert report["passed"] is True
    assert report["sim_backend"] == VERILATOR_HIERARCHICAL_BACKEND
    assert report["compile_timeout_sec"] == DEFAULT_VERILATOR_COMPILE_TIMEOUT_SEC
    assert report["simulation_timeout_sec"] == 1
    assert report["sim_backend_metadata"] == {
        "compile_tool": "verilator",
        "run_tool": "verilated_binary",
        "compile_timeout_sec": DEFAULT_VERILATOR_COMPILE_TIMEOUT_SEC,
        "simulation_timeout_sec": 1,
        "top_module": "tb",
        "build_jobs": VERILATOR_BUILD_JOBS,
        "control_file": "verilator_hier.vlt",
        "hierarchical_modules": {
            "p54_cluster": "fake_top__cluster_p54",
            "p53_cluster": "fake_top__cluster_p53",
            "global_tree": "fake_top__global_tree",
        },
    }
    assert len(calls) == 2
    assert calls[0][:4] == ["/tools/verilator", "--binary", "--timing", "--hierarchical"]
    assert "verilator_hier.vlt" in " ".join(calls[0])
    assert calls[1] == [str(Path(calls[0][calls[0].index("--Mdir") + 1]) / "simv")]


def test_build_report_defaults_to_icarus_backend(
    monkeypatch: Any,
) -> None:
    reference, summary, cluster_summaries, cluster_rows, root_rows = _audit_fixture()
    calls: list[list[str]] = []

    monkeypatch.setattr(
        "npu.eval.probe_attention_score32_exact_local16_global_tree_cluster_sram_gqa8.generate",
        lambda _config, rtl_dir: (
            rtl_dir.mkdir(parents=True, exist_ok=True),
            (rtl_dir / "top.v").write_text("module top; endmodule\n", encoding="ascii"),
        ),
    )
    monkeypatch.setattr(
        "npu.eval.probe_attention_score32_exact_local16_global_tree_cluster_sram_gqa8._write_memh_sidecars",
        lambda *_args, **_kwargs: {},
    )
    monkeypatch.setattr(
        "npu.eval.probe_attention_score32_exact_local16_global_tree_cluster_sram_gqa8._reference",
        lambda **_kwargs: reference,
    )
    monkeypatch.setattr(
        "npu.eval.probe_attention_score32_exact_local16_global_tree_cluster_sram_gqa8._parse_stdout",
        lambda _stdout: (summary, cluster_summaries, cluster_rows, root_rows, None),
    )
    monkeypatch.setattr(
        "npu.eval.probe_attention_score32_exact_local16_global_tree_cluster_sram_gqa8._tool",
        lambda name: f"/tools/{name}",
    )
    monkeypatch.setattr(
        "npu.eval.probe_attention_score32_exact_local16_global_tree_cluster_sram_gqa8.subprocess.run",
        lambda command, **_kwargs: (
            calls.append(list(command))
            or __import__("subprocess").CompletedProcess(args=command, returncode=0, stdout="", stderr="")
        ),
    )

    report = build_report(config=_minimal_probe_config(), timeout_sec=1)

    assert DEFAULT_SIM_BACKEND in SIM_BACKEND_CHOICES
    assert report["sim_backend"] == DEFAULT_SIM_BACKEND
    assert report["compile_timeout_sec"] == 1
    assert report["simulation_timeout_sec"] == 1
    assert report["sim_backend_metadata"] == {
        "compile_tool": "iverilog",
        "run_tool": "vvp",
        "compile_timeout_sec": 1,
        "simulation_timeout_sec": 1,
    }
    assert calls[0][0] == "/tools/iverilog"
    assert calls[1] == ["/tools/vvp", calls[0][5]]


def test_build_report_selects_concrete_compositional_backend(monkeypatch: Any) -> None:
    reference, summary, cluster_summaries, cluster_rows, root_rows = _audit_fixture()
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        "npu.eval.probe_attention_score32_exact_local16_global_tree_cluster_sram_gqa8.generate",
        lambda config, rtl_dir: (
            rtl_dir.mkdir(parents=True, exist_ok=True),
            (rtl_dir / "config.json").write_text(json.dumps(config), encoding="utf-8"),
        ),
    )
    monkeypatch.setattr(
        "npu.eval.probe_attention_score32_exact_local16_global_tree_cluster_sram_gqa8._reference",
        lambda **_kwargs: reference,
    )
    monkeypatch.setattr(
        "npu.eval.probe_attention_score32_exact_local16_global_tree_cluster_sram_gqa8._parse_stdout",
        lambda _stdout: (summary, cluster_summaries, cluster_rows, root_rows, None),
    )

    def fake_compositional(**kwargs: object) -> dict[str, object]:
        captured.update(kwargs)
        return {
            "simulation_status": "ok",
            "returncode": 0,
            "stdout": "component observations",
            "stderr": "",
            "phase_records": [{"phase": "strict_generated_top_guard", "returncode": 0}],
            "component_metadata": {
                "proof": "concrete_rtl_composition",
                "strict_generated_top_guard": "passed",
            },
        }

    monkeypatch.setattr(
        "npu.eval.gqa8_compositional_exact.run_compositional_exact",
        fake_compositional,
    )

    report = build_report(
        config=_minimal_probe_config(),
        timeout_sec=9,
        compile_timeout_sec=17,
        sim_backend=COMPOSITIONAL_ICARUS_BACKEND,
    )

    assert report["passed"] is True
    assert report["sim_backend"] == COMPOSITIONAL_ICARUS_BACKEND
    assert report["compile_timeout_sec"] == 17
    assert report["simulation_timeout_sec"] == 9
    assert report["sim_backend_metadata"]["proof"] == "concrete_rtl_composition"
    assert report["compositional_components"]["strict_generated_top_guard"] == "passed"
    assert captured["compile_timeout_sec"] == 17
    assert captured["simulation_timeout_sec"] == 9
    assert captured["logical_head_groups"] == 1


def test_build_report_selects_fine_compositional_backend(monkeypatch: Any) -> None:
    reference, summary, cluster_summaries, cluster_rows, root_rows = _audit_fixture()
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        "npu.eval.probe_attention_score32_exact_local16_global_tree_cluster_sram_gqa8.generate",
        lambda config, rtl_dir: (
            rtl_dir.mkdir(parents=True, exist_ok=True),
            (rtl_dir / "config.json").write_text(json.dumps(config), encoding="utf-8"),
        ),
    )
    monkeypatch.setattr(
        "npu.eval.probe_attention_score32_exact_local16_global_tree_cluster_sram_gqa8._reference",
        lambda **_kwargs: reference,
    )
    monkeypatch.setattr(
        "npu.eval.probe_attention_score32_exact_local16_global_tree_cluster_sram_gqa8._parse_stdout",
        lambda _stdout: (summary, cluster_summaries, cluster_rows, root_rows, None),
    )

    def fake_fine(**kwargs: object) -> dict[str, object]:
        captured.update(kwargs)
        return {
            "simulation_status": "ok",
            "returncode": 0,
            "stdout": "fine component observations",
            "stderr": "",
            "phase_records": [{"phase": "strict_generated_top_guard", "returncode": 0}],
            "component_metadata": {
                "proof": "fine_grained_concrete_rtl_composition",
                "strict_generated_top_guard": "passed",
                "producer_replay_parallelism": 1,
            },
        }

    monkeypatch.setattr(
        "npu.eval.gqa8_fine_compositional_exact.run_fine_compositional_exact",
        fake_fine,
    )

    report = build_report(
        config=_minimal_probe_config(),
        timeout_sec=11,
        compile_timeout_sec=19,
        sim_backend=FINE_COMPOSITIONAL_ICARUS_BACKEND,
    )

    assert report["passed"] is True
    assert report["sim_backend"] == FINE_COMPOSITIONAL_ICARUS_BACKEND
    assert report["compile_timeout_sec"] == 19
    assert report["simulation_timeout_sec"] == 11
    assert report["sim_backend_metadata"]["proof"] == "fine_grained_concrete_rtl_composition"
    assert report["sim_backend_metadata"]["producer_replay_parallelism"] == 1
    assert report["compositional_components"]["strict_generated_top_guard"] == "passed"
    assert report["compositional_components"]["producer_replay_parallelism"] == 1
    assert captured["compile_timeout_sec"] == 19
    assert captured["simulation_timeout_sec"] == 11
    assert captured["logical_head_groups"] == 1


def test_checked_in_config_rejects_partition_drift() -> None:
    config = json.loads((_design_dir() / "config.json").read_text(encoding="utf-8"))
    _validate(config)
    body = config["attention_score32_exact_local16_global_tree_cluster_sram_gqa8"]
    body["cluster_producers"] = [54] * 7 + [53] * 9
    try:
        _validate(config)
    except SystemExit as exc:
        assert "exactly eight 54s followed by eight 53s" in str(exc)
    else:
        raise AssertionError("expected partition drift to be rejected")


def test_checked_in_top_removes_external_value_lanes_and_enforces_fill_window() -> None:
    manifest = json.loads(
        (_rtl_dir() / "attention_score32_exact_local16_global_tree_cluster_sram_gqa8_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    rtl = (_rtl_dir() / "top.v").read_text(encoding="utf-8")

    assert manifest["semantic_profile"] == "score32_exact_local16_global_tree_cluster_sram_gqa8_full_compute_v1"
    assert manifest["internal_value_memory_lanes"] == 1712
    assert manifest["external_fill_interfaces"] == 16
    assert manifest["service_model"]["per_cluster_internal_value_memory_lanes"] == [108] * 8 + [106] * 8
    assert "output wire [1711:0] value_read_req_valid" not in rtl
    assert "input  wire [876543:0] value_response_matrix" not in rtl
    assert "input  wire [15:0] fill_target_valid" in rtl
    assert "output wire [15:0] cluster_fill_schedule_contract_error" in rtl
    assert "output wire fill_schedule_contract_error" in rtl
    assert "assign fill_target_schedule_allowed_w[gfill] =" in rtl
    assert "fill_target_head_base[(gfill * 5) +: 5] == expected_head_base_w" in rtl
    assert "fill_target_head_base[(gfill * 5) +: 5] == next_expected_head_base_w" in rtl
    assert ".fill_target_valid(fill_target_valid[0] && fill_target_schedule_allowed_w[0])" in rtl
    assert "fill_target_valid[0] && (!fill_target_metadata_valid_w[0] || !fill_target_schedule_allowed_w[0])" in rtl


def test_main_writes_bounded_json_and_markdown_reports(
    tmp_path: Path,
    monkeypatch: Any,
    capsys: Any,
) -> None:
    fake_report = {
        "passed": True,
        "classification": "passed",
        "simulation_status": "ok",
        "sim_backend": DEFAULT_SIM_BACKEND,
        "compile_timeout_sec": DEFAULT_SUBPROCESS_TIMEOUT_SEC,
        "simulation_timeout_sec": DEFAULT_SUBPROCESS_TIMEOUT_SEC,
        "sim_backend_metadata": {
            "compile_tool": "iverilog",
            "run_tool": "vvp",
            "compile_timeout_sec": DEFAULT_SUBPROCESS_TIMEOUT_SEC,
            "simulation_timeout_sec": DEFAULT_SUBPROCESS_TIMEOUT_SEC,
        },
        "summary": dict(EXPECTED_TOTALS),
        "cluster_summaries": [{"cluster": cluster, **EXPECTED_PER_CLUSTER, "errors": 0} for cluster in range(16)],
        "counts_passed": True,
        "full_row_audit": {"passed": True, "clusters": [], "root": {"passed": True}},
        "observed_cluster_hashes": ["abc"] * 16,
        "expected_cluster_hashes": ["abc"] * 16,
        "observed_root_hash": "root",
        "expected_root_hash": "root",
    }
    fake_config = {
        "top_name": "fake_top",
        "attention_score32_exact_local16_global_tree_cluster_sram_gqa8": {
            "cluster_producers": [54] * 8 + [53] * 8
        },
    }

    monkeypatch.setattr(
        "npu.eval.probe_attention_score32_exact_local16_global_tree_cluster_sram_gqa8.build_default_config",
        lambda: fake_config,
    )
    captured: dict[str, object] = {}

    def fake_build_report(**kwargs: object) -> dict[str, object]:
        captured.update(kwargs)
        return fake_report

    monkeypatch.setattr(
        "npu.eval.probe_attention_score32_exact_local16_global_tree_cluster_sram_gqa8.build_report",
        fake_build_report,
    )

    out = tmp_path / "nested" / "probe.json"
    out_md = tmp_path / "nested" / "probe.md"
    exit_code = main(
        ["--json", "--logical-head-groups", "4", "--out", str(out), "--out-md", str(out_md)]
    )

    assert exit_code == 0
    assert captured["logical_head_groups"] == 4
    assert captured["compile_timeout_sec"] is None
    assert captured["sim_backend"] == DEFAULT_SIM_BACKEND
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["passed"] is True
    assert payload["classification"] == "passed"
    assert "observed_cluster_rows" not in payload
    assert "expected_cluster_rows" not in payload
    assert "observed_root_rows" not in payload
    assert "expected_root_rows" not in payload
    markdown = out_md.read_text(encoding="utf-8")
    assert "# attention_score32_exact_local16_global_tree_cluster_sram_gqa8_probe" in markdown
    assert "- producer_handshakes: `8192`" in markdown
    stdout = capsys.readouterr().out
    assert json.loads(stdout) == payload
