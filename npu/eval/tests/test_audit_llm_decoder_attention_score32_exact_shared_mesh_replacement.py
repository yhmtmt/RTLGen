from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from npu.eval.audit_llm_decoder_attention_score32_exact_shared_mesh_replacement import (
    build_contract,
    render_markdown,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
BASE = REPO_ROOT / "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
EXACT = BASE / (
    "decoder_attention_score32_exact_reduction_recost__"
    "l2_decoder_attention_score32_exact_reduction_recost_llama7b_v1.json"
)
FRONTIER = BASE / (
    "decoder_attention_score32_exact_reduction_gqa8_full_equivalence_rerank__"
    "l2_decoder_attention_score32_exact_reduction_gqa8_full_equivalence_rerank_llama7b_v1.json"
)
MATERIALIZED = REPO_ROOT / (
    "docs/proposals/prop_l1_attention_score32_exact_dual_producer_shared_mesh_ppa_activity_v1/"
    "replacement_contract.json"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_current_frontier_has_exact_non_overlapping_replacement_boundary() -> None:
    report = build_contract(exact_reduction=_load(EXACT), frontier=_load(FRONTIER))
    area = report["area_ownership"]

    assert area["source_replaced_primitive_overhead"]["area_um2"] == pytest.approx(480367.9308)
    assert area["source_ranked_compute_area_um2"] == pytest.approx(296826366.2009)
    assert area["retained_area_um2"] == pytest.approx(656696176.0132041)
    assert area["maximum_composed_hierarchy_area_um2"] == pytest.approx(143303823.9867959)
    assert area["source_ranked_area_omits_primitive_overhead"] is True
    assert report["measured_replacement_contract"]["required_hierarchy_prefixes"] == [
        "composition/vc0_activity/service/",
        "composition/vc1_activity/exact_transport_wrapper/",
        "composition/shared_transport/",
    ]
    assert report["source_frontier"]["token_throughput_per_s"] == pytest.approx(74.137971543343)
    assert report["source_frontier"]["quality_backed"] is True
    assert "vectorless" in report["post_measurement_gates"]["energy"]
    assert "maximum composed hierarchy area" in render_markdown(report)


def test_materialized_replacement_contract_matches_current_sources() -> None:
    materialized = _load(MATERIALIZED)
    current = build_contract(exact_reduction=_load(EXACT), frontier=_load(FRONTIER))

    assert materialized["model"] == current["model"]
    assert materialized["source_frontier"] == current["source_frontier"]
    assert materialized["area_ownership"] == current["area_ownership"]
    assert materialized["measured_replacement_contract"] == current["measured_replacement_contract"]
    assert materialized["post_measurement_gates"] == current["post_measurement_gates"]


def test_replacement_contract_rejects_source_primitive_accounting_drift() -> None:
    exact = copy.deepcopy(_load(EXACT))
    exact["best_requested"]["selected_l1_overhead_area_um2"] += 1.0

    with pytest.raises(ValueError, match="primitive area ownership mismatch"):
        build_contract(exact_reduction=exact, frontier=_load(FRONTIER))


def test_replacement_contract_rejects_ranked_area_ownership_drift() -> None:
    frontier = copy.deepcopy(_load(FRONTIER))
    row = next(
        row
        for row in frontier["promotable_latency_rank"]
        if row["candidate_id"] == "score32_exp_lut_schedule_wrapper_hbm_controller_replay_best"
    )
    row["compute_area_mm2"] += 0.001

    with pytest.raises(ValueError, match="ranked score32 area ownership mismatch"):
        build_contract(exact_reduction=_load(EXACT), frontier=frontier)
