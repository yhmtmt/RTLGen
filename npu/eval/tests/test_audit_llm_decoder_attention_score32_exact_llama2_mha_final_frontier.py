from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.eval.audit_llm_decoder_attention_score32_exact_llama2_mha_final_frontier import (  # noqa: E402
    _DECISION_HOLD,
    _DECISION_PASS,
    build_report,
)


def _recost() -> dict:
    return {
        "version": 1,
        "model": "llm_decoder_attention_score32_global_hbm_exact_llama2_mha_recost_v1",
        "decision": "exact_llama2_mha_recost_recorded_native_quality_required",
        "rows": [
            {
                "candidate_id": "score32_gqa8_global_hbm_finite_endpoint",
                "model_contract": {
                    "contract_scope": "llama7b_shaped_gqa8_proxy_not_exact_llama2_7b",
                    "hidden_size": 4096,
                    "attention_heads": 32,
                    "kv_heads": 4,
                    "gqa_group_size": 8,
                    "kv_sharing": "gqa8",
                },
                "throughput": {
                    "token_throughput_per_s": 34.5,
                    "token_latency_us": 28985.507246,
                },
                "physical": {
                    "total_embodied_area_um2": 780_000_000,
                },
                "energy": {
                    "total_proxy_energy_mj_per_token": 880.0,
                },
                "remaining_abstractions": [
                    "HBM controller service is deterministic burst replay, not controller RTL or vendor timing signoff.",
                    "Logic energy is an always-on vectorless upper proxy; workload clock-gating activity is not measured.",
                ],
            },
            {
                "candidate_id": "score32_exact_llama2_7b_mha_global_hbm_finite_endpoint",
                "model_contract": {
                    "contract_scope": "exact_llama2_7b_mha_structure",
                    "hidden_size": 4096,
                    "attention_heads": 32,
                    "kv_heads": 32,
                    "gqa_group_size": 1,
                    "kv_sharing": "mha",
                },
                "throughput": {
                    "token_throughput_per_s": 4.4043,
                    "token_latency_us": 227050.832595,
                },
                "physical": {
                    "total_embodied_area_um2": 790_000_000,
                },
                "energy": {
                    "total_proxy_energy_mj_per_token": 6893.038,
                },
                "remaining_abstractions": [
                    "The fixed shared-SRAM residency policy is recosted but not reoptimized for MHA.",
                ],
            },
        ],
        "remaining_abstractions": [
            "HBM energy is command calibrated rather than vendor current signoff.",
            "Native Llama-2-7B score32 generation quality has not been measured.",
        ],
    }


def _quality(*, status: str = "mixed_int8_generation_quality_pass", model_id: str = "meta-llama/Llama-2-7b-hf") -> dict:
    return {
        "version": 1.0,
        "quality_gate": "mixed_int8_generation_quality",
        "model": {
            "model_id": model_id,
            "resolved_model_id": model_id,
            "expected_model_id": "meta-llama/Llama-2-7b-hf",
            "hidden_size": 4096,
            "attention_head_count": 32,
            "kv_head_count": 32,
            "gqa_group_size": 1.0,
            "structural_contract_status": "pass",
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
        "decision": {
            "status": status,
        },
        "summary": {
            "prompt_count": 8,
        },
    }


def _quality_frontier() -> dict:
    return {
        "version": 1,
        "model": "llm_decoder_attention_score32_integrated_frontier_ranking_v1",
        "rows": [
            {
                "candidate_id": "measured_exact_fp16_gqa8_kv8_reference",
                "family": "measured_exact_fp16_gqa8_kv8",
                "promotable": False,
                "quality_backed": False,
                "token_throughput_per_s": 12.0,
                "latency_us": 83333.333333,
                "compute_area_mm2": 479.6,
                "die_area_mm2": 1200.0,
                "energy_mj_per_token": 120.0,
                "remaining_abstractions": [
                    "Profile-scaled SRAM activity remains approximate.",
                ],
            },
            {
                "candidate_id": "planning_only_history",
                "family": "abstract",
                "promotable": False,
                "quality_backed": False,
                "precision_status": "planning_only",
            },
        ],
    }


def test_exact_quality_pass_yields_promotable_frontier_with_unchanged_candidate_ids() -> None:
    result = build_report(
        recost=_recost(),
        generation_quality=_quality(),
        quality_frontier=_quality_frontier(),
    )

    assert result["model"] == "llama2_7b_score32_exact_mha_final_frontier_v1"
    assert result["decision"] == _DECISION_PASS
    assert result["scalar_universal_winner"] is None
    assert result["dimension_winners"] == {
        "throughput_comparable_boundary": "score32_gqa8_global_hbm_finite_endpoint",
        "embodied_area_comparable_boundary": "score32_gqa8_global_hbm_finite_endpoint",
        "energy_comparable_boundary": "score32_gqa8_global_hbm_finite_endpoint",
        "precision_comparable_boundary": [
            "score32_gqa8_global_hbm_finite_endpoint",
            "score32_exact_llama2_7b_mha_global_hbm_finite_endpoint",
        ],
        "higher_precision_noncomparable_reference": "measured_exact_fp16_gqa8_kv8_reference",
    }

    promotable = result["promotable_pareto_frontier"]
    assert [row["candidate_id"] for row in promotable] == [
        "score32_exact_llama2_7b_mha_global_hbm_finite_endpoint"
    ]
    assert promotable[0]["promotable"] is True
    assert promotable[0]["quality_backed"] is True

    all_rows = {row["candidate_id"]: row for row in result["all_rows"]}
    assert all_rows["score32_gqa8_global_hbm_finite_endpoint"]["promotable"] is False
    assert all_rows["score32_gqa8_global_hbm_finite_endpoint"]["structural_quality_backed"] is False
    assert all_rows["measured_exact_fp16_gqa8_kv8_reference"]["promotable"] is False

    engineering = [row["candidate_id"] for row in result["engineering_pareto_frontier"]]
    assert engineering == ["score32_gqa8_global_hbm_finite_endpoint"]
    references = result["noncomparable_reference_rows"]
    assert [row["candidate_id"] for row in references] == [
        "measured_exact_fp16_gqa8_kv8_reference"
    ]
    assert references[0]["embodied_area_mm2"] is None
    assert references[0]["area_metric_status"] == "compute_only_not_total_embodied_noncomparable"


def test_quality_hold_keeps_exact_mha_nonpromotable_but_preserves_engineering_frontier() -> None:
    result = build_report(
        recost=_recost(),
        generation_quality=_quality(status="mixed_int8_generation_quality_hold"),
        quality_frontier=_quality_frontier(),
    )

    assert result["decision"] == _DECISION_HOLD
    assert result["promotable_pareto_frontier"] == []
    exact_row = next(
        row for row in result["all_rows"] if row["candidate_id"] == "score32_exact_llama2_7b_mha_global_hbm_finite_endpoint"
    )
    assert exact_row["promotable"] is False
    assert exact_row["quality_backed"] is False
    assert "quality gate" in exact_row["promotion_blocker"]


def test_exact_identity_rejection_requires_official_llama2_checkpoint() -> None:
    with pytest.raises(ValueError, match="generation quality model_id mismatch"):
        build_report(
            recost=_recost(),
            generation_quality=_quality(model_id="mistralai/Mistral-7B-v0.1"),
            quality_frontier=_quality_frontier(),
        )


def test_remaining_abstractions_preserve_required_frontier_caveats() -> None:
    result = build_report(
        recost=_recost(),
        generation_quality=_quality(),
        quality_frontier=_quality_frontier(),
    )

    abstractions = result["remaining_abstractions"]
    assert "HBM controller service remains deterministic global replay rather than controller RTL or vendor timing signoff." in abstractions
    assert "Logic energy remains a vectorless activity proxy rather than workload-toggle-complete power." in abstractions
    assert "Fixed shared-SRAM residency is recosted but not reoptimized for exact MHA." in abstractions
    assert "Native exact Llama-2-7B quality is bounded to a limited prompt sample rather than a full benchmark suite." in abstractions
    assert "Exact FP16 MHA has not been physically recosted on the same accounting boundary." in abstractions
