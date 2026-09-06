from __future__ import annotations

import json
from pathlib import Path

import pytest

from npu.eval.audit_llama7b_score32_cadence_frontier_consistency import build_report


ROOT = Path(__file__).resolve().parents[1]


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_checked_in_frontier_retracts_stale_score32_latency() -> None:
    frontier_path = ROOT / (
        "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
        "decoder_attention_score32_integrated_frontier_ranking__"
        "l2_decoder_attention_score32_quality_aware_hbm_controller_replay_rtl_ppa_recost_"
        "frontier_llama7b_v1.json"
    )
    norm_path = ROOT / "npu/docs/generated/llama7b_rmsnorm_macro_banked_latency_composition.json"
    cadence_path = ROOT / (
        "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
        "decoder_attention_score32_folded_global_exact_reduction_recost__"
        "l2_decoder_attention_score32_folded_global_exact_reduction_recost_llama7b_v2_r2.json"
    )
    report = build_report(
        _load(frontier_path), frontier_path=frontier_path,
        norm=_load(norm_path), norm_path=norm_path,
        cadence=_load(cadence_path), cadence_path=cadence_path,
    )
    assert report["decision"] == "recorded_score32_latency_retracted_pending_cadence_integrated_recost"
    assert report["superseded_contract"]["attention_cycles_per_layer"] == 7888
    assert report["strict_serialized_sensitivity"]["replacement_attention_cycles_per_layer"] == 27608
    assert report["strict_serialized_sensitivity"]["corrected_layer_cycles"] == 27951
    assert report["strict_serialized_sensitivity"]["latency_us_before_rmsnorm"] == pytest.approx(43514.9217888)
    assert report["strict_serialized_sensitivity"]["latency_lead_preserved_across_serialized_rmsnorm_envelope"] is True
    assert report["pareto_status"]["recorded_two_point_set_physically_credible"] is False


def test_audit_requires_explicit_986_cycle_retraction(tmp_path: Path) -> None:
    frontier_path = ROOT / (
        "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
        "decoder_attention_score32_integrated_frontier_ranking__"
        "l2_decoder_attention_score32_quality_aware_hbm_controller_replay_rtl_ppa_recost_"
        "frontier_llama7b_v1.json"
    )
    norm_path = ROOT / "npu/docs/generated/llama7b_rmsnorm_macro_banked_latency_composition.json"
    cadence_path = ROOT / (
        "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
        "decoder_attention_score32_folded_global_exact_reduction_recost__"
        "l2_decoder_attention_score32_folded_global_exact_reduction_recost_llama7b_v2_r2.json"
    )
    cadence = _load(cadence_path)
    cadence["cadence_evidence"]["reference_986_cycles_sustained"] = True
    local_cadence = tmp_path / "cadence.json"
    local_cadence.write_text(json.dumps(cadence), encoding="utf-8")
    with pytest.raises(ValueError, match="does not explicitly retract"):
        build_report(
            _load(frontier_path), frontier_path=frontier_path,
            norm=_load(norm_path), norm_path=norm_path,
            cadence=cadence, cadence_path=local_cadence,
        )
