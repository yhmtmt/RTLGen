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


def test_direct_mesh_depends_only_on_fresh_aggregate_revision() -> None:
    direct = _load(
        "docs/proposals/prop_l1_segmented_xy_mesh4x4_direct_ppa_v1/"
        "evaluation_requests.json"
    )["requested_items"][0]
    assert direct["paired_baseline_item_id"] == "l1_segmented_xy_mesh4x4_aggregate_ppa_v1_r2"
    assert "l1_segmented_xy_mesh4x4_aggregate_ppa_v1_r2" in direct["depends_on_item_ids"]
    assert "l1_segmented_xy_mesh4x4_aggregate_ppa_v1" not in direct["depends_on_item_ids"]
