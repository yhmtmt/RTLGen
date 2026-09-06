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
        "decoder_attention_score32_local_reducer_measured_recost__"
        "l2_decoder_attention_score32_local_reducer_measured_recost_llama7b_v1_r1.json"
    )
    report = build_report(
        _load(frontier_path), frontier_path=frontier_path,
        norm=_load(norm_path), norm_path=norm_path,
        cadence=_load(cadence_path), cadence_path=cadence_path,
    )
    assert report["decision"] == "recorded_score32_latency_retracted_pending_cadence_integrated_recost"
    assert report["superseded_contract"]["attention_cycles_per_layer"] == 7888
    recost = report["measured_local_reducer_recost"]
    assert recost["single_clock_latency_interval_us"] == pytest.approx([146083.473619, 172387.653024])
    assert recost["single_clock_latency_lead_preserved"] is False
    assert recost["dual_clock_latency_interval_us"] == pytest.approx([29360.930822, 50588.450822])
    assert recost["dual_clock_latency_lead_preserved_across_serialized_rmsnorm_envelope"] is True
    assert recost["local_reducer_area_interval_mm2"] == pytest.approx([52.753805, 92.3472])
    assert recost["remaining_area_headroom_to_fp16_interval_mm2"] == pytest.approx([90.4285637991, 130.0219587991])
    assert report["pareto_status"]["recorded_two_point_set_physically_credible"] is False


def test_audit_requires_matching_superseded_986_cycle_contract(tmp_path: Path) -> None:
    frontier_path = ROOT / (
        "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
        "decoder_attention_score32_integrated_frontier_ranking__"
        "l2_decoder_attention_score32_quality_aware_hbm_controller_replay_rtl_ppa_recost_"
        "frontier_llama7b_v1.json"
    )
    norm_path = ROOT / "npu/docs/generated/llama7b_rmsnorm_macro_banked_latency_composition.json"
    cadence_path = ROOT / (
        "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
        "decoder_attention_score32_local_reducer_measured_recost__"
        "l2_decoder_attention_score32_local_reducer_measured_recost_llama7b_v1_r1.json"
    )
    cadence = _load(cadence_path)
    cadence["schedule_recost"]["source_exact_reduction_contract"]["replica_recost_tile_service_cycles"] = 985
    local_cadence = tmp_path / "cadence.json"
    local_cadence.write_text(json.dumps(cadence), encoding="utf-8")
    with pytest.raises(ValueError, match="do not share"):
        build_report(
            _load(frontier_path), frontier_path=frontier_path,
            norm=_load(norm_path), norm_path=norm_path,
            cadence=cadence, cadence_path=local_cadence,
        )
