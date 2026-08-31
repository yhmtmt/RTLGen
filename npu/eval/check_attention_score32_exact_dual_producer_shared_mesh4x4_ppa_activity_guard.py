#!/usr/bin/env python3
"""Guard composed dual-producer shared-mesh physical artifacts."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Sequence

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_KEY = "attention_score32_exact_dual_producer_shared_mesh4x4_ppa_activity_harness"
MANIFEST_NAME = "attention_score32_exact_dual_producer_shared_mesh4x4_ppa_activity_harness_manifest.json"
PROPOSAL_ID = "prop_l1_attention_score32_exact_dual_producer_shared_mesh_ppa_activity_v1"
HIERARCHY_PREFIXES = (
    "composition/vc0_activity/service/",
    "composition/vc1_activity/exact_transport_wrapper/",
    "composition/shared_transport/",
)
HIERARCHY_METHOD = "openroad_final_odb_leaf_master_area_disjoint_prefix_sum_v1"
HIERARCHY_FIELDS = (
    "hierarchical_instance_area_um2",
    "hierarchical_instance_count",
    "hierarchy_area_prefix",
    "hierarchy_area_prefixes",
    "hierarchy_area_method",
    "hierarchy_area_report",
)
METRICS_TAIL_FIELDS = ("params_json", "result_path")
EXACT_TREE_TOP = "attention_score32_exact_banked_finalized_tree_factored_c16_r2_l8_b59"


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
    seen: set[str] = set()
    for record in records:
        if not isinstance(record, dict):
            _fail("manifest source_files contains a non-object entry")
        relative = str(record.get("path", "")).strip()
        expected = str(record.get("sha256", "")).strip()
        path = REPO_ROOT / relative
        if not relative or relative in seen or not path.is_file() or len(expected) != 64:
            _fail(f"invalid manifest source record: {record}")
        seen.add(relative)
        if _sha256(path) != expected:
            _fail(f"source hash changed for {relative}")


def _check_config_and_proposal(design_dir: Path) -> tuple[dict[str, Any], str]:
    config = _load(design_dir / "config.json")
    body = config.get(CONFIG_KEY)
    if not isinstance(body, dict):
        _fail(f"config missing {CONFIG_KEY}")
    top_name = str(config.get("top_name", "")).strip()
    if not top_name or top_name != design_dir.name:
        _fail("top_name must match the design directory")
    if int(body.get("physical_banks", 0)) != 15 or int(body.get("use_fakeram", 0)) != 1:
        _fail("composed physical configuration must be PHYSICAL_BANKS=15 and USE_FAKERAM=1")
    prefixes = body.get("hierarchy_area_prefixes")
    if tuple(str(prefix).strip() for prefix in prefixes or ()) != HIERARCHY_PREFIXES:
        _fail("config hierarchy_area_prefixes mismatch")

    links = config.get("report_links")
    if not isinstance(links, dict) or links.get("proposal_id") != PROPOSAL_ID:
        _fail("config proposal linkage is missing or incorrect")
    proposal_path = REPO_ROOT / str(links.get("proposal_path", ""))
    if not proposal_path.is_file():
        _fail(f"linked proposal is missing: {proposal_path}")
    proposal = _load(proposal_path)
    if proposal.get("proposal_id") != PROPOSAL_ID or proposal.get("layer") != "layer1":
        _fail("linked proposal identity or layer is incorrect")
    return config, top_name


def _check_structural_contract(
    *, design_dir: Path, top_name: str, manifest: dict[str, Any], macro: dict[str, Any], rtl: str
) -> None:
    if manifest.get("top_name") != top_name or manifest.get("linked_proposal_id") != PROPOSAL_ID:
        _fail("generated manifest identity or proposal linkage mismatch")
    if manifest.get("top_pin_bits") != 163:
        _fail("generated top pin total must be 163 bits")
    pins = manifest.get("top_pin_inventory")
    if not isinstance(pins, dict) or pins.get("input_bits") != 35 or pins.get("output_bits") != 128:
        _fail("generated top pin inventory must be 35 input bits and 128 output bits")
    if manifest.get("hierarchy_area_prefixes") != list(HIERARCHY_PREFIXES):
        _fail("generated hierarchy prefix inventory mismatch")

    composition = manifest.get("composition")
    if not isinstance(composition, dict):
        _fail("composition manifest is missing")
    if composition.get("instance_name") != "composition":
        _fail("composed harness instance must be named composition")
    if composition.get("parameters") != {"PHYSICAL_BANKS": 15, "USE_FAKERAM": 1}:
        _fail("composition parameters are not fixed to the physical 15-bank point")
    if composition.get("dut_hierarchy_area_prefixes") != list(HIERARCHY_PREFIXES):
        _fail("composition DUT hierarchy prefixes are incomplete")
    if composition.get("stimulus_excluded_from_dut_area") is not True:
        _fail("composition must exclude stimulus from DUT area")

    tree = manifest.get("exact_global_tree")
    expected_tree = {
        "clusters": 16,
        "radix": 2,
        "value_slices": 16,
        "head_id_bits": 5,
        "divider_lanes": 8,
        "finalizer_banks": 59,
        "exp_scale_impl": "factored_h33_l64_mul_exact",
    }
    if not isinstance(tree, dict) or tree.get("module") != EXACT_TREE_TOP or tree.get("parameters") != expected_tree:
        _fail("exact global tree contract is not c16/r2/l8/b59")

    vc0 = manifest.get("vc0_service")
    if not isinstance(vc0, dict) or {
        "virtual_channel": vc0.get("virtual_channel"),
        "remote_contexts": vc0.get("remote_contexts"),
        "waves": vc0.get("waves"),
        "packets_per_context": vc0.get("packets_per_context"),
        "total_packets": vc0.get("total_packets"),
        "flits_per_packet": vc0.get("flits_per_packet"),
        "total_flits": vc0.get("total_flits"),
    } != {
        "virtual_channel": 0,
        "remote_contexts": 112,
        "waves": 7,
        "packets_per_context": 68,
        "total_packets": 7616,
        "flits_per_packet": 8,
        "total_flits": 60928,
    }:
        _fail("VC0 traffic contract mismatch")
    vc1 = manifest.get("vc1_exact_reduction")
    if not isinstance(vc1, dict) or {
        "virtual_channel": vc1.get("virtual_channel"),
        "groups": vc1.get("groups"),
        "packets_per_group": vc1.get("packets_per_group"),
        "flits_per_group": vc1.get("flits_per_group"),
        "total_packets": vc1.get("total_packets"),
        "total_flits": vc1.get("total_flits"),
    } != {
        "virtual_channel": 1,
        "groups": 4,
        "packets_per_group": 315,
        "flits_per_group": 2505,
        "total_packets": 1260,
        "total_flits": 10020,
    }:
        _fail("VC1 traffic contract mismatch")
    transport = manifest.get("shared_transport")
    if not isinstance(transport, dict) or {
        "module": transport.get("module"),
        "mesh_module": transport.get("mesh_module"),
        "mesh_count": transport.get("mesh_count"),
        "injection_arbiter_module": transport.get("injection_arbiter_module"),
        "injection_arbiter_count": transport.get("injection_arbiter_count"),
        "virtual_channels": transport.get("virtual_channels"),
    } != {
        "module": "noc_shared_vc_dual_producer_transport4x4",
        "mesh_module": "noc_segmented_mesh4x4",
        "mesh_count": 1,
        "injection_arbiter_module": "noc_endpoint_vc_injection_arbiter",
        "injection_arbiter_count": 16,
        "virtual_channels": 2,
    }:
        _fail("shared transport contract mismatch")

    required_modules = (
        top_name,
        "attention_score32_exact_dual_producer_shared_mesh4x4_ppa_activity_harness",
        "attention_shared_stream_context_service_ppa_activity_harness",
        "attention_shared_stream_context_service",
        "attention_shared_stream_context_admission",
        "attention_shared_stream_context_engine",
        "noc_sram_packet_endpoint_array16",
        "noc_sram_packet_endpoint",
        "local_reducer_aggregate_stats_once_exact_shared_root_transport_ppa_activity_harness",
        "local_reducer_aggregate_stats_once_exact_shared_root_transport_wrapper",
        "local_reducer_aggregate_stats_once_exact_packet_tx_framer",
        "local_reducer_aggregate_stats_once_exact_packet_rx_deframer",
        "local_reducer_aggregate_stats_once_exact_encoder",
        "local_reducer_aggregate_stats_once_exact_decoder",
        "local_reducer_aggregate_stats_once_exact_sram_packet_adapter",
        "local_reducer_aggregate_stats_once_exact_shared_root_rx_adapter",
        "local_reducer_aggregate_stats_once_exact_shared_root_leaf_adapter",
        "local_reducer_aggregate_stats_once_exact_shared_root_global_tree_composition",
        "local_reducer_aggregate_stats_once_exact_shared_root_group_admission",
        "local_reducer_aggregate_stats_once_exact_shared_root_storage_fabric",
        "noc_endpoint_vc_injection_arbiter",
        "noc_shared_vc_dual_producer_transport4x4",
        "noc_segmented_mesh4x4",
        "noc_segmented_mesh_router",
        "noc_ready_valid_fifo",
        EXACT_TREE_TOP,
        "fakeram45_64x32",
    )
    for module in required_modules:
        if f"module {module}" not in rtl:
            _fail(f"generated top is missing required module {module}")
    for fragment in (
        f"module {top_name} (",
        "input wire clk",
        "input wire rst_n",
        "input wire enable",
        "input wire [31:0] control",
        "output wire [127:0] observable",
        "attention_score32_exact_dual_producer_shared_mesh4x4_ppa_activity_harness #(",
        ") composition (",
        ") vc0_activity (",
        ") vc1_activity (",
        "shared_transport (",
        ".INTERNAL_MESH(0)",
        "`ifndef SYNTHESIS",
        "module fakeram45_64x32",
        "localparam integer NODES = 16",
        "for (endpoint_g = 0; endpoint_g < NODES; endpoint_g = endpoint_g + 1)",
    ):
        if fragment not in rtl:
            _fail(f"generated top is missing required structural fragment: {fragment}")
    if len(
        re.findall(
            r"\bnoc_shared_vc_dual_producer_transport4x4\s+shared_transport\s*\(",
            rtl,
        )
    ) != 1:
        _fail("generated top must contain exactly one shared_transport composition")
    if rtl.count(".INTERNAL_MESH(0)") != 2:
        _fail("both activity producers must use the shared external mesh boundary")

    root_storage = manifest.get("root_storage")
    if not isinstance(root_storage, dict) or root_storage.get("macro_type") != "fakeram45_64x32":
        _fail("root-storage macro type is missing")
    if root_storage.get("macro_count") != 120 or manifest.get("macro_count") != 120:
        _fail("generated root-storage macro count must be exactly 120")
    if manifest.get("blackbox_instance_counts") != {"fakeram45_64x32": 120}:
        _fail("generated blackbox inventory must contain exactly 120 fakeram45_64x32 macros")
    power_scope = manifest.get("power_scope")
    if not isinstance(power_scope, dict) or not power_scope.get("whole_harness_power_is_upper_bound"):
        _fail("manifest must mark whole-harness power as an upper bound")
    if power_scope.get("stimulus_logic_is_dut_area") is not False:
        _fail("manifest must exclude stimulus logic from DUT area")

    if macro.get("design_id") != top_name or macro.get("module") != top_name:
        _fail("macro manifest identity mismatch")
    if macro.get("linked_proposal_id") != PROPOSAL_ID:
        _fail("macro manifest proposal linkage mismatch")
    if macro.get("blackboxes") != ["fakeram45_64x32"]:
        _fail("macro manifest must contain only fakeram45_64x32")
    if macro.get("hierarchy_area_prefixes") != list(HIERARCHY_PREFIXES):
        _fail("macro manifest hierarchy prefix inventory mismatch")
    macro_params = macro.get("manifest_params")
    if (
        not isinstance(macro_params, dict)
        or macro_params.get("macro_count") != 120
        or macro_params.get("root_storage_macro_count") != 120
        or macro.get("macro_count") != 120
    ):
        _fail("macro manifest must declare exactly 120 macros")
    if macro.get("blackbox_instance_counts") != {"fakeram45_64x32": 120}:
        _fail("macro manifest blackbox inventory must contain exactly 120 macros")
    inventory = macro.get("macro_inventory")
    if not isinstance(inventory, list) or len(inventory) != 1:
        _fail("macro inventory must contain one exact root-storage entry")
    if inventory[0].get("module") != "fakeram45_64x32" or inventory[0].get("count") != 120:
        _fail("macro inventory must contain exactly 120 fakeram45_64x32 macros")
    macro_power = macro.get("power_scope")
    if not isinstance(macro_power, dict) or not macro_power.get("whole_harness_power_is_upper_bound"):
        _fail("macro manifest must carry the whole-harness power upper-bound scope")
    if macro_power.get("stimulus_logic_is_dut_area") is not False:
        _fail("macro manifest must exclude stimulus logic from DUT area claims")
    _check_source_hashes(manifest)


def check(design_dir: Path) -> None:
    _, top_name = _check_config_and_proposal(design_dir)
    verilog_dir = design_dir / "verilog"
    rtl_path = verilog_dir / "top.v"
    manifest = _load(verilog_dir / MANIFEST_NAME)
    macro = _load(verilog_dir / "macro_manifest.json")
    rtl = rtl_path.read_text(encoding="utf-8")
    _check_structural_contract(
        design_dir=design_dir, top_name=top_name, manifest=manifest, macro=macro, rtl=rtl
    )


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
    candidates: list[Path] = []
    flow_variant = str(params.get("FLOW_VARIANT", "")).strip()
    if flow_variant:
        candidates.append(Path("/orfs/flow/results") / "nangate45" / design / flow_variant / "6_final.odb")
    candidates.extend(
        (
            Path("/orfs/flow/results") / "nangate45" / design / tag / "6_final.odb",
            Path("/orfs/flow/results") / "nangate45" / design / "base" / "6_final.odb",
        )
    )
    return next((path for path in candidates if path.is_file()), None)


def _hierarchy_tcl(odb: Path, report: Path) -> str:
    prefixes = " ".join("{" + prefix + "}" for prefix in HIERARCHY_PREFIXES)
    prefix_json = json.dumps(list(HIERARCHY_PREFIXES), separators=(",", ":"))
    prefix_json_tcl = (
        prefix_json.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("[", "\\[")
        .replace("]", "\\]")
    )
    prefix_reports: list[str] = []
    for index, prefix in enumerate(HIERARCHY_PREFIXES):
        comma = "," if index + 1 < len(HIERARCHY_PREFIXES) else ""
        prefix_reports.append(
            f'puts $report "    {{\\"prefix\\": \\"{prefix}\\", '
            f'\\"matched_instance_count\\": $matched_count_{index}, '
            f'\\"matched_instance_area_um2\\": [expr {{$matched_area_dbu2_{index} / $scale}}]}}{comma}"'
        )
    prefix_report_text = "\n".join(prefix_reports)
    return f'''read_db {{{odb}}}
set block [ord::get_db_block]
set dbu [$block getDbUnitsPerMicron]
set prefixes [list {prefixes}]
set matched_count 0
set matched_area_dbu2 0.0
set total_count 0
set total_area_dbu2 0.0
set matched_count_0 0
set matched_count_1 0
set matched_count_2 0
set matched_area_dbu2_0 0.0
set matched_area_dbu2_1 0.0
set matched_area_dbu2_2 0.0
foreach inst [$block getInsts] {{
  set name [$inst getName]
  set master [$inst getMaster]
  set area_dbu2 [expr {{double([$master getWidth]) * double([$master getHeight])}}]
  set total_count [expr {{$total_count + 1}}]
  set total_area_dbu2 [expr {{$total_area_dbu2 + $area_dbu2}}]
  set matching_prefix_count 0
  set matching_prefix_index -1
  for {{set prefix_index 0}} {{$prefix_index < [llength $prefixes]}} {{incr prefix_index}} {{
    set prefix [lindex $prefixes $prefix_index]
    if {{[string first $prefix $name] == 0}} {{
      incr matching_prefix_count
      set matching_prefix_index $prefix_index
    }}
  }}
  if {{$matching_prefix_count > 1}} {{
    puts stderr "hierarchy prefixes overlap for instance $name"
    exit 2
  }}
  if {{$matching_prefix_index >= 0}} {{
    incr matched_count
    set matched_area_dbu2 [expr {{$matched_area_dbu2 + $area_dbu2}}]
    if {{$matching_prefix_index == 0}} {{
      incr matched_count_0
      set matched_area_dbu2_0 [expr {{$matched_area_dbu2_0 + $area_dbu2}}]
    }} elseif {{$matching_prefix_index == 1}} {{
      incr matched_count_1
      set matched_area_dbu2_1 [expr {{$matched_area_dbu2_1 + $area_dbu2}}]
    }} elseif {{$matching_prefix_index == 2}} {{
      incr matched_count_2
      set matched_area_dbu2_2 [expr {{$matched_area_dbu2_2 + $area_dbu2}}]
    }}
  }}
}}
set scale [expr {{double($dbu) * double($dbu)}}]
set report [open {{{report}}} w]
puts $report "{{"
puts $report "  \\"prefixes\\": {prefix_json_tcl},"
puts $report "  \\"matched_instance_count\\": $matched_count,"
puts $report "  \\"matched_instance_area_um2\\": [expr {{$matched_area_dbu2 / $scale}}],"
puts $report "  \\"unmatched_instance_count\\": [expr {{$total_count - $matched_count}}],"
puts $report "  \\"unmatched_instance_area_um2\\": [expr {{($total_area_dbu2 - $matched_area_dbu2) / $scale}}],"
puts $report "  \\"total_instance_count\\": $total_count,"
puts $report "  \\"total_instance_area_um2\\": [expr {{$total_area_dbu2 / $scale}}],"
puts $report "  \\"prefix_reports\\": \\["
{prefix_report_text}
puts $report "  \\]"
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
    if payload.get("prefixes") != list(HIERARCHY_PREFIXES):
        _fail("hierarchy report prefix inventory mismatch")
    if (_safe_float(payload.get("matched_instance_count")) or 0.0) <= 0:
        _fail("hierarchy report matched no physical instances")
    if (_safe_float(payload.get("matched_instance_area_um2")) or 0.0) <= 0:
        _fail("hierarchy report matched no physical area")
    prefix_reports = payload.get("prefix_reports")
    if not isinstance(prefix_reports, list) or len(prefix_reports) != len(HIERARCHY_PREFIXES):
        _fail("hierarchy report lacks one result per DUT prefix")
    for expected, item in zip(HIERARCHY_PREFIXES, prefix_reports):
        if not isinstance(item, dict) or item.get("prefix") != expected:
            _fail("hierarchy report prefix result mismatch")
        if (_safe_float(item.get("matched_instance_count")) or 0.0) <= 0:
            _fail(f"hierarchy report matched no instances for {expected}")
        if (_safe_float(item.get("matched_instance_area_um2")) or 0.0) <= 0:
            _fail(f"hierarchy report matched no area for {expected}")
    return payload


def attach_hierarchy_reports(design_dir: Path) -> None:
    check(design_dir)
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
    measured = 0
    report_index: list[dict[str, Any]] = []
    prefixes_json = json.dumps(list(HIERARCHY_PREFIXES), separators=(",", ":"))
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
        row["hierarchy_area_prefix"] = ";".join(HIERARCHY_PREFIXES)
        row["hierarchy_area_prefixes"] = prefixes_json
        row["hierarchy_area_method"] = HIERARCHY_METHOD
        row["hierarchy_area_report"] = str(report.relative_to(REPO_ROOT))
        report_index.append(
            {
                "tag": tag,
                "odb_path": str(odb),
                "report_path": str(report.relative_to(REPO_ROOT)),
                "hierarchical_instance_area_um2": payload["matched_instance_area_um2"],
                "hierarchical_instance_count": payload["matched_instance_count"],
                "hierarchy_area_prefixes": list(HIERARCHY_PREFIXES),
                "hierarchy_area_method": HIERARCHY_METHOD,
                "prefix_reports": payload["prefix_reports"],
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
                "hierarchy_area_prefixes": list(HIERARCHY_PREFIXES),
                "hierarchy_area_method": HIERARCHY_METHOD,
                "aggregation": "sum matched areas from disjoint prefixes",
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
