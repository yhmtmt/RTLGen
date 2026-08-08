import json
from pathlib import Path

import pytest

from npu.eval.audit_attention_decode_score_multivalue_service_exact_partial_physical_recost import (
    _validate_functional_probe,
)
from npu.eval.run_attention_decode_score_multivalue_service_finalized_cdc_lane_campaign import (
    _lightweight_probe_summary,
    _validate_campaign,
    run_campaign,
)


PROPOSAL_ID = "prop_l2_decoder_attention_decode_score_multivalue_service_finalized_cdc_lane_probe_v1"


def _campaign() -> dict:
    return {
        "model": "attention_decode_score_multivalue_service_finalized_cdc_lane_campaign_v1",
        "campaign_id": "attention_decode_score_multivalue_service_finalized_cdc_lane_probe_10ns_12ns_v1",
        "proposal_ref": {
            "proposal_id": PROPOSAL_ID,
            "proposal_path": f"docs/proposals/{PROPOSAL_ID}/proposal.json",
        },
        "fixed_parameters": {
            "service_period_ns": 10.0,
            "temporal_period_ns": 12.0,
            "temporal_state_backend": "sram",
            "service_value_memory_backend": "macro_banked_4x16x64x32",
        },
        "divider_lanes": [1, 2, 4, 8],
    }


def _probe_report(lane: int, *, passed: bool = True) -> dict:
    return {
        "model": "attention_decode_score_multivalue_service_finalized_cdc_probe_v1",
        "passed": passed,
        "service_period_ns": 10.0,
        "temporal_period_ns": 12.0,
        "divider_lanes": lane,
        "temporal_state_backend": "sram",
        "service_value_memory_backend": "macro_banked_4x16x64x32",
        "observed_rows": [[lane, 1, 2, 3]],
        "expected_rows": [[lane, 1, 2, 3]],
        "manifest": {"large": "omitted"},
        "macro_manifest": {"large": "omitted"},
        "summary": {
            "service_cycles": 120,
            "temporal_cycles": 36 + lane,
            "finalizer_cycles": 20 - lane,
            "cdc_accepted": 32,
            "cdc_emitted": 32,
            "finalizer_completed": 16,
        },
    }


@pytest.mark.parametrize(
    ("mutation", "error"),
    [
        (lambda payload: payload["fixed_parameters"].update(service_period_ns=9.0), "periods must be exactly"),
        (lambda payload: payload["fixed_parameters"].update(temporal_state_backend="behavioral"), "must be sram"),
        (
            lambda payload: payload["fixed_parameters"].update(service_value_memory_backend="behavioral"),
            "must be macro_banked_4x16x64x32",
        ),
        (lambda payload: payload.update(divider_lanes=[1, 2, 8]), r"exactly \[1, 2, 4, 8\]"),
        (lambda payload: payload["proposal_ref"].update(proposal_id="prop_wrong"), "proposal_ref must match"),
    ],
)
def test_validate_campaign_rejects_unbounded_contract(mutation, error: str) -> None:
    payload = _campaign()
    mutation(payload)
    with pytest.raises(ValueError, match=error):
        _validate_campaign(payload)


def test_lightweight_summary_is_direct_recost_input() -> None:
    campaign = _validate_campaign(_campaign())
    summary = _lightweight_probe_summary(_probe_report(4), campaign=campaign, lane=4)

    assert summary["model"] == "attention_decode_score_multivalue_service_finalized_cdc_probe_v1"
    assert summary["divider_lanes"] == 4
    assert summary["service_period_ns"] == 10.0
    assert summary["temporal_period_ns"] == 12.0
    assert summary["temporal_state_backend"] == "sram"
    assert summary["service_value_memory_backend"] == "macro_banked_4x16x64x32"
    assert "observed_rows" not in summary
    assert "expected_rows" not in summary
    assert "manifest" not in summary
    assert "macro_manifest" not in summary
    assert _validate_functional_probe(summary)["divider_lanes"] == 4


def test_run_campaign_writes_four_atomic_lightweight_outputs(tmp_path: Path) -> None:
    campaign_path = tmp_path / "campaign.json"
    campaign_path.write_text(json.dumps(_campaign()), encoding="utf-8")
    calls: list[dict] = []

    def probe_runner(**kwargs):
        calls.append(kwargs)
        return _probe_report(kwargs["divider_lanes"])

    out_root = tmp_path / "outputs"
    aggregate = run_campaign(
        campaign_path=campaign_path,
        out_root=out_root,
        probe_runner=probe_runner,
    )

    assert [call["divider_lanes"] for call in calls] == [1, 2, 4, 8]
    assert all(call["service_period_ns"] == 10.0 for call in calls)
    assert all(call["temporal_period_ns"] == 12.0 for call in calls)
    assert all(call["temporal_state_backend"] == "sram" for call in calls)
    assert all(call["service_value_memory_backend"] == "macro_banked_4x16x64x32" for call in calls)
    assert aggregate["passed"] is True
    assert aggregate["point_count"] == 4
    assert sorted(path.name for path in out_root.iterdir()) == [
        "campaign_summary.json",
        "lane1.json",
        "lane2.json",
        "lane4.json",
        "lane8.json",
    ]
    for lane in (1, 2, 4, 8):
        payload = json.loads((out_root / f"lane{lane}.json").read_text(encoding="utf-8"))
        assert payload["divider_lanes"] == lane
        assert _validate_functional_probe(payload)["temporal_period_ns"] == 12.0


def test_run_campaign_publishes_nothing_when_a_probe_fails(tmp_path: Path) -> None:
    campaign_path = tmp_path / "campaign.json"
    campaign_path.write_text(json.dumps(_campaign()), encoding="utf-8")
    out_root = tmp_path / "outputs"

    def probe_runner(**kwargs):
        return _probe_report(kwargs["divider_lanes"], passed=kwargs["divider_lanes"] != 4)

    with pytest.raises(RuntimeError, match="divider_lanes=4"):
        run_campaign(
            campaign_path=campaign_path,
            out_root=out_root,
            probe_runner=probe_runner,
        )
    assert not out_root.exists()
