#!/usr/bin/env python3
"""Guard the compact exact transport physical-evaluation artifacts."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Sequence

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_KEY = "attention_score32_exact_shared_root_transport_ppa_activity_harness"
MANIFEST_NAME = "attention_score32_exact_shared_root_transport_ppa_activity_harness_manifest.json"
PROPOSAL_ID = "prop_l1_attention_score32_exact_shared_root_transport_ppa_activity_v1"
HIERARCHY_PREFIX = "composition/exact_transport_wrapper/"
EXACT_TREE_TOP = "attention_score32_exact_banked_finalized_tree_factored_c16_r2_l8_b59"
HIERARCHY_METHOD = "openroad_final_odb_leaf_master_area_v1"
HIERARCHY_FIELDS = (
    "hierarchical_instance_area_um2",
    "hierarchical_instance_count",
    "hierarchy_area_prefix",
    "hierarchy_area_method",
    "hierarchy_area_report",
)
METRICS_TAIL_FIELDS = ("params_json", "result_path")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"expected JSON object: {path}")
    return payload


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _fail(message: str) -> None:
    raise SystemExit(message)


def _check_source_hashes(manifest: dict[str, Any]) -> None:
    records = manifest.get("source_files")
    if not isinstance(records, list) or not records:
        _fail("manifest source_files inventory is missing")
    for record in records:
        if not isinstance(record, dict):
            _fail("manifest source_files contains a non-object entry")
        relative = str(record.get("path", "")).strip()
        expected = str(record.get("sha256", "")).strip()
        path = REPO_ROOT / relative
        if not relative or not path.is_file() or len(expected) != 64:
            _fail(f"invalid manifest source record: {record}")
        if _sha256(path) != expected:
            _fail(f"source hash changed for {relative}")


def check(design_dir: Path) -> None:
    config = _load(design_dir / "config.json")
    body = config.get(CONFIG_KEY)
    if not isinstance(body, dict):
        _fail(f"config missing {CONFIG_KEY}")
    top_name = str(config.get("top_name", "")).strip()
    if not top_name or top_name != design_dir.name:
        _fail("top_name must match the design directory")
    if int(body.get("physical_banks", 0)) != 15 or int(body.get("use_fakeram", 0)) != 1:
        _fail("compact transport physical configuration must be PHYSICAL_BANKS=15 and USE_FAKERAM=1")
    if str(body.get("hierarchy_area_prefix", "")).strip() != HIERARCHY_PREFIX:
        _fail("config hierarchy_area_prefix mismatch")

    links = config.get("report_links")
    if not isinstance(links, dict) or links.get("proposal_id") != PROPOSAL_ID:
        _fail("config proposal linkage is missing or incorrect")
    proposal_path = REPO_ROOT / str(links.get("proposal_path", ""))
    if not proposal_path.is_file():
        _fail(f"linked proposal is missing: {proposal_path}")
    proposal = _load(proposal_path)
    if proposal.get("proposal_id") != PROPOSAL_ID or proposal.get("layer") != "layer1":
        _fail("linked proposal identity or layer is incorrect")
    proposal_text = proposal_path.read_text(encoding="utf-8").lower()
    if "retracted l2" not in proposal_text and "retracted layer2" not in proposal_text:
        _fail("proposal must state that retracted L2 frontier items are not restored")

    verilog_dir = design_dir / "verilog"
    rtl_path = verilog_dir / "top.v"
    manifest = _load(verilog_dir / MANIFEST_NAME)
    macro = _load(verilog_dir / "macro_manifest.json")
    rtl = rtl_path.read_text(encoding="utf-8")

    if manifest.get("top_name") != top_name or manifest.get("linked_proposal_id") != PROPOSAL_ID:
        _fail("generated manifest identity or proposal linkage mismatch")
    if manifest.get("top_pin_bits") != 163:
        _fail("generated top pin total must be 163 bits")
    pins = manifest.get("top_pin_inventory")
    if not isinstance(pins, dict) or pins.get("input_bits") != 35 or pins.get("output_bits") != 128:
        _fail("generated top pin inventory must be 35 input bits and 128 output bits")
    if manifest.get("hierarchy_area_prefix") != HIERARCHY_PREFIX:
        _fail("generated hierarchy prefix mismatch")
    composition = manifest.get("composition")
    if not isinstance(composition, dict):
        _fail("composition manifest is missing")
    if composition.get("instance_name") != "composition":
        _fail("harness instance must be named composition")
    if composition.get("parameters") != {"PHYSICAL_BANKS": 15, "USE_FAKERAM": 1}:
        _fail("composition parameters are not fixed to the physical 15-bank point")
    power_scope = manifest.get("power_scope")
    if not isinstance(power_scope, dict) or not power_scope.get("whole_harness_power_is_upper_bound"):
        _fail("manifest must mark whole-harness power as an upper bound")
    if power_scope.get("stimulus_logic_is_dut_area") is not False:
        _fail("manifest must not claim stimulus logic is DUT area")

    required_modules = (
        top_name,
        "local_reducer_aggregate_stats_once_exact_shared_root_transport_ppa_activity_harness",
        "local_reducer_aggregate_stats_once_exact_shared_root_transport_wrapper",
        "local_reducer_aggregate_stats_once_exact_shared_root_global_tree_composition",
        EXACT_TREE_TOP,
        "local_reducer_aggregate_stats_once_exact_shared_root_storage_fabric",
        "local_reducer_aggregate_stats_once_exact_shared_root_rx_adapter",
    )
    for module in required_modules:
        if f"module {module}" not in rtl:
            _fail(f"generated top is missing required module {module}")
    if f"module {top_name} (" not in rtl:
        _fail("generated top module declaration is missing")
    for fragment in (
        "input wire clk",
        "input wire rst_n",
        "input wire enable",
        "input wire [31:0] control",
        "output wire [127:0] observable",
        ") composition (",
        ".PHYSICAL_BANKS(15)",
        ".USE_FAKERAM(1)",
        "local_reducer_aggregate_stats_once_exact_shared_root_transport_wrapper",
    ):
        if fragment not in rtl:
            _fail(f"generated top is missing required contract fragment: {fragment}")

    root_storage = manifest.get("root_storage")
    if not isinstance(root_storage, dict) or root_storage.get("macro_type") != "fakeram45_64x32":
        _fail("root-storage macro type is missing")
    if root_storage.get("macro_count") != 120 or manifest.get("macro_count") != 120:
        _fail("generated root-storage macro count must be exactly 120")
    if manifest.get("blackbox_instance_counts") != {"fakeram45_64x32": 120}:
        _fail("generated blackbox inventory must contain exactly 120 fakeram45_64x32 macros")
    if macro.get("module") != top_name or macro.get("linked_proposal_id") != PROPOSAL_ID:
        _fail("macro manifest identity or proposal linkage mismatch")
    if macro.get("blackboxes") != ["fakeram45_64x32"]:
        _fail("macro manifest must contain only fakeram45_64x32 as the blackbox")
    macro_params = macro.get("manifest_params")
    if (
        not isinstance(macro_params, dict)
        or macro_params.get("macro_count") != 120
        or macro.get("macro_count") != 120
    ):
        _fail("macro manifest must declare exactly 120 macros")
    if macro.get("blackbox_instance_counts") != {"fakeram45_64x32": 120}:
        _fail("macro manifest blackbox inventory must contain exactly 120 macros")
    if macro_params.get("root_storage_macro_count") != 120:
        _fail("macro manifest root-storage inventory must be exactly 120")
    if macro.get("hierarchy_area_prefix") != HIERARCHY_PREFIX:
        _fail("macro manifest hierarchy prefix mismatch")
    macro_power = macro.get("power_scope")
    if not isinstance(macro_power, dict) or not macro_power.get("whole_harness_power_is_upper_bound"):
        _fail("macro manifest must carry the whole-harness power upper-bound scope")
    if macro_power.get("stimulus_logic_is_dut_area") is not False:
        _fail("macro manifest must exclude stimulus logic from DUT area claims")
    inventory = macro.get("macro_inventory")
    if not isinstance(inventory, list) or len(inventory) != 1 or inventory[0].get("count") != 120:
        _fail("macro inventory must contain one exact 120-macro root-storage entry")
    _check_source_hashes(manifest)


def _safe_float(value: object) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _find_odb(design_dir: Path, tag: str, params_json: str) -> Path | None:
    try:
        params = json.loads(params_json) if params_json else {}
    except json.JSONDecodeError:
        params = {}
    design = design_dir.name
    candidates = []
    flow_variant = str(params.get("FLOW_VARIANT", "")).strip()
    if flow_variant:
        candidates.append(Path("/orfs/flow/results") / "nangate45" / design / flow_variant / "6_final.odb")
    candidates.extend(
        [
            Path("/orfs/flow/results") / "nangate45" / design / tag / "6_final.odb",
            Path("/orfs/flow/results") / "nangate45" / design / "base" / "6_final.odb",
        ]
    )
    return next((path for path in candidates if path.is_file()), None)


def _hierarchy_tcl(odb: Path, report: Path) -> str:
    return f'''read_db {{{odb}}}
set block [ord::get_db_block]
set dbu [$block getDbUnitsPerMicron]
set prefix {{{HIERARCHY_PREFIX}}}
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
puts $report "  \\"prefix\\": \\"$prefix\\","
puts $report "  \\"matched_instance_count\\": $matched_count,"
puts $report "  \\"matched_instance_area_um2\\": [expr {{$matched_area_dbu2 / $scale}}],"
puts $report "  \\"unmatched_instance_count\\": [expr {{$total_count - $matched_count}}],"
puts $report "  \\"unmatched_instance_area_um2\\": [expr {{($total_area_dbu2 - $matched_area_dbu2) / $scale}}],"
puts $report "  \\"total_instance_count\\": $total_count,"
puts $report "  \\"total_instance_area_um2\\": [expr {{$total_area_dbu2 / $scale}}]"
puts $report "}}"
close $report
exit
'''


def _measure_hierarchy(odb: Path, report: Path) -> dict[str, Any]:
    openroad = shutil.which("openroad") or "/oss-cad-suite/bin/openroad"
    if not Path(openroad).is_file() and shutil.which(openroad) is None:
        _fail("openroad is required for hierarchical area reporting")
    report.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [openroad, "-exit"],
        input=_hierarchy_tcl(odb, report),
        text=True,
        check=True,
        cwd=REPO_ROOT,
        capture_output=True,
        timeout=300,
    )
    payload = _load(report)
    if payload.get("prefix") != HIERARCHY_PREFIX:
        _fail("hierarchy report prefix mismatch")
    if (_safe_float(payload.get("matched_instance_count")) or 0.0) <= 0:
        _fail("hierarchy report matched no physical instances")
    if (_safe_float(payload.get("matched_instance_area_um2")) or 0.0) <= 0:
        _fail("hierarchy report matched no physical area")
    return payload


def attach_hierarchy_reports(design_dir: Path) -> None:
    check(design_dir)
    metrics_path = design_dir / "metrics.csv"
    if not metrics_path.is_file():
        _fail(f"metrics.csv is missing: {metrics_path}")
    with metrics_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)
    if not rows:
        _fail("metrics.csv contains no rows")
    fieldnames = [
        field
        for field in fieldnames
        if field not in HIERARCHY_FIELDS and field not in METRICS_TAIL_FIELDS
    ]
    fieldnames.extend(HIERARCHY_FIELDS)
    fieldnames.extend(field for field in METRICS_TAIL_FIELDS if field in (reader.fieldnames or []))
    reports_dir = design_dir / "hierarchy_reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    measured = 0
    report_index: list[dict[str, Any]] = []
    for row in rows:
        if str(row.get("status", "")).strip().lower() != "ok":
            continue
        tag = str(row.get("tag", "")).strip()
        odb = _find_odb(design_dir, tag, str(row.get("params_json", "")))
        if odb is None:
            _fail(f"no final OpenDB found for successful metrics row tag={tag}")
        report = reports_dir / f"{tag}.json"
        payload = _measure_hierarchy(odb, report)
        row["hierarchical_instance_area_um2"] = payload["matched_instance_area_um2"]
        row["hierarchical_instance_count"] = payload["matched_instance_count"]
        row["hierarchy_area_prefix"] = HIERARCHY_PREFIX
        row["hierarchy_area_method"] = HIERARCHY_METHOD
        row["hierarchy_area_report"] = str(report.relative_to(REPO_ROOT))
        report_index.append(
            {
                "tag": tag,
                "odb_path": str(odb),
                "report_path": str(report.relative_to(REPO_ROOT)),
                "hierarchical_instance_area_um2": payload["matched_instance_area_um2"],
                "hierarchical_instance_count": payload["matched_instance_count"],
                "hierarchy_area_prefix": HIERARCHY_PREFIX,
                "hierarchy_area_method": HIERARCHY_METHOD,
            }
        )
        measured += 1
    with metrics_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    (reports_dir / "index.json").write_text(
        json.dumps(
            {
                "version": 1,
                "design": design_dir.name,
                "status": "ok" if measured else "no_successful_physical_rows",
                "hierarchy_area_prefix": HIERARCHY_PREFIX,
                "hierarchy_area_method": HIERARCHY_METHOD,
                "rows": report_index,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--design-dir", type=Path, required=True)
    parser.add_argument("--post-sweep", action="store_true")
    args = parser.parse_args(argv)
    if args.post_sweep:
        attach_hierarchy_reports(args.design_dir)
    else:
        check(args.design_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
