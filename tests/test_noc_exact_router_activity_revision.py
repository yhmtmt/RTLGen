from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PROPOSAL_DIR = REPO_ROOT / "docs/proposals/prop_l2_decoder_attention_score32_noc_router_postroute_activity_power_llama7b_v1"
OLD_ITEM = "l2_decoder_attention_score32_noc_router_postroute_activity_power_llama7b_v1"
NEW_ITEM = "l2_decoder_attention_score32_noc_exact_router_postroute_activity_power_llama7b_v2"
EXACT_REVISION = "l2_decoder_attention_score32_noc_phase2_exact_transport_revision_llama7b_v1"
RETRACTED_SCHEDULE = "l2_decoder_attention_score32_noc_phase2_schedule_llama7b_v1_r1"


def _items(path: Path) -> dict[str, dict[str, object]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    key = "requested_items" if "requested_items" in payload else "required_evaluations"
    return {row["item_id"]: row for row in payload[key]}


def test_exact_activity_revision_retracts_old_schedule_and_requires_exact_sources() -> None:
    for name in ("evaluation_requests.json", "proposal.json"):
        items = _items(PROPOSAL_DIR / name)
        assert items[OLD_ITEM]["status"] == "retracted_wrong_precision_and_release_contract"
        assert items[OLD_ITEM]["superseded_by_item_id"] == NEW_ITEM
        assert items[NEW_ITEM]["status"] == "pending_after_bare_router_ppa"
        dependencies = items[NEW_ITEM]["depends_on_item_ids"]
        assert EXACT_REVISION in dependencies
        assert "l1_attention_score32_exact_stats_once_transport_codec_ppa_v1" in dependencies
        assert "l1_segmented_xy_router_node5_bare_ppa_v1" in dependencies
        assert RETRACTED_SCHEDULE not in dependencies


def test_exact_activity_request_records_full_five_phase_transport_contract() -> None:
    items = _items(PROPOSAL_DIR / "evaluation_requests.json")
    contract = items[NEW_ITEM]["exact_transport_contract"]
    assert contract == {
        "partial_link_bits_per_beat": 419,
        "partial_payload_bits_per_beat": 328,
        "release_contract": "group_major_actual_valid_ready",
        "phase_count": 5,
        "shared_vc0_flits": 60928,
        "reduction_vc1_flits": 10020,
        "total_flits": 70948,
    }
