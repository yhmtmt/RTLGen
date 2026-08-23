"""Attach reusable hierarchy-area evidence to physical metrics rows."""

from __future__ import annotations

import csv
import json
import math
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
HIERARCHY_METHOD = "openroad_final_odb_leaf_master_area_v1"
HIERARCHY_FIELDS = (
    "hierarchical_instance_area_um2",
    "hierarchical_instance_count",
    "hierarchy_area_prefix",
    "hierarchy_area_method",
    "hierarchy_area_report",
)
METRICS_TAIL_FIELDS = ("params_json", "result_path")


def _fail(message: str) -> None:
    raise SystemExit(message)


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        _fail(f"expected JSON object: {path}")
    return payload


def _safe_float(value: object) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def find_final_odb(design_dir: Path, tag: str, params_json: str) -> Path | None:
    try:
        params = json.loads(params_json) if params_json else {}
    except json.JSONDecodeError:
        params = {}
    design = design_dir.name
    candidates: list[Path] = []
    flow_variant = str(params.get("FLOW_VARIANT", "")).strip()
    if flow_variant:
        candidates.append(
            Path("/orfs/flow/results") / "nangate45" / design / flow_variant / "6_final.odb"
        )
    candidates.extend(
        [
            Path("/orfs/flow/results") / "nangate45" / design / tag / "6_final.odb",
            Path("/orfs/flow/results") / "nangate45" / design / "base" / "6_final.odb",
        ]
    )
    return next((path for path in candidates if path.is_file()), None)


def hierarchy_tcl(*, odb: Path, report: Path, prefix: str) -> str:
    return f'''read_db {{{odb}}}
set block [ord::get_db_block]
set dbu [$block getDbUnitsPerMicron]
set prefix {{{prefix}}}
set matched_count 0
set matched_area_dbu2 0.0
set total_count 0
set total_area_dbu2 0.0
foreach inst [$block getInsts] {{
  set master [$inst getMaster]
  set area_dbu2 [expr {{double([$master getWidth]) * double([$master getHeight])}}]
  set total_count [expr {{$total_count + 1}}]
  set total_area_dbu2 [expr {{$total_area_dbu2 + $area_dbu2}}]
  if {{[string first $prefix [$inst getName]] == 0}} {{
    set matched_count [expr {{$matched_count + 1}}]
    set matched_area_dbu2 [expr {{$matched_area_dbu2 + $area_dbu2}}]
  }}
}}
set scale [expr {{double($dbu) * double($dbu)}}]
set report [open {{{report}}} w]
puts $report "{{"
puts $report "  \"prefix\": \"$prefix\","
puts $report "  \"matched_instance_count\": $matched_count,"
puts $report "  \"matched_instance_area_um2\": [expr {{$matched_area_dbu2 / $scale}}],"
puts $report "  \"unmatched_instance_count\": [expr {{$total_count - $matched_count}}],"
puts $report "  \"unmatched_instance_area_um2\": [expr {{($total_area_dbu2 - $matched_area_dbu2) / $scale}}],"
puts $report "  \"total_instance_count\": $total_count,"
puts $report "  \"total_instance_area_um2\": [expr {{$total_area_dbu2 / $scale}}]"
puts $report "}}"
close $report
exit
'''


def measure_hierarchy(*, odb: Path, report: Path, prefix: str) -> dict[str, Any]:
    openroad = shutil.which("openroad") or "/oss-cad-suite/bin/openroad"
    if not Path(openroad).is_file() and shutil.which(openroad) is None:
        _fail("openroad is required for hierarchical area reporting")
    report.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [openroad, "-exit"],
        input=hierarchy_tcl(odb=odb, report=report, prefix=prefix),
        text=True,
        check=True,
        cwd=REPO_ROOT,
        capture_output=True,
        timeout=300,
    )
    payload = _load(report)
    if payload.get("prefix") != prefix:
        _fail("hierarchy report prefix mismatch")
    if (_safe_float(payload.get("matched_instance_count")) or 0.0) <= 0:
        _fail("hierarchy report matched no physical instances")
    if (_safe_float(payload.get("matched_instance_area_um2")) or 0.0) <= 0:
        _fail("hierarchy report matched no physical area")
    return payload


def attach_hierarchy_reports(
    design_dir: Path,
    *,
    prefix: str,
    precheck: Callable[[Path], None],
    repo_root: Path = REPO_ROOT,
) -> None:
    precheck(design_dir)
    metrics_path = design_dir / "metrics.csv"
    if not metrics_path.is_file():
        _fail(f"metrics.csv is missing: {metrics_path}")
    with metrics_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        original_fields = list(reader.fieldnames or [])
        rows = list(reader)
    if not rows:
        _fail("metrics.csv contains no rows")
    fieldnames = [
        field
        for field in original_fields
        if field not in HIERARCHY_FIELDS and field not in METRICS_TAIL_FIELDS
    ]
    fieldnames.extend(HIERARCHY_FIELDS)
    fieldnames.extend(field for field in METRICS_TAIL_FIELDS if field in original_fields)

    reports_dir = design_dir / "hierarchy_reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_index: list[dict[str, Any]] = []
    for row in rows:
        if str(row.get("status", "")).strip().lower() != "ok":
            continue
        tag = str(row.get("tag", "")).strip()
        odb = find_final_odb(design_dir, tag, str(row.get("params_json", "")))
        if odb is None:
            _fail(f"no final OpenDB found for successful metrics row tag={tag}")
        report = reports_dir / f"{tag}.json"
        payload = measure_hierarchy(odb=odb, report=report, prefix=prefix)
        row["hierarchical_instance_area_um2"] = payload["matched_instance_area_um2"]
        row["hierarchical_instance_count"] = payload["matched_instance_count"]
        row["hierarchy_area_prefix"] = prefix
        row["hierarchy_area_method"] = HIERARCHY_METHOD
        row["hierarchy_area_report"] = str(report.relative_to(repo_root))
        report_index.append(
            {
                "tag": tag,
                "odb_path": str(odb),
                "report_path": str(report.relative_to(repo_root)),
                "hierarchical_instance_area_um2": payload["matched_instance_area_um2"],
                "hierarchical_instance_count": payload["matched_instance_count"],
                "hierarchy_area_prefix": prefix,
                "hierarchy_area_method": HIERARCHY_METHOD,
            }
        )

    with metrics_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)
    (reports_dir / "index.json").write_text(
        json.dumps(
            {
                "version": 1,
                "design": design_dir.name,
                "status": "ok" if report_index else "no_successful_physical_rows",
                "hierarchy_area_prefix": prefix,
                "hierarchy_area_method": HIERARCHY_METHOD,
                "rows": report_index,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
