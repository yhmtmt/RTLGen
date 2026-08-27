#!/usr/bin/env python3
"""Measure exact Llama7B replay power on hierarchy-matched routed router points."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any

from npu.eval.generate_llm_decoder_attention_score32_noc_router_activity import (
    DEFAULT_SCHEDULE_JSON,
)
from npu.eval.generate_llm_decoder_attention_score32_noc_router_rtl_activity import (
    build_manifest as build_rtl_activity_manifest,
)
from npu.synth.run_postroute_vcd_power import build_report as build_power_report


JsonDict = dict[str, Any]
_MODEL = "llm_decoder_attention_score32_noc_router_postroute_activity_power_v1"
_DESIGN = "noc_segmented_mesh_router_node5_bare"
_TOP = "noc_segmented_mesh_router_node5"
_PLATFORM = "nangate45"
_BASE_FLOW_VARIANT = "router_node5_bare_v1"
_SCOPE = "tb/dut"


def _load(path: Path) -> JsonDict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _positive(value: Any, label: str) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be numeric") from exc
    if not math.isfinite(numeric) or numeric <= 0.0:
        raise ValueError(f"{label} must be finite and positive")
    return numeric


def _portable(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.name


def _validate_config(path: Path) -> JsonDict:
    payload = _load(path)
    if payload.get("top_name") != _TOP:
        raise ValueError(f"bare router top_name must be {_TOP}")
    profile = payload.get("segmented_mesh_router_bare")
    expected = {
        "node": 5,
        "x_coord": 1,
        "y_coord": 1,
        "data_bits": 256,
        "virtual_channels": 4,
        "fifo_depth": 4,
        "ports": 5,
    }
    if not isinstance(profile, dict) or any(profile.get(key) != value for key, value in expected.items()):
        raise ValueError("bare router config does not match the verified node-5 replay hierarchy")
    return payload


def _physical_rows(metrics_csv: Path) -> list[JsonDict]:
    rows: list[JsonDict] = []
    seen_variants: set[str] = set()
    with metrics_csv.open(newline="", encoding="utf-8") as handle:
        for raw in csv.DictReader(handle):
            if raw.get("design") != _DESIGN or raw.get("platform") != _PLATFORM:
                continue
            if raw.get("status") != "ok":
                continue
            params = json.loads(raw.get("params_json") or "{}")
            if params.get("FLOW_VARIANT") != _BASE_FLOW_VARIANT:
                continue
            param_hash = str(raw.get("param_hash") or "").strip()
            effective = str(raw.get("effective_flow_variant") or "").strip()
            if not param_hash or effective != f"{_BASE_FLOW_VARIANT}__{param_hash}":
                raise ValueError("bare router row lacks an isolated effective_flow_variant")
            if effective in seen_variants:
                raise ValueError(f"duplicate bare router effective_flow_variant: {effective}")
            seen_variants.add(effective)
            target_clock_ns = _positive(params.get("CLOCK_PERIOD"), "CLOCK_PERIOD")
            critical_path_ns = _positive(raw.get("critical_path_ns"), "critical_path_ns")
            rows.append(
                {
                    "param_hash": param_hash,
                    "effective_flow_variant": effective,
                    "target_clock_ns": target_clock_ns,
                    "core_utilization_pct": _positive(
                        params.get("CORE_UTILIZATION"), "CORE_UTILIZATION"
                    ),
                    "place_density": _positive(params.get("PLACE_DENSITY"), "PLACE_DENSITY"),
                    "critical_path_ns": critical_path_ns,
                    "timing_feasible": critical_path_ns <= target_clock_ns,
                    "die_area_um2": _positive(raw.get("die_area"), "die_area"),
                    "instance_area_um2": _positive(
                        raw.get("instance_area_um2"), "instance_area_um2"
                    ),
                    "vectorless_power_mw": _positive(raw.get("total_power_mw"), "total_power_mw"),
                }
            )
    if not rows:
        raise ValueError("no complete bare-router physical rows found")
    return sorted(rows, key=lambda row: (row["core_utilization_pct"], row["param_hash"]))


def _measure_point(
    *,
    physical: JsonDict,
    activity_manifest: JsonDict,
    activity_manifest_path: Path,
    orfs_design_config: Path,
) -> JsonDict:
    activity_power = build_power_report(
        manifest=activity_manifest,
        manifest_path=activity_manifest_path,
        design_config=orfs_design_config,
        flow_variant=physical["effective_flow_variant"],
        scope=_SCOPE,
        min_vcd_coverage=0.02,
        min_vcd_pins=8,
        min_sequential_register_activity_coverage=0.95,
        min_macro_active_coverage=0.0,
        min_macro_active_pins=0,
        timeout_seconds=1800,
    )
    if activity_power.get("promotion_gate_pass") is not True:
        raise ValueError(
            f"post-route activity gate failed for {physical['effective_flow_variant']}"
        )
    phases = activity_power.get("phases")
    if not isinstance(phases, list) or len(phases) != 1 or not isinstance(phases[0], dict):
        raise ValueError("router power report must contain exactly one replay phase")
    phase = phases[0]
    for key in (
        "annotation_gate_pass",
        "sequential_register_activity_gate_pass",
        "clock_period_gate_pass",
        "power_numeric_gate_pass",
        "structural_macro_activity_gate_pass",
        "phase_gate_pass",
    ):
        if phase.get(key) is not True:
            raise ValueError(f"router post-route activity gate failed: {key}")
    if int(phase.get("macro_activity_assignment_count", 0)) != 0:
        raise ValueError("bare router replay unexpectedly requires macro activity")
    measured_cycles = int(phase.get("measured_cycles", 0))
    if measured_cycles <= 0 or measured_cycles != int(phase.get("full_context_cycles", -1)):
        raise ValueError("router replay does not cover its full cycle context")
    power = phase.get("power")
    if not isinstance(power, dict):
        raise ValueError("router post-route phase is missing power")
    internal_w = _positive(power.get("internal_w"), "internal_w")
    switching_w = _positive(power.get("switching_w"), "switching_w")
    leakage_w = _positive(power.get("leakage_w"), "leakage_w")
    total_w = _positive(power.get("total_w"), "total_w")
    if not math.isclose(internal_w + switching_w + leakage_w, total_w, rel_tol=1e-6, abs_tol=1e-9):
        raise ValueError("router power components do not sum to total_w")
    annotation_clock_ns = _positive(activity_manifest.get("clock_period_ns"), "clock_period_ns")
    if not math.isclose(
        annotation_clock_ns,
        physical["target_clock_ns"],
        rel_tol=0.0,
        abs_tol=1e-9,
    ):
        raise ValueError("router activity clock does not match the routed target clock")
    promotion_clock_ns = max(annotation_clock_ns, physical["critical_path_ns"])
    dynamic_energy_j = (internal_w + switching_w) * measured_cycles * annotation_clock_ns * 1e-9
    leakage_energy_j = leakage_w * measured_cycles * promotion_clock_ns * 1e-9
    return {
        **physical,
        "activity_status": "activity_backed",
        "measured_cycles": measured_cycles,
        "annotation_clock_ns": annotation_clock_ns,
        "promotion_clock_ns": promotion_clock_ns,
        "power_w": {
            "internal": internal_w,
            "switching": switching_w,
            "dynamic": internal_w + switching_w,
            "leakage": leakage_w,
            "total": total_w,
        },
        "replay_energy_j": {
            "dynamic": dynamic_energy_j,
            "leakage": leakage_energy_j,
            "dynamic_plus_leakage": dynamic_energy_j + leakage_energy_j,
        },
        "annotation": {
            "direct_vcd_coverage": phase.get("direct_vcd_annotation_coverage"),
            "trace_backed_vcd_coverage": phase.get("trace_backed_vcd_annotation_coverage"),
            "direct_pin_gate_pass": phase.get("direct_vcd_annotation_pin_gate_pass"),
            "trace_coverage_gate_pass": phase.get("trace_coverage_gate_pass"),
        },
        "sequential_register_activity": {
            "assignment_count": phase.get("sequential_register_activity_assignment_count"),
            "coverage": phase.get("sequential_register_activity_coverage"),
            "matched_count": phase.get("sequential_register_activity_matched_count"),
            "applied_count": phase.get("sequential_register_activity_applied_count"),
        },
    }


def build_report(
    *,
    repo_root: Path,
    config: Path,
    metrics_csv: Path,
    schedule_json: Path,
    orfs_design_config: Path,
    activity_dir: Path,
    timeout_seconds: int,
) -> JsonDict:
    _validate_config(config)
    physical_rows = _physical_rows(metrics_csv)
    target_clocks = {float(row["target_clock_ns"]) for row in physical_rows}
    if len(target_clocks) != 1:
        raise ValueError(
            "bare-router activity audit currently requires one routed target clock; "
            "split mixed-clock rows into separate activity manifests"
        )
    activity_clock_ns = next(iter(target_clocks))
    activity_dir.mkdir(parents=True, exist_ok=True)
    activity_manifest = build_rtl_activity_manifest(
        repo_root=repo_root,
        schedule_json=schedule_json,
        node=5,
        out_dir=activity_dir,
        timeout_seconds=timeout_seconds,
        clock_period_ns=activity_clock_ns,
    )
    rtl = activity_manifest.get("rtl_activity")
    if not isinstance(rtl, dict) or rtl.get("equivalence_status") != "pass":
        raise ValueError("router RTL replay equivalence did not pass")
    if "all cycle in_ready values" not in str(rtl.get("equivalence_scope") or ""):
        raise ValueError("router RTL replay equivalence scope is incomplete")
    phases = activity_manifest.get("phases")
    if not isinstance(phases, list) or len(phases) != 1:
        raise ValueError("router activity manifest must contain one full replay phase")
    activity_manifest_path = activity_dir / "router_node5_rtl_activity_manifest.json"
    activity_manifest_path.write_text(
        json.dumps(activity_manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    measurements = [
        _measure_point(
            physical=row,
            activity_manifest=activity_manifest,
            activity_manifest_path=activity_manifest_path,
            orfs_design_config=orfs_design_config,
        )
        for row in physical_rows
    ]
    feasible = [row for row in measurements if row["timing_feasible"]]
    if not feasible:
        raise ValueError("no timing-feasible bare-router point remains after activity measurement")
    best = min(
        feasible,
        key=lambda row: (
            row["replay_energy_j"]["dynamic_plus_leakage"],
            row["die_area_um2"],
            row["critical_path_ns"],
        ),
    )
    return {
        "version": 1,
        "model": _MODEL,
        "decision": "hierarchy_matched_router_postroute_activity_recorded",
        "promotion_gate_pass": True,
        "scope": {
            "included": "one exact node-5 router, all FIFO/control/data state, and full Llama7B replay",
            "excluded": [
                "inter-router links and aggregate mesh clock tree",
                "packet endpoints and SRAM macros",
                "HBM/DRAM controller and PHY",
            ],
        },
        "inputs": {
            "config": _portable(config, repo_root),
            "metrics_csv": _portable(metrics_csv, repo_root),
            "schedule_json": _portable(schedule_json, repo_root),
            "orfs_design_config": _portable(orfs_design_config, repo_root),
            "activity_dir": activity_dir.name,
        },
        "rtl_equivalence": {
            "status": rtl["equivalence_status"],
            "scope": rtl["equivalence_scope"],
            "forwarded_event_count": rtl["forwarded_event_count"],
            "forwarded_event_sha256": rtl["forwarded_event_sha256"],
            "vcd_sha256": rtl["vcd_sha256"],
            "rtl_summary": rtl["rtl_summary"],
            "clock_contract": activity_manifest["clock_contract"],
        },
        "measurement_count": len(measurements),
        "measurements": measurements,
        "best": best,
        "next_step": (
            "Substitute this intrinsic router replay energy into the Llama7B recost, then replace "
            "remaining link and mesh-clock estimates with the routed aggregate/composed mesh measurement."
        ),
    }


def _write_markdown(path: Path, payload: JsonDict) -> None:
    lines = [
        "# Node-5 Router Post-Route Activity Power",
        "",
        f"- promotion gate: `{payload['promotion_gate_pass']}`",
        f"- measured physical points: `{payload['measurement_count']}`",
        f"- RTL equivalence: `{payload['rtl_equivalence']['status']}`",
        "",
        "| util (%) | target (ns) | path (ns) | feasible | die (um2) | instance (um2) | dynamic (W) | leakage (W) | replay energy (J) |",
        "|---:|---:|---:|:---:|---:|---:|---:|---:|---:|",
    ]
    for row in payload["measurements"]:
        lines.append(
            "| {core_utilization_pct:g} | {target_clock_ns:g} | {critical_path_ns:.6g} | "
            "{timing_feasible} | {die_area_um2:.6g} | {instance_area_um2:.6g} | "
            "{dynamic:.6g} | {leakage:.6g} | {energy:.6g} |".format(
                **row,
                dynamic=row["power_w"]["dynamic"],
                leakage=row["power_w"]["leakage"],
                energy=row["replay_energy_j"]["dynamic_plus_leakage"],
            )
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--metrics-csv", type=Path, required=True)
    parser.add_argument("--schedule-json", type=Path, default=DEFAULT_SCHEDULE_JSON)
    parser.add_argument("--orfs-design-config", type=Path, required=True)
    parser.add_argument("--activity-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    parser.add_argument("--timeout-seconds", type=int, default=1800)
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    payload = build_report(
        repo_root=repo_root,
        config=args.config,
        metrics_csv=args.metrics_csv,
        schedule_json=args.schedule_json,
        orfs_design_config=args.orfs_design_config,
        activity_dir=args.activity_dir,
        timeout_seconds=args.timeout_seconds,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_markdown(args.out_md, payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
