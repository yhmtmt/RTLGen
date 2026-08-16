from __future__ import annotations

import copy

import pytest

from npu.eval.audit_llm_decoder_attention_score32_finite_endpoint_final_frontier import (
    _validate_finite_recost,
    build_report,
)


def _recost() -> dict:
    return {
        "version": 1,
        "model": "llama7b_proxy",
        "profile": "decoder_attention_score32_noc_phase2_finite_endpoint_composed_recost",
        "decision": "score32_noc_phase2_finite_endpoint_composed_recost_recorded",
        "throughput": {
            "token_throughput_per_s": 74.0,
            "token_latency_us": 13513.5135135,
            "bottleneck": "compute",
        },
        "physical_recost": {
            "area_fit": True,
            "die_area_um2": 800_000_000,
            "total_embodied_area_um2": 760_000_000,
            "recost_logic_vectorless_energy_per_token_mj": 350.0,
        },
        "precision_contract": {
            "precision_profile": "q8_k8_v8_a32_s32_w16_exp_lut_div_b20_int8_compute",
            "semantic_profile": "score32_exp_lut_div",
            "arithmetic_changed_by_this_recost": False,
        },
        "closure_flags": {
            "finite_endpoint_and_mesh_cycle_equivalence_consumed": True,
            "aggregate_endpoint_mesh_ppa_consumed": True,
            "prior_primitive_area_power_replaced_not_added": True,
        },
        "remaining_abstractions": ["SRAM activity energy"],
    }


def _frontier() -> dict:
    return {
        "version": 1,
        "model": "llm_decoder_attention_score32_integrated_frontier_ranking_v1",
        "rows": [
            {
                "candidate_id": "old-score32",
                "family": "score32_exp_lut_div",
                "promotable": True,
                "quality_backed": True,
                "quality": {
                    "quality_backed": True,
                    "status": "mixed_int8_generation_quality_pass",
                },
                "hbm_energy_mj_per_token": 134.0,
                "score32_hbm_controller_replay_ppa": {
                    "controller_power_mw": 0.1,
                    "controller_area_mm2": 0.03,
                },
                "remaining_abstractions": ["vendor HBM signoff"],
            },
            {
                "candidate_id": "fp16-reference",
                "family": "measured_exact_fp16_gqa8_kv8",
                "promotable": True,
                "quality_backed": True,
                "precision_status": "conservative_native_gqa8_kv8",
                "token_throughput_per_s": 14.0,
                "latency_us": 71428.5714,
                "die_area_mm2": 1200.0,
                "energy_mj_per_token": 82.0,
                "abstraction_status": "measured_compute_with_source_backed_hbm_energy",
                "remaining_abstractions": ["profile-scaled SRAM energy"],
            },
            {
                "candidate_id": "invalid-fast",
                "family": "abstract",
                "promotable": False,
                "quality_backed": False,
                "precision_status": "planning_only",
            },
        ],
    }


def test_recost_validation_rejects_primitive_double_counting_flag() -> None:
    payload = _recost()
    payload["closure_flags"]["prior_primitive_area_power_replaced_not_added"] = False

    with pytest.raises(ValueError, match="communication flag"):
        _validate_finite_recost(payload)


def test_final_frontier_has_two_nondominated_quality_backed_points() -> None:
    result = build_report(finite_recost=_recost(), quality_frontier=_frontier())

    assert result["decision"] == "two_nondominated_precision_safe_points_no_universal_scalar_winner"
    assert result["conditional_recommendation"]["unconditional_best"] is None
    assert len(result["pareto_frontier"]) == 2
    score32, fp16 = result["pareto_frontier"]
    assert score32["token_throughput_per_s"] == 74.0
    assert score32["total_embodied_area_mm2"] == 760.03
    assert score32["energy_mj_per_token"] == pytest.approx(484.00135135135134)
    assert fp16["energy_mj_per_token"] == 82.0
    assert result["dimension_winners"]["token_throughput"] == score32["candidate_id"]
    assert result["dimension_winners"]["energy_per_token"] == fp16["candidate_id"]
    assert result["excluded_nonpromotable_history"] == [
        {"candidate_id": "invalid-fast", "family": "abstract", "reason": "planning_only"}
    ]


def test_final_frontier_rejects_quality_regression() -> None:
    frontier = _frontier()
    frontier["rows"][0]["quality"]["status"] = "mixed_int8_generation_quality_fail"

    with pytest.raises(ValueError, match="quality evidence is not passing"):
        build_report(finite_recost=copy.deepcopy(_recost()), quality_frontier=frontier)
