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
        "model_contract": {
            "contract_scope": "llama7b_shaped_gqa8_proxy_not_exact_llama2_7b",
            "hidden_size": 4096,
            "layers": 32,
            "attention_heads": 32,
            "kv_heads": 4,
            "gqa_group_size": 8,
            "kv_sharing": "gqa8",
            "sequence_length": 131072,
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


def _generation_quality(*, gqa_group_size: int = 4) -> dict:
    return {
        "version": 1.0,
        "quality_gate": "mixed_int8_generation_quality",
        "model": {
            "model_id": "mistralai/Mistral-7B-v0.1",
            "gqa_group_size": float(gqa_group_size),
            "generation_steps": 8,
        },
        "precision": {
            "candidate_id": "score32_exp_lut_div",
            "q_bits": 8,
            "k_bits": 8,
            "v_bits": 8,
            "score_bits": 32,
            "weight_bits": 16,
            "softmax_mode": "exp_lut_div_bucket20",
        },
        "decision": {"status": "mixed_int8_generation_quality_pass"},
        "summary": {"prompt_count": 8},
    }


def test_recost_validation_rejects_primitive_double_counting_flag() -> None:
    payload = _recost()
    payload["closure_flags"]["prior_primitive_area_power_replaced_not_added"] = False

    with pytest.raises(ValueError, match="communication flag"):
        _validate_finite_recost(payload)


def test_final_frontier_keeps_two_engineering_points_but_promotes_neither_structure() -> None:
    result = build_report(
        finite_recost=_recost(),
        quality_frontier=_frontier(),
        generation_quality=_generation_quality(),
    )

    assert result["decision"] == "no_structurally_quality_backed_exact_llama7b_point"
    assert result["conditional_recommendation"]["unconditional_best"] is None
    assert result["pareto_frontier"] == []
    assert len(result["engineering_pareto_frontier"]) == 2
    score32, fp16 = result["engineering_pareto_frontier"]
    assert score32["token_throughput_per_s"] == 74.0
    assert score32["total_embodied_area_mm2"] == 760.03
    assert score32["energy_mj_per_token"] == pytest.approx(484.00135135135134)
    assert fp16["energy_mj_per_token"] == 82.0
    assert score32["arithmetic_quality_backed"] is True
    assert score32["structural_quality_backed"] is False
    assert score32["promotable"] is False
    assert fp16["structural_quality_backed"] is False
    assert result["dimension_winners"]["token_throughput"] == score32["candidate_id"]
    assert result["dimension_winners"]["energy_per_token"] == fp16["candidate_id"]
    assert result["excluded_nonpromotable_history"] == [
        {"candidate_id": "invalid-fast", "family": "abstract", "reason": "planning_only"}
    ]


def test_final_frontier_rejects_quality_regression() -> None:
    frontier = _frontier()
    frontier["rows"][0]["quality"]["status"] = "mixed_int8_generation_quality_fail"

    with pytest.raises(ValueError, match="quality evidence is not passing"):
        build_report(
            finite_recost=copy.deepcopy(_recost()),
            quality_frontier=frontier,
            generation_quality=_generation_quality(),
        )


def test_dimension_winner_uses_measured_throughput_not_candidate_identity() -> None:
    recost = _recost()
    recost["throughput"]["token_throughput_per_s"] = 10.0
    recost["throughput"]["token_latency_us"] = 100000.0

    result = build_report(
        finite_recost=recost,
        quality_frontier=_frontier(),
        generation_quality=_generation_quality(),
    )

    assert result["dimension_winners"]["token_throughput"] == "fp16-reference"


def test_matching_trained_gqa8_evidence_promotes_score32_structure() -> None:
    result = build_report(
        finite_recost=_recost(),
        quality_frontier=_frontier(),
        generation_quality=_generation_quality(gqa_group_size=8),
    )

    score32 = result["engineering_pareto_frontier"][0]
    assert score32["structural_quality_backed"] is True
    assert score32["promotable"] is True
    assert [row["candidate_id"] for row in result["pareto_frontier"]] == [score32["candidate_id"]]
