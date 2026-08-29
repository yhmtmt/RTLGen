from __future__ import annotations

import json
from pathlib import Path

from scripts.run_sweep import cartesian_product, make_run_id


REPO_ROOT = Path(__file__).resolve().parents[1]


def _load(relative: str) -> dict:
    return json.loads((REPO_ROOT / relative).read_text(encoding="utf-8"))


def test_aggregate_r2_bypasses_stale_v1_parameter_identity() -> None:
    v1 = _load(
        "runs/campaigns/noc/l1_segmented_xy_mesh4x4/sweeps/"
        "nangate45_hierarchical_feasibility.json"
    )
    r2 = _load(
        "runs/campaigns/noc/l1_segmented_xy_mesh4x4/sweeps/"
        "nangate45_hierarchical_feasibility_r2.json"
    )
    v1_params = cartesian_product(v1["flow_params"])[0]
    r2_params = cartesian_product(r2["flow_params"])[0]
    assert "FLOW_VARIANT" not in v1_params
    assert r2_params["FLOW_VARIANT"] == "mesh4x4_aggregate_r2"
    assert make_run_id(v1_params) != make_run_id(r2_params)


def test_r3_intentionally_reuses_r2_parameter_identity_to_test_cache_gate() -> None:
    requests = _load(
        "docs/proposals/prop_l1_segmented_xy_mesh4x4_aggregate_ppa_v1/"
        "evaluation_requests.json"
    )["requested_items"]
    r2 = next(item for item in requests if item["item_id"].endswith("_r2"))
    r3 = next(item for item in requests if item["item_id"].endswith("_r3"))
    assert r2["status"] == "superseded_incomplete_cache_reuse"
    assert r2["superseded_by_item_id"] == r3["item_id"]
    assert r3["sweep_path"] == r2["sweep_path"]
    assert "Re-running ineligible cached run" in r3["acceptance_notes"]


def test_r4_uses_clean_flow_identity_and_requires_failure_evidence() -> None:
    requests = _load(
        "docs/proposals/prop_l1_segmented_xy_mesh4x4_aggregate_ppa_v1/"
        "evaluation_requests.json"
    )["requested_items"]
    r3 = next(item for item in requests if item["item_id"].endswith("_r3"))
    r4 = next(item for item in requests if item["item_id"].endswith("_r4"))
    sweep = _load(r4["sweep_path"])
    params = cartesian_product(sweep["flow_params"])[0]
    assert r3["status"] == "superseded_missing_orfs_failure_evidence"
    assert r3["superseded_by_item_id"] == r4["item_id"]
    assert params["FLOW_VARIANT"] == "mesh4x4_aggregate_r4_diag"
    assert r4["required_complete_ppa_rows"] == 1
    assert r4["expected_outputs"][-1].endswith("timing_debug_report.md")
    assert "exactly one complete finite PPA row" in r4["acceptance_notes"]
    assert "make_returncode" in r4["acceptance_notes"]
    assert "failure_evidence" in r4["acceptance_notes"]


def test_direct_mesh_depends_only_on_cache_safe_aggregate_revision() -> None:
    direct = _load(
        "docs/proposals/prop_l1_segmented_xy_mesh4x4_direct_ppa_v1/"
        "evaluation_requests.json"
    )["requested_items"][0]
    assert direct["paired_baseline_item_id"] == "l1_segmented_xy_mesh4x4_aggregate_ppa_v1_r4"
    assert "l1_segmented_xy_mesh4x4_aggregate_ppa_v1_r4" in direct["depends_on_item_ids"]
    assert "l1_segmented_xy_mesh4x4_aggregate_ppa_v1_r3" not in direct["depends_on_item_ids"]
    assert "l1_segmented_xy_mesh4x4_aggregate_ppa_v1_r2" not in direct["depends_on_item_ids"]
    assert "l1_segmented_xy_mesh4x4_aggregate_ppa_v1" not in direct["depends_on_item_ids"]
