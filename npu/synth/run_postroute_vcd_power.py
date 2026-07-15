#!/usr/bin/env python3
"""Measure post-route power from explicit phase VCD activity.

This utility intentionally lives outside the normal PPA sweep.  A regular
``run_block_sweep.py`` result remains vectorless; only this command may turn a
functional simulation trace into activity-backed power evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import tempfile
from typing import Any


JsonDict = dict[str, Any]
ORFS_FLOW = Path(os.environ.get("ORFS_FLOW", "/orfs/flow"))


def _load_json(path: Path) -> JsonDict:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"expected a JSON object: {path}")
    return raw


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _activity_annotation_counts(stdout: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for line in stdout.splitlines():
        match = re.fullmatch(r"\s*(vcd|saif|input|unannotated)\s+(\d+)\s*", line)
        if match:
            counts[match.group(1)] = int(match.group(2))
    return counts


def _phase_rows(manifest: JsonDict, manifest_path: Path) -> list[JsonDict]:
    raw_phases = manifest.get("phases")
    if not isinstance(raw_phases, list) or not raw_phases:
        raise ValueError("activity manifest requires a non-empty phases[]")
    rows: list[JsonDict] = []
    seen: set[str] = set()
    for index, raw in enumerate(raw_phases):
        if not isinstance(raw, dict):
            raise ValueError(f"phases[{index}] must be an object")
        phase = str(raw.get("phase", raw.get("name", ""))).strip()
        if not phase or phase in seen:
            raise ValueError(f"invalid or duplicate phase name at phases[{index}]")
        seen.add(phase)
        vcd_value = str(raw.get("vcd", raw.get("vcd_path", ""))).strip()
        if not vcd_value:
            raise ValueError(f"phase {phase} is missing vcd/vcd_path")
        vcd = Path(vcd_value)
        if not vcd.is_absolute():
            vcd = (manifest_path.parent / vcd).resolve()
        if not vcd.is_file():
            raise FileNotFoundError(f"phase VCD does not exist: {vcd}")
        expected_hash = str(raw.get("vcd_sha256", "")).strip().lower()
        actual_hash = _sha256(vcd)
        if expected_hash and expected_hash != actual_hash:
            raise ValueError(
                f"phase {phase} VCD hash mismatch: expected {expected_hash}, got {actual_hash}"
            )
        measured_cycles = int(raw.get("measured_cycles", raw.get("trace_cycles", 0)))
        scaling = raw.get("scaling") if isinstance(raw.get("scaling"), dict) else {}
        full_context_cycles = int(
            raw.get("full_context_cycles", scaling.get("full_context_cycles", 0))
        )
        if measured_cycles <= 0 or full_context_cycles <= 0:
            raise ValueError(
                f"phase {phase} requires positive measured_cycles and full_context_cycles"
            )
        rows.append(
            {
                **raw,
                "phase": phase,
                "vcd": vcd_value,
                "_resolved_vcd": str(vcd),
                "vcd_sha256": actual_hash,
                "measured_cycles": measured_cycles,
                "full_context_cycles": full_context_cycles,
                "requires_macro_activity": bool(
                    raw.get("requires_macro_activity", phase in {"score_fill", "replay_value"})
                ),
            }
        )
    return rows


def _tcl_script() -> str:
    return r'''source $::env(SCRIPTS_DIR)/load.tcl
load_design 6_final.odb 6_final.sdc
read_spef $::env(RESULTS_DIR)/6_final.spef
log_cmd read_vcd -scope $::env(RTLGEN_ACTIVITY_SCOPE) $::env(RTLGEN_ACTIVITY_VCD)

set annotatable 0
set vcd_count 0
set constant_count 0
set clock_count 0
set macro_annotatable 0
set macro_trace_active_count 0
foreach pin [get_pins -hierarchical *] {
  if {[get_property $pin is_hierarchical]} {
    continue
  }
  set direction [get_property $pin direction]
  if {$direction == "internal"} {
    continue
  }
  incr annotatable
  set activity [get_property $pin activity]
  set origin [lindex $activity 2]
  if {$origin == "vcd"} {
    incr vcd_count
  } elseif {$origin == "constant"} {
    incr constant_count
  } elseif {$origin == "clock"} {
    incr clock_count
  }
  set full_name [get_property $pin full_name]
  if {[string match "*u_group_*" $full_name]} {
    incr macro_annotatable
    set toggle_rate [lindex $activity 0]
    if {($origin == "vcd" || $origin == "propagated") && $toggle_rate > 0.0} {
      incr macro_trace_active_count
    }
  }
}

proc rtlgen_json_number {value} {
  if {[string match -nocase "*nan*" "$value"] ||
      [string match -nocase "*inf*" "$value"]} {
    return "null"
  }
  if {[catch {format "%.12g" $value} formatted]} {
    return "null"
  }
  return $formatted
}
set totals [sta::design_power [sta::corners]]
set clocks [get_clocks *]
set sdc_clock_period_ns "null"
if {[llength $clocks] > 0} {
  set sdc_clock_period_ns [rtlgen_json_number [get_property [lindex $clocks 0] period]]
}
set internal_w [rtlgen_json_number [lindex $totals 0]]
set switching_w [rtlgen_json_number [lindex $totals 1]]
set leakage_w [rtlgen_json_number [lindex $totals 2]]
set total_w [rtlgen_json_number [lindex $totals 3]]
set fp [open $::env(RTLGEN_ACTIVITY_RESULT) w]
puts $fp "{"
puts $fp "  \"internal_w\": $internal_w,"
puts $fp "  \"switching_w\": $switching_w,"
puts $fp "  \"leakage_w\": $leakage_w,"
puts $fp "  \"total_w\": $total_w,"
puts $fp "  \"sdc_clock_period_ns\": $sdc_clock_period_ns,"
puts $fp "  \"annotatable_pin_count\": $annotatable,"
puts $fp "  \"vcd_annotated_pin_count\": $vcd_count,"
puts $fp "  \"constant_pin_count\": $constant_count,"
puts $fp "  \"clock_pin_count\": $clock_count,"
puts $fp "  \"macro_annotatable_pin_count\": $macro_annotatable,"
puts $fp "  \"macro_trace_active_pin_count\": $macro_trace_active_count"
puts $fp "}"
close $fp

report_activity_annotation
report_power
'''


def _run_openroad_phase(
    *,
    design_config: Path,
    flow_variant: str,
    vcd: Path,
    scope: str,
    tcl: Path,
    result: Path,
    timeout_seconds: int,
) -> JsonDict:
    resolved_config = design_config.resolve()
    if not resolved_config.is_file():
        raise FileNotFoundError(f"ORFS design config does not exist: {resolved_config}")
    try:
        config_arg = str(resolved_config.relative_to(ORFS_FLOW.resolve()))
    except ValueError:
        # ORFS includes DESIGN_CONFIG directly, so an absolute out-of-tree
        # config is valid and useful for isolated workspaces.
        config_arg = str(resolved_config)
    recipe = (
        ".PHONY: rtlgen_activity_power\n"
        "rtlgen_activity_power:\n"
        f"\t@RTLGEN_ACTIVITY_VCD='{vcd}' "
        f"RTLGEN_ACTIVITY_SCOPE='{scope}' "
        f"RTLGEN_ACTIVITY_RESULT='{result}' "
        f"$(OPENROAD_CMD) '{tcl}'\n"
    )
    command = [
        "make",
        "--no-print-directory",
        f"DESIGN_CONFIG={config_arg}",
        f"FLOW_VARIANT={flow_variant}",
        "--eval",
        recipe,
        "rtlgen_activity_power",
    ]
    completed = subprocess.run(
        command,
        cwd=ORFS_FLOW,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
    )
    if completed.returncode:
        raise RuntimeError(
            "post-route VCD power failed:\n"
            f"command: {' '.join(command[:4])} ...\n"
            f"stdout:\n{completed.stdout}\n"
            f"stderr:\n{completed.stderr}"
        )
    if not result.is_file():
        raise RuntimeError("OpenROAD completed without writing the activity power result")
    payload = _load_json(result)
    annotation_counts = _activity_annotation_counts(completed.stdout)
    if "vcd" in annotation_counts and "unannotated" in annotation_counts:
        payload["leaf_vcd_annotated_pin_count"] = payload.get("vcd_annotated_pin_count", 0)
        payload["leaf_annotatable_pin_count"] = payload.get("annotatable_pin_count", 0)
        payload["vcd_annotated_pin_count"] = annotation_counts["vcd"]
        payload["annotatable_pin_count"] = sum(annotation_counts.values())
        payload["activity_annotation_counts"] = annotation_counts
    return payload


def _portable_repo_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(Path.cwd().resolve()))
    except ValueError:
        return path.name


def _orfs_relative_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ORFS_FLOW.resolve()))
    except ValueError:
        try:
            return str(path.resolve().relative_to(Path.cwd().resolve()))
        except ValueError:
            return path.name


def build_report(
    *,
    manifest: JsonDict,
    manifest_path: Path,
    design_config: Path,
    flow_variant: str,
    scope: str,
    min_vcd_coverage: float,
    min_vcd_pins: int,
    min_macro_active_coverage: float,
    min_macro_active_pins: int,
    timeout_seconds: int,
) -> JsonDict:
    clock_period_ns = float(manifest.get("clock_period_ns", 0.0))
    if clock_period_ns <= 0.0:
        raise ValueError("activity manifest requires positive clock_period_ns")
    phases = _phase_rows(manifest, manifest_path)
    measured: list[JsonDict] = []
    with tempfile.TemporaryDirectory(prefix="rtlgen-vcd-power-") as temp_text:
        temp = Path(temp_text)
        tcl = temp / "activity_power.tcl"
        tcl.write_text(_tcl_script(), encoding="utf-8")
        for phase in phases:
            result = temp / f"{phase['phase']}.json"
            power = _run_openroad_phase(
                design_config=design_config,
                flow_variant=flow_variant,
                vcd=Path(str(phase["_resolved_vcd"])),
                scope=scope,
                tcl=tcl,
                result=result,
                timeout_seconds=timeout_seconds,
            )
            annotatable = int(power.get("annotatable_pin_count", 0))
            annotated = int(power.get("vcd_annotated_pin_count", 0))
            coverage = annotated / annotatable if annotatable else 0.0
            macro_active = int(power.get("macro_trace_active_pin_count", 0))
            macro_annotatable = int(power.get("macro_annotatable_pin_count", 0))
            macro_coverage = macro_active / macro_annotatable if macro_annotatable else 0.0
            coverage_pass = annotated >= min_vcd_pins and coverage >= min_vcd_coverage
            macro_pass = not phase["requires_macro_activity"] or (
                macro_active >= min_macro_active_pins
                and macro_coverage >= min_macro_active_coverage
            )
            sdc_period_value = power.get("sdc_clock_period_ns")
            sdc_period_ns = float(sdc_period_value) if sdc_period_value is not None else 0.0
            clock_period_pass = abs(sdc_period_ns - clock_period_ns) <= 1e-6
            component_names = ("internal_w", "switching_w", "leakage_w", "total_w")
            component_values = [power.get(name) for name in component_names]
            power_numeric_pass = all(
                value is not None and math.isfinite(float(value)) and float(value) >= 0.0
                for value in component_values
            )
            total_value = power.get("total_w")
            total_w = float(total_value) if total_value is not None else 0.0
            power_numeric_pass = power_numeric_pass and total_w > 0.0
            full_cycles = int(phase["full_context_cycles"])
            energy_j = total_w * full_cycles * clock_period_ns * 1e-9
            measured.append(
                {
                    **{key: value for key, value in phase.items() if not key.startswith("_")},
                    "power": power,
                    "vcd_annotation_coverage": coverage,
                    "annotation_gate_pass": coverage_pass,
                    "macro_activity_gate_pass": macro_pass,
                    "macro_trace_active_coverage": macro_coverage,
                    "clock_period_gate_pass": clock_period_pass,
                    "power_numeric_gate_pass": power_numeric_pass,
                    "phase_gate_pass": coverage_pass and macro_pass and clock_period_pass and power_numeric_pass,
                    "full_context_energy_j": energy_j,
                }
            )
    gate_pass = all(bool(row["phase_gate_pass"]) for row in measured)
    total_cycles = sum(int(row["full_context_cycles"]) for row in measured)
    total_energy_j = sum(float(row["full_context_energy_j"]) for row in measured)
    return {
        "version": 1,
        "model": "postroute_phase_vcd_power_v1",
        "status": "activity_backed" if gate_pass else "rejected_annotation_gate",
        "promotion_gate_pass": gate_pass,
        "clock_period_ns": clock_period_ns,
        "scope": scope,
        "flow_variant": flow_variant,
        "orfs_design_config": _orfs_relative_path(design_config),
        "min_vcd_annotation_coverage": min_vcd_coverage,
        "min_vcd_annotated_pins": min_vcd_pins,
        "min_macro_trace_active_coverage": min_macro_active_coverage,
        "min_macro_trace_active_pins": min_macro_active_pins,
        "full_context_cycles": total_cycles,
        "full_context_latency_s": total_cycles * clock_period_ns * 1e-9,
        "full_context_energy_j": total_energy_j if gate_pass else None,
        "phases": measured,
        "source_activity_manifest": _portable_repo_path(manifest_path),
        "source_activity_manifest_sha256": _sha256(manifest_path),
        "orfs_design_config_sha256": _sha256(design_config),
        "remaining_abstractions": [
            "FakeRAM power uses the Nangate45 proxy Liberty model, not SRAM compiler signoff.",
            "RTL-generated VCD is mapped onto the post-route netlist; annotation coverage is explicit and gated.",
            "Off-cluster value-memory, NoC, and HBM energy are outside this cluster power result.",
        ],
    }


def write_markdown(payload: JsonDict, path: Path) -> None:
    lines = [
        "# Post-route Phase VCD Power",
        "",
        f"- status: `{payload['status']}`",
        f"- promotion_gate_pass: `{payload['promotion_gate_pass']}`",
        f"- clock_period_ns: `{payload['clock_period_ns']}`",
        f"- full_context_cycles: `{payload['full_context_cycles']}`",
        f"- full_context_latency_s: `{payload['full_context_latency_s']}`",
        f"- full_context_energy_j: `{payload['full_context_energy_j']}`",
        "",
        "| phase | measured cycles | full cycles | total W | VCD coverage | macro active pins | energy J | gate |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in payload["phases"]:
        power = row["power"]
        lines.append(
            "| {phase} | {measured_cycles} | {full_context_cycles} | {total_w} | "
            "{coverage:.6f} | {macro_pins} | {energy} | {gate} |".format(
                phase=row["phase"],
                measured_cycles=row["measured_cycles"],
                full_context_cycles=row["full_context_cycles"],
                total_w=power.get("total_w"),
                coverage=row["vcd_annotation_coverage"],
                macro_pins=power.get("macro_trace_active_pin_count", 0),
                energy=row["full_context_energy_j"],
                gate=row["phase_gate_pass"],
            )
        )
    lines.extend(["", "## Remaining Abstractions", ""])
    lines.extend(f"- {item}" for item in payload["remaining_abstractions"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--activity-manifest", type=Path, required=True)
    parser.add_argument("--design-config", type=Path, required=True)
    parser.add_argument("--flow-variant", required=True)
    parser.add_argument("--scope", default="tb/dut")
    parser.add_argument("--min-vcd-coverage", type=float, default=0.05)
    parser.add_argument("--min-vcd-pins", type=int, default=32)
    parser.add_argument("--min-macro-active-coverage", type=float, default=0.01)
    parser.add_argument("--min-macro-active-pins", type=int, default=16)
    parser.add_argument("--timeout-seconds", type=int, default=1800)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--out-md", type=Path)
    args = parser.parse_args()
    if not 0.0 < args.min_vcd_coverage <= 1.0:
        parser.error("--min-vcd-coverage must be in (0, 1]")
    if args.min_vcd_pins <= 0:
        parser.error("--min-vcd-pins must be positive")
    if not 0.0 < args.min_macro_active_coverage <= 1.0:
        parser.error("--min-macro-active-coverage must be in (0, 1]")
    if args.min_macro_active_pins <= 0:
        parser.error("--min-macro-active-pins must be positive")
    manifest = _load_json(args.activity_manifest)
    payload = build_report(
        manifest=manifest,
        manifest_path=args.activity_manifest,
        design_config=args.design_config,
        flow_variant=args.flow_variant,
        scope=args.scope,
        min_vcd_coverage=args.min_vcd_coverage,
        min_vcd_pins=args.min_vcd_pins,
        min_macro_active_coverage=args.min_macro_active_coverage,
        min_macro_active_pins=args.min_macro_active_pins,
        timeout_seconds=args.timeout_seconds,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.out_md:
        write_markdown(payload, args.out_md)
    return 0 if payload["promotion_gate_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
