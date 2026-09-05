from __future__ import annotations

from pathlib import Path

import pytest

from npu.eval.audit_llama7b_rmsnorm_latency_composition import build_report, render_markdown


def test_rmsnorm_latency_composition_is_fail_closed(tmp_path: Path) -> None:
    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text("{}", encoding="utf-8")
    baseline = {
        "diagnosis": {
            "current_recommended_candidate": "score32",
            "score32_latency_us": 10000.0,
            "score32_token_throughput_per_s": 100.0,
        }
    }
    baseline_path.write_text(__import__("json").dumps(baseline), encoding="utf-8")
    attention_scope_path = tmp_path / "attention.json"
    attention_scope = {
        "best_requested": {
            "replica_recost_qkv_cycles": 202,
            "tile_waves": 8,
            "replica_recost_tile_service_cycles": 994,
            "command_dispatch_cycles": 0,
            "cross_tile_reduction_cycles": 141,
            "kv_write_cycles": 10,
            "replica_recost_layer_cycles": 8305,
            "replica_recost_total_cycles": 265760,
            "layers": 32,
        }
    }
    attention_scope_path.write_text(__import__("json").dumps(attention_scope), encoding="utf-8")
    report = build_report(
        baseline,
        baseline_path=baseline_path,
        attention_scope=attention_scope,
        attention_scope_path=attention_scope_path,
    )

    assert report["rmsnorm_contract"]["rows_per_token"] == 65
    assert report["rmsnorm_contract"]["service_cycles_per_token"] == 117000
    assert report["promotion_gate_pass"] is False
    assert report["attention_scope_proof"]["status"] == "verified_attention_only_excludes_transformer_rmsnorm"
    assert report["attention_scope_proof"]["reconstructed_layer_cycles"] == 8305
    serialized_10ns = next(
        row for row in report["rows"] if row["clock_period_ns"] == 10.0 and row["hidden_fraction"] == 0.0
    )
    assert serialized_10ns["raw_rmsnorm_latency_us"] == 1170.0
    assert serialized_10ns["composed_latency_us"] == 11170.0
    fully_hidden = next(
        row for row in report["rows"] if row["clock_period_ns"] == 18.0 and row["hidden_fraction"] == 1.0
    )
    assert fully_hidden["composed_latency_us"] == 10000.0
    markdown = render_markdown(report)
    assert "pending_routed_ppa" in markdown
    assert "117000" in markdown


def test_rmsnorm_composition_rejects_unreconstructed_attention_scope(tmp_path: Path) -> None:
    baseline = {
        "diagnosis": {
            "current_recommended_candidate": "score32",
            "score32_latency_us": 10000.0,
            "score32_token_throughput_per_s": 100.0,
        }
    }
    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text(__import__("json").dumps(baseline), encoding="utf-8")
    scope = {
        "best_requested": {
            "replica_recost_qkv_cycles": 202,
            "tile_waves": 8,
            "replica_recost_tile_service_cycles": 994,
            "command_dispatch_cycles": 0,
            "cross_tile_reduction_cycles": 141,
            "kv_write_cycles": 10,
            "replica_recost_layer_cycles": 8306,
            "replica_recost_total_cycles": 265792,
            "layers": 32,
        }
    }
    scope_path = tmp_path / "scope.json"
    scope_path.write_text(__import__("json").dumps(scope), encoding="utf-8")
    with pytest.raises(ValueError, match="does not reconstruct"):
        build_report(
            baseline,
            baseline_path=baseline_path,
            attention_scope=scope,
            attention_scope_path=scope_path,
        )
