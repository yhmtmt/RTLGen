import hashlib
import json
import math
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
        assert "sequential_register_activity" in phase
        assert "sequential_register_activity_sha256" in phase
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

        sequential_activity_path = tmp_path / phase["sequential_register_activity"]
        assert sequential_activity_path.exists()
        sequential_raw = sequential_activity_path.read_bytes()
        assert phase["sequential_register_activity_sha256"] == hashlib.sha256(sequential_raw).hexdigest()
        sequential = json.loads(sequential_raw)
        assert sequential["version"] == 1
        assert sequential["model"] == "sequential_register_vcd_activity_v1"
        assert sequential["scope"] == "tb/dut"
        assert sequential["source_vcd"] == phase["vcd"]
        assert sequential["source_vcd_sha256"] == phase["vcd_sha256"]
        assert sequential["active_start_tick"] < sequential["active_end_tick"]
        assert sequential["timescale_seconds"] > 0
        assert sequential["register_bits"]
        assert sequential["register_bits"] == sorted(
            sequential["register_bits"], key=lambda row: row["full_name"]
        )
        register_bits = sequential["register_bits"]
        names = {row["full_name"] for row in register_bits}
        numerator_accum_names = {
            name for name in names if name.startswith("reducer/numerator_accum[")
        }
        score_accum_names = {name for name in names if name.startswith("score_tile/accum[")}
        block_weight_names = {name for name in names if name.startswith("reducer/block_weight[")}
        expected_numerator_accum_names = {
            f"reducer/numerator_accum[{word}][{bit}]"
            for word in range(128)
            for bit in range(41)
        }
        expected_score_accum_names = {
            f"score_tile/accum[{word}][{bit}]" for word in range(8) for bit in range(32)
        }
        expected_block_weight_names = {
            f"reducer/block_weight[{word}][{bit}]"
            for word in range(8)
            for bit in range(16)
        }
        assert len(numerator_accum_names) == 5_248
        assert numerator_accum_names == expected_numerator_accum_names
        assert len(score_accum_names) == 256
        assert score_accum_names == expected_score_accum_names
        assert len(block_weight_names) == 128
        assert block_weight_names == expected_block_weight_names
        assert {
            "reducer/numerator_accum[0][0]",
            "reducer/numerator_accum[0][40]",
            "reducer/numerator_accum[127][0]",
            "reducer/numerator_accum[127][40]",
            "score_tile/accum[0][0]",
            "score_tile/accum[0][31]",
            "score_tile/accum[7][0]",
            "score_tile/accum[7][31]",
            "reducer/block_weight[0][0]",
            "reducer/block_weight[0][15]",
        } <= names
        for row in register_bits:
            assert not row["full_name"].startswith("tb/dut/")
            assert row["source"] == "vcd"
            assert math.isfinite(row["density_hz"])
            assert row["density_hz"] >= 0.0
            assert math.isfinite(row["duty_cycle"])
            assert 0.0 <= row["duty_cycle"] <= 1.0
            assert math.isfinite(row["transition_count"])
            assert row["transition_count"] >= 0.0

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
