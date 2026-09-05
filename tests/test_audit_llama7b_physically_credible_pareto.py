from __future__ import annotations

import json
from pathlib import Path

import pytest

from npu.eval.audit_llama7b_physically_credible_pareto import build_report, render_markdown


def _write(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value), encoding="utf-8")


def test_pareto_audit_excludes_noncredible_dominators(tmp_path: Path) -> None:
    frontier_path = tmp_path / "frontier.json"
    frontier = {
        "model": "llm_decoder_attention_score32_integrated_frontier_ranking_v1",
        "inputs": {"score32_activity_power_json": None},
        "rows": [
            {
                "candidate_id": "fast_quality_safe",
                "family": "score32",
                "promotable": True,
                "quality_backed": True,
                "latency_us": 10,
                "energy_mj_per_token": 100,
                "die_area_mm2": 8,
                "token_throughput_per_s": 100000,
            },
            {
                "candidate_id": "efficient_quality_safe",
                "family": "fp16",
                "promotable": True,
                "quality_backed": True,
                "latency_us": 50,
                "energy_mj_per_token": 20,
                "die_area_mm2": 12,
                "token_throughput_per_s": 20000,
            },
            {
                "candidate_id": "abstract_dominator",
                "family": "abstract",
                "promotable": False,
                "quality_backed": False,
                "latency_us": 1,
                "energy_mj_per_token": 1,
                "die_area_mm2": 1,
                "token_throughput_per_s": 1000000,
            },
        ],
    }
    _write(frontier_path, frontier)
    norm_path = tmp_path / "norm.json"
    norm = {
        "model": "llama7b_rmsnorm_macro_banked_latency_composition_v2",
        "baseline": {"candidate_id": "fast_quality_safe", "latency_us": 10},
        "attention_scope_proof": {
            "status": "verified_attention_only_excludes_transformer_rmsnorm",
            "excluded_terms": ["pre_attention_rmsnorm", "pre_mlp_rmsnorm", "final_rmsnorm"],
        },
        "rmsnorm_scope": {"rows_per_token": 65},
        "rmsnorm_candidates": [
            {"candidate_id": "macro_banked_three_credit", "row_cycles": 1035}
        ],
        "rows": [
            {
                "rmsnorm_candidate_id": "macro_banked_three_credit",
                "clock_period_ns": clock,
                "hidden_fraction": 0.0,
                "composed_latency_us": latency,
                "composed_token_throughput_per_s": 1.0e6 / latency,
            }
            for clock, latency in ((10.0, 11.0), (14.0, 12.0), (18.0, 13.0))
        ],
        "promotion_gate_pass": False,
    }
    _write(norm_path, norm)

    report = build_report(
        frontier,
        frontier_path=frontier_path,
        norm=norm,
        norm_path=norm_path,
    )
    assert [row["candidate_id"] for row in report["pareto_points"]] == [
        "fast_quality_safe",
        "efficient_quality_safe",
    ]
    assert report["excluded_points"][0]["candidate_id"] == "abstract_dominator"
    assert report["scope_guard"]["rmsnorm_rows_per_token"] == 65
    assert report["promotion_gate_pass"] is False
    assert "not activity-backed" in report["objective_evidence"]["energy"]
    assert report["rmsnorm_serialized_latency_robustness"]["latency_anchor_robust_across_envelope"] is True
    assert report["rmsnorm_serialized_latency_robustness"]["worst_case"]["composed_latency_us"] == 13.0
    markdown = render_markdown(report)
    assert "fast_quality_safe" in markdown
    assert "abstract_dominator" in markdown


def test_pareto_audit_requires_proven_norm_scope(tmp_path: Path) -> None:
    frontier_path = tmp_path / "frontier.json"
    frontier = {
        "model": "llm_decoder_attention_score32_integrated_frontier_ranking_v1",
        "rows": [
            {
                "candidate_id": "candidate",
                "promotable": True,
                "quality_backed": True,
                "latency_us": 1,
                "energy_mj_per_token": 1,
                "die_area_mm2": 1,
            }
        ],
    }
    _write(frontier_path, frontier)
    norm_path = tmp_path / "norm.json"
    norm = {
        "model": "llama7b_rmsnorm_macro_banked_latency_composition_v2",
        "attention_scope_proof": {"status": "unproven"},
    }
    _write(norm_path, norm)
    with pytest.raises(ValueError, match="scope exclusion"):
        build_report(
            frontier,
            frontier_path=frontier_path,
            norm=norm,
            norm_path=norm_path,
        )
