from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PROPOSAL = REPO_ROOT / "docs/proposals/prop_l1_noc_sram_packet_mesh4x4_composed_ppa_v1"
ITEM_ID = "l1_noc_sram_packet_mesh4x4_composed_ppa_v1"


def _row(path: Path, key: str) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return next(row for row in payload[key] if row.get("item_id") == ITEM_ID)


def test_composed_endpoint_mesh_v1_is_non_dispatchable_in_both_manifests() -> None:
    for path, key in (
        (PROPOSAL / "evaluation_requests.json", "requested_items"),
        (PROPOSAL / "proposal.json", "required_evaluations"),
    ):
        row = _row(path, key)
        assert row["status"] == "superseded_obsolete_dependencies_and_floorplan"
        assert "Do not dispatch" in row["acceptance_notes"]


def test_composed_endpoint_mesh_revision_requires_measured_r2_floorplan() -> None:
    request = _row(PROPOSAL / "evaluation_requests.json", "requested_items")
    proposal = json.loads((PROPOSAL / "proposal.json").read_text(encoding="utf-8"))
    for revision in (request["revision"], proposal["revision"]):
        assert revision["reason"] == "obsolete_dependencies_and_unmatched_floorplan"
        assert "aggregate r4" in revision["replacement_plan"]
        assert "endpoint path identity" in revision["replacement_plan"]
