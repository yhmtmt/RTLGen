from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PROPOSALS = REPO_ROOT / "docs/proposals"
EXACT_REVISION = "l2_decoder_attention_score32_noc_phase2_exact_transport_revision_llama7b_v1"
RETRACTED = {
    "prop_l2_decoder_attention_score32_noc_phase2_measured_router_closure_v1": (
        "l2_decoder_attention_score32_noc_phase2_measured_router_closure_llama7b_v1",
        "retracted_wrong_precision_and_release_contract",
    ),
    "prop_l2_decoder_attention_score32_noc_phase2_measured_router_clock_reroute_v1": (
        "l2_decoder_attention_score32_noc_phase2_measured_router_clock_reroute_llama7b_v1",
        "retracted_wrong_precision_and_release_contract",
    ),
    "prop_l2_decoder_attention_score32_noc_phase2_composed_mesh_reroute_v1": (
        "l2_decoder_attention_score32_noc_phase2_composed_mesh_reroute_llama7b_v1",
        "retracted_wrong_precision_and_release_contract",
    ),
    "prop_l2_decoder_attention_score32_global_hbm_exact_llama2_mha_recost_v1": (
        "l2_decoder_attention_score32_global_hbm_exact_llama2_mha_recost_v1",
        "retracted_transitive_wrong_precision_and_release_contract",
    ),
    "prop_l2_decoder_attention_score32_exact_llama2_mha_final_frontier_v1": (
        "l2_decoder_attention_score32_exact_llama2_mha_final_frontier_v1",
        "retracted_transitive_wrong_precision_and_release_contract",
    ),
}


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_invalid_phase2_descendants_are_retracted_in_requests_and_proposals() -> None:
    for directory, (item_id, status) in RETRACTED.items():
        proposal_dir = PROPOSALS / directory
        requests = _load(proposal_dir / "evaluation_requests.json")["requested_items"]
        evaluations = _load(proposal_dir / "proposal.json")["required_evaluations"]
        for rows in (requests, evaluations):
            row = next(entry for entry in rows if entry.get("item_id") == item_id)
            assert row["status"] == status
            assert row["retracted_by_item_id"] == EXACT_REVISION


def test_exact_transport_revision_names_every_late_discovered_descendant() -> None:
    expected = {item_id for item_id, _status in RETRACTED.values()}
    proposal_dir = (
        PROPOSALS
        / "prop_l2_decoder_attention_score32_noc_phase2_exact_transport_revision_v1"
    )
    requests = _load(proposal_dir / "evaluation_requests.json")
    proposal = _load(proposal_dir / "proposal.json")
    for row in (
        requests["requested_items"][0],
        proposal["required_evaluations"][0],
    ):
        invalidated = set(row["revision"]["invalidates_item_ids"])
        assert expected <= invalidated


def test_no_active_request_descends_from_retracted_phase2_schedule() -> None:
    items: dict[str, dict] = {}
    for path in PROPOSALS.glob("*/evaluation_requests.json"):
        for row in _load(path).get("requested_items", []):
            if row.get("item_id"):
                items[row["item_id"]] = row

    invalid_schedule = "l2_decoder_attention_score32_noc_phase2_schedule_llama7b_v1_r1"
    tainted = {invalid_schedule}
    changed = True
    while changed:
        changed = False
        for item_id, row in items.items():
            if item_id == EXACT_REVISION or item_id in tainted:
                continue
            dependencies = set(row.get("depends_on_item_ids") or [])
            paired = row.get("paired_baseline_item_id")
            if paired:
                dependencies.add(paired)
            if dependencies & tainted:
                tainted.add(item_id)
                changed = True

    for item_id in tainted:
        status = str(items[item_id].get("status") or "")
        assert status.startswith(("retracted", "invalidated", "superseded")), (
            item_id,
            status,
        )
