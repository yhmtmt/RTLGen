from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from npu.eval.audit_llm_decoder_attention_score32_exact_shared_mesh_service_envelope import (
    build_report,
    render_markdown,
)


ROOT = Path(__file__).resolve().parents[3]
PROPOSAL = ROOT / "docs/proposals/prop_l1_attention_score32_exact_dual_producer_shared_mesh_ppa_activity_v1"
BASE = ROOT / "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
REPLACEMENT = PROPOSAL / "replacement_contract.json"
OBSERVATION = PROPOSAL / "service_envelope_observation.json"
MATERIALIZED = PROPOSAL / "service_envelope.json"
EXACT = BASE / (
    "decoder_attention_score32_exact_reduction_recost__"
    "l2_decoder_attention_score32_exact_reduction_recost_llama7b_v1.json"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_service_envelope_sets_finite_capacity_threshold_without_overclaim() -> None:
    report = build_report(
        replacement=_load(REPLACEMENT),
        exact_reduction=_load(EXACT),
        observation=_load(OBSERVATION),
    )

    assert report["rtl_observation"]["service_cycles"] == 15769
    assert report["rtl_observation"]["vc0_done_cycle"] == 15769
    assert report["rtl_observation"]["vc1_done_cycle"] == 10219
    assert report["compute_comparison"]["source_compute_layer_time_ns"] == pytest.approx(421511.3976)
    assert report["compute_comparison"][
        "maximum_composed_clock_ns_for_standalone_service_to_fit_compute_window"
    ] == pytest.approx(26.73038224364259)
    assert "producer-release-coupled" in report["interpretation"]["does_not_prove"][0]
    assert "not a producer-coupled throughput result" in render_markdown(report)


def test_service_envelope_rejects_incomplete_or_mismatched_observation() -> None:
    observation = copy.deepcopy(_load(OBSERVATION))
    observation["service_cycles"] -= 1

    with pytest.raises(ValueError, match="later producer completion"):
        build_report(
            replacement=_load(REPLACEMENT),
            exact_reduction=_load(EXACT),
            observation=observation,
        )


def test_materialized_service_envelope_matches_current_sources() -> None:
    materialized = _load(MATERIALIZED)
    current = build_report(
        replacement=_load(REPLACEMENT),
        exact_reduction=_load(EXACT),
        observation=_load(OBSERVATION),
    )

    for key in ("model", "decision", "traffic", "rtl_observation", "compute_comparison", "interpretation"):
        assert materialized[key] == current[key]
    for source in materialized["source_refs"]:
        path = ROOT / source["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == source["sha256"]
