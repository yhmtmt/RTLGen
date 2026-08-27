#!/usr/bin/env python3
"""Verify that routed direct-mesh rows retain all transport hierarchies and no debug state."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Any


NODE_PREFIXES = tuple(f"u_mesh.gen_nodes[{node}].u_router" for node in range(16))
COUNTER_MARKERS = (
    "accepted_flit_count",
    "forwarded_flit_count",
    "input_stall_cycles",
    "output_stall_cycles",
    "arbitration_contention_cycles",
    "max_input_occupancy",
    "route_flit_count",
)


def _tcl(odb: Path, report: Path) -> str:
    prefix_entries = " ".join(f"{{{prefix}}}" for prefix in NODE_PREFIXES)
    marker_entries = " ".join(f"{{{marker}}}" for marker in COUNTER_MARKERS)
    return f'''read_db {{{odb}}}
set block [ord::get_db_block]
set prefixes [list {prefix_entries}]
set markers [list {marker_entries}]
set node_counts [lrepeat 16 0]
set counter_cells 0
foreach inst [$block getInsts] {{
  set name [$inst getName]
  for {{set node 0}} {{$node < 16}} {{incr node}} {{
    if {{[string first [lindex $prefixes $node] $name] >= 0}} {{
      lset node_counts $node [expr {{[lindex $node_counts $node] + 1}}]
    }}
  }}
  foreach marker $markers {{
    if {{[string first $marker $name] >= 0}} {{
      incr counter_cells
      break
    }}
  }}
}}
set handle [open {{{report}}} w]
for {{set node 0}} {{$node < 16}} {{incr node}} {{
  puts $handle "NODE $node [lindex $node_counts $node]"
}}
puts $handle "COUNTER_CELLS $counter_cells"
close $handle
exit
'''


def parse_hierarchy_report(text: str) -> dict[str, Any]:
    node_counts: dict[int, int] = {}
    counter_cells: int | None = None
    for raw_line in text.splitlines():
        fields = raw_line.strip().split()
        if len(fields) == 3 and fields[0] == "NODE":
            node_counts[int(fields[1])] = int(fields[2])
        elif len(fields) == 2 and fields[0] == "COUNTER_CELLS":
            counter_cells = int(fields[1])
    if set(node_counts) != set(range(16)):
        raise ValueError(f"physical hierarchy report lacks nodes 0 through 15: {sorted(node_counts)}")
    missing = [node for node, count in sorted(node_counts.items()) if count <= 0]
    if missing:
        raise ValueError(f"physical direct mesh lost router hierarchy for nodes: {missing}")
    if counter_cells is None:
        raise ValueError("physical hierarchy report lacks debug-counter cell count")
    if counter_cells != 0:
        raise ValueError(f"physical direct mesh retained {counter_cells} debug-counter cells")
    return {
        "node_leaf_instance_counts": [node_counts[node] for node in range(16)],
        "total_router_leaf_instances": sum(node_counts.values()),
        "debug_counter_cell_count": counter_cells,
    }


def measure_odb(odb: Path) -> dict[str, Any]:
    openroad = shutil.which("openroad") or "/oss-cad-suite/bin/openroad"
    with tempfile.TemporaryDirectory(prefix="rtlgen-direct-mesh-") as td:
        report = Path(td) / "hierarchy.txt"
        subprocess.run(
            [openroad, "-exit"],
            input=_tcl(odb, report),
            text=True,
            check=True,
            capture_output=True,
            timeout=300,
        )
        return parse_hierarchy_report(report.read_text(encoding="utf-8"))


def check(metrics_csv: Path, out: Path, orfs_results_root: Path) -> dict[str, Any]:
    with metrics_csv.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError("direct mesh metrics contain no rows")

    design = metrics_csv.parent.name
    checked_rows: list[dict[str, Any]] = []
    failed_rows: list[dict[str, str]] = []
    for row in rows:
        status = str(row.get("status", "")).strip().lower()
        tag = str(row.get("tag", "")).strip()
        if status != "ok":
            failed_rows.append(
                {
                    "tag": tag,
                    "status": status,
                    "failure_stage": str(row.get("failure_stage", "")).strip(),
                    "failure_signature": str(row.get("failure_signature", "")).strip(),
                }
            )
            continue
        effective_variant = str(row.get("effective_flow_variant", "")).strip()
        if not effective_variant or "__" not in effective_variant:
            raise ValueError(f"successful direct mesh row lacks isolated flow variant: {tag}")
        odb = orfs_results_root / "nangate45" / design / effective_variant / "6_final.odb"
        if not odb.is_file():
            raise ValueError(f"successful direct mesh row lacks final ODB: {odb}")
        checked_rows.append(
            {
                "tag": tag,
                "effective_flow_variant": effective_variant,
                "odb_path": str(odb),
                **measure_odb(odb),
            }
        )

    payload = {
        "version": 1,
        "design": design,
        "status": "ok" if checked_rows else "no_successful_physical_rows",
        "required_router_nodes": 16,
        "debug_counters_enabled": False,
        "checked_rows": checked_rows,
        "failed_rows": failed_rows,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metrics-csv", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument(
        "--orfs-results-root",
        type=Path,
        default=Path("/orfs/flow/results"),
    )
    args = parser.parse_args()
    print(json.dumps(check(args.metrics_csv, args.out, args.orfs_results_root), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
