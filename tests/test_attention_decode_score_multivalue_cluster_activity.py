import hashlib
import json
import shutil
from pathlib import Path

import pytest

from npu.eval.generate_attention_decode_score_multivalue_cluster_activity import generate_phase_activity


def _tool_available(name: str) -> bool:
    return shutil.which(name) is not None or (Path("/oss-cad-suite/bin") / name).exists()


def _config() -> dict:
    return {
        "top_name": "attention_decode_score_multivalue_cluster_activity",
        "attention_decode_score_multivalue_cluster": {
            "max_blocks": 16384,
            "array_n": 8,
            "value_slices": 16,
            "divider_impl": "iterative_restoring",
            "score_scale_lanes_per_cycle": 1,
        },
    }


def test_multivalue_cluster_activity_generates_phase_vcds_and_manifest(tmp_path: Path) -> None:
    if not _tool_available("iverilog") or not _tool_available("vvp"):
        pytest.skip("iverilog/vvp unavailable")

    manifest = generate_phase_activity(_config(), tmp_path, block_count=2, head_dim=128, clock_period_ns=10.0)
    manifest_path = tmp_path / "attention_decode_score_multivalue_cluster_activity_manifest.json"
    assert manifest_path.exists()
    on_disk = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert on_disk == manifest

    assert manifest["activity_generation"] == "explicit_script_only"
    assert manifest["block_count"] == 2
    assert manifest["head_dim"] == 128
    assert manifest["clock_period_ns"] == 10.0
    assert manifest["max_blocks"] == 16384
    assert manifest["target_max_blocks"] == 16384
    assert manifest["phase_partition_cycle_sum"] == manifest["representative_full_transaction_cycles"]

    phases = {row["phase"]: row for row in manifest["phases"]}
    assert set(phases) == {"score_fill", "replay_value", "finalize_result"}

    for phase_name, phase in phases.items():
        vcd_path = tmp_path / phase["vcd"]
        assert vcd_path.exists()
        raw = vcd_path.read_bytes()
        assert raw
        assert phase["vcd_sha256"] == hashlib.sha256(raw).hexdigest()
        text = raw.decode("utf-8", errors="ignore")
        assert "$timescale" in text
        assert "$scope module tb $end" in text
        assert phase["measured_cycles"] > 0
        assert "macro_activity" in phase
        assert "macro_activity_sha256" in phase
        macro_activity_path = tmp_path / phase["macro_activity"]
        assert macro_activity_path.exists()
        sidecar_raw = macro_activity_path.read_bytes()
        assert phase["macro_activity_sha256"] == hashlib.sha256(sidecar_raw).hexdigest()
        macro = json.loads(sidecar_raw)
        assert macro["version"] == 1
        assert macro["model"] == "fakeram_macro_pin_vcd_activity_v1"
        assert macro["scope"] == "tb/dut"
        assert macro["source_vcd"] == phase["vcd"]
        assert macro["source_vcd_sha256"] == phase["vcd_sha256"]
        assert macro["active_start_tick"] < macro["active_end_tick"]
        assert macro["timescale_seconds"] > 0
        assert len(macro["pins"]) == 5096
        assert macro["pins"] == sorted(macro["pins"], key=lambda row: row["full_name"])

    score_fill = phases["score_fill"]
    assert (score_fill["measured_cycles"] - 1) % manifest["block_count"] == 0
    assert score_fill["scaling"]["kind"] == "fixed_setup_plus_linear_by_block_count"
    assert score_fill["scaling"]["cycles_per_block"] == (score_fill["measured_cycles"] - 1) // manifest["block_count"]
    assert score_fill["full_context_cycles"] == (
        1 + score_fill["scaling"]["cycles_per_block"] * manifest["target_max_blocks"]
    )

    replay_value = phases["replay_value"]
    assert replay_value["measured_cycles"] > 16
    assert replay_value["scaling"]["kind"] == "fixed_clear_plus_linear_by_block_count"
    assert replay_value["scaling"]["clear_cycles"] == 16
    assert replay_value["scaling"]["representative_block_count"] == 2
    assert replay_value["scaling"]["replay_cycles_per_block"] == (
        replay_value["measured_cycles"] - 16
    ) // manifest["block_count"]
    assert replay_value["full_context_cycles"] == (
        16 + replay_value["scaling"]["replay_cycles_per_block"] * 16384
    )
    assert replay_value["scaling"]["formula"] == "clear_cycles + replay_cycles_per_block * target_max_blocks"

    finalize_result = phases["finalize_result"]
    assert finalize_result["measured_cycles"] == 128 * 60 + 16
    assert finalize_result["scaling"] == {
        "kind": "fixed_per_command",
        "value_dimensions": 128,
        "divide_cycles_per_dimension": 60,
        "result_emit_cycles": 16,
        "target_max_blocks": 16384,
        "full_context_cycles": 128 * 60 + 16,
        "formula": "value_dimensions * divide_cycles_per_dimension + result_emit_cycles",
    }


@pytest.mark.parametrize("block_count", [1, 3])
def test_phase_scaling_is_invariant_across_representative_block_counts(
    tmp_path: Path, block_count: int
) -> None:
    if not _tool_available("iverilog") or not _tool_available("vvp"):
        pytest.skip("iverilog/vvp unavailable")
    manifest = generate_phase_activity(
        _config(), tmp_path, block_count=block_count, head_dim=128, clock_period_ns=8.0
    )
    phases = {row["phase"]: row for row in manifest["phases"]}
    assert phases["score_fill"]["scaling"]["cycles_per_block"] == 139
    assert phases["replay_value"]["scaling"]["replay_cycles_per_block"] == 68
    assert phases["score_fill"]["full_context_cycles"] == 1 + 139 * 16384
    assert phases["replay_value"]["full_context_cycles"] == 16 + 68 * 16384
    assert phases["finalize_result"]["full_context_cycles"] == 7696
    assert manifest["phase_partition_cycle_sum"] == manifest["representative_full_transaction_cycles"]
