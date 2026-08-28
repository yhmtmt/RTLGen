from __future__ import annotations

import csv
from pathlib import Path

import pytest

from npu.eval.check_noc_segmented_mesh4x4_direct_physical import (
    NODE_PREFIXES,
    _tcl,
    check,
    parse_hierarchy_report,
)


def test_physical_hierarchy_report_requires_every_router_and_no_counters() -> None:
    report = "\n".join([f"NODE {node} {node + 1}" for node in range(16)] + ["COUNTER_CELLS 0"])
    parsed = parse_hierarchy_report(report)
    assert parsed["node_leaf_instance_counts"] == list(range(1, 17))
    assert parsed["total_router_leaf_instances"] == 136
    assert parsed["debug_counter_cell_count"] == 0

    with pytest.raises(ValueError, match="lost router hierarchy"):
        parse_hierarchy_report(report.replace("NODE 7 8", "NODE 7 0"))
    with pytest.raises(ValueError, match="retained 3 debug-counter cells"):
        parse_hierarchy_report(report.replace("COUNTER_CELLS 0", "COUNTER_CELLS 3"))


def test_physical_hierarchy_tcl_names_all_router_prefixes() -> None:
    script = _tcl(Path("/tmp/final.odb"), Path("/tmp/report.txt"))
    for prefix in NODE_PREFIXES:
        assert f"{{{prefix}}}" in script
        assert prefix.startswith("u_mesh/gen_nodes[")
        assert prefix.endswith("].u_router/")
    assert "accepted_flit_count" in script


def test_all_failed_physical_rows_are_retained_as_bounded_evidence(tmp_path: Path) -> None:
    metrics = tmp_path / "noc_segmented_mesh4x4_direct" / "metrics.csv"
    metrics.parent.mkdir(parents=True)
    with metrics.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["tag", "status", "failure_stage", "failure_signature"],
        )
        writer.writeheader()
        writer.writerow(
            {
                "tag": "direct",
                "status": "flow_failed",
                "failure_stage": "floorplan",
                "failure_signature": "pin placement infeasible",
            }
        )
    out = metrics.parent / "physical_hierarchy_report.json"
    payload = check(metrics, out, tmp_path / "orfs")
    assert payload["status"] == "no_successful_physical_rows"
    assert payload["checked_rows"] == []
    assert payload["failed_rows"][0]["failure_stage"] == "floorplan"
