#!/usr/bin/env python3
"""Measure routed bare-router power for exact VC0/VC1 Llama7B traffic."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from npu.eval.audit_llm_decoder_attention_score32_noc_router_postroute_activity_power import (
    _physical_rows,
    _portable,
    _positive,
    _validate_config,
)
from npu.eval.generate_llm_decoder_attention_score32_noc_exact_router_rtl_activity import (
    build_manifest as build_exact_activity_manifest,
)
from npu.synth.run_postroute_vcd_power import build_report as build_power_report

JsonDict = dict[str, Any]
_MODEL = "llm_decoder_attention_score32_noc_exact_router_postroute_activity_power_v2"
_EXPECTED_PHASES = (
    "shared_vc0_full_context_service",
    "reduction_vc1_group_0",
    "reduction_vc1_group_1",
    "reduction_vc1_group_2",
    "reduction_vc1_group_3",
)
_EXPECTED_PHASE_COUNTS = {
    "shared_vc0_full_context_service": (7_616, 60_928, None),
    "reduction_vc1_group_0": (315, 2_505, 0),
    "reduction_vc1_group_1": (315, 2_505, 1),
    "reduction_vc1_group_2": (315, 2_505, 2),
    "reduction_vc1_group_3": (315, 2_505, 3),
}
_SCOPE = "tb/dut"


def _phase_energy(
    phase: JsonDict,
    *,
    annotation_clock_ns: float,
    promotion_clock_ns: float,
) -> JsonDict:
    for gate in (
        "annotation_gate_pass",
        "sequential_register_activity_gate_pass",
        "clock_period_gate_pass",
        "power_numeric_gate_pass",
        "structural_macro_activity_gate_pass",
        "phase_gate_pass",
    ):
        if phase.get(gate) is not True:
            raise ValueError(f"exact router post-route phase failed {gate}: {phase.get('phase')}")
    if int(phase.get("macro_activity_assignment_count", 0)) != 0:
        raise ValueError("bare router exact replay unexpectedly requires macro activity")
    cycles = int(phase.get("full_context_cycles", 0))
    if cycles <= 0 or cycles != int(phase.get("measured_cycles", -1)):
        raise ValueError("exact router activity phase lacks complete cycle coverage")
    phase_name = str(phase.get("phase") or "")
    expected_packets, expected_flits, expected_group = _EXPECTED_PHASE_COUNTS[phase_name]
    packet_count = int(phase.get("packet_count", -1))
    flit_count = int(phase.get("flit_count", -1))
    if (
        (packet_count, flit_count) != (expected_packets, expected_flits)
        or phase.get("group") != expected_group
    ):
        raise ValueError(f"exact router activity phase count mismatch: {phase_name}")
    power = phase.get("power")
    if not isinstance(power, dict):
        raise ValueError("exact router activity phase lacks power data")
    internal_w = _positive(power.get("internal_w"), "internal_w")
    switching_w = _positive(power.get("switching_w"), "switching_w")
    leakage_w = _positive(power.get("leakage_w"), "leakage_w")
    total_w = _positive(power.get("total_w"), "total_w")
    if not math.isclose(
        internal_w + switching_w + leakage_w,
        total_w,
        rel_tol=1e-6,
        abs_tol=1e-9,
    ):
        raise ValueError("exact router phase power components do not sum")
    dynamic_j = (internal_w + switching_w) * cycles * annotation_clock_ns * 1e-9
    leakage_j = leakage_w * cycles * promotion_clock_ns * 1e-9
    return {
        "phase": phase["phase"],
        "transport_class": phase.get("transport_class"),
        "group": phase.get("group"),
        "cycles": cycles,
        "packet_count": packet_count,
        "flit_count": flit_count,
        "power_w": {
            "internal": internal_w,
            "switching": switching_w,
            "dynamic": internal_w + switching_w,
            "leakage": leakage_w,
            "total": total_w,
        },
        "energy_j": {
            "dynamic": dynamic_j,
            "leakage": leakage_j,
            "dynamic_plus_leakage": dynamic_j + leakage_j,
        },
        "annotation": {
            "direct_vcd_coverage": phase.get("direct_vcd_annotation_coverage"),
            "trace_backed_vcd_coverage": phase.get(
                "trace_backed_vcd_annotation_coverage"
            ),
            "sequential_register_coverage": phase.get(
                "sequential_register_activity_coverage"
            ),
        },
    }


def _measure_point(
    *,
    physical: JsonDict,
    activity_manifest: JsonDict,
    activity_manifest_path: Path,
    orfs_design_config: Path,
    timeout_seconds: int,
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
        timeout_seconds=timeout_seconds,
    )
    if activity_power.get("promotion_gate_pass") is not True:
        raise ValueError("exact router post-route activity gate failed")
    raw_phases = activity_power.get("phases")
    if not isinstance(raw_phases, list):
        raise ValueError("exact router power report lacks phases")
    if tuple(row.get("phase") for row in raw_phases if isinstance(row, dict)) != _EXPECTED_PHASES:
        raise ValueError("exact router power report does not contain the five required phases")
    annotation_clock_ns = _positive(activity_manifest.get("clock_period_ns"), "clock_period_ns")
    if not math.isclose(
        annotation_clock_ns,
        physical["target_clock_ns"],
        rel_tol=0.0,
        abs_tol=1e-9,
    ):
        raise ValueError("exact router activity clock differs from routed target clock")
    promotion_clock_ns = max(annotation_clock_ns, physical["critical_path_ns"])
    phases = [
        _phase_energy(
            row,
            annotation_clock_ns=annotation_clock_ns,
            promotion_clock_ns=promotion_clock_ns,
        )
        for row in raw_phases
    ]
    dynamic_j = sum(row["energy_j"]["dynamic"] for row in phases)
    leakage_j = sum(row["energy_j"]["leakage"] for row in phases)
    return {
        **physical,
        "activity_status": "exact_activity_backed",
        "annotation_clock_ns": annotation_clock_ns,
        "promotion_clock_ns": promotion_clock_ns,
        "phase_count": len(phases),
        "total_cycles": sum(row["cycles"] for row in phases),
        "total_packets": sum(row["packet_count"] for row in phases),
        "total_flits": sum(row["flit_count"] for row in phases),
        "phases": phases,
        "exact_transport_energy_j": {
            "dynamic": dynamic_j,
            "leakage": leakage_j,
            "dynamic_plus_leakage": dynamic_j + leakage_j,
        },
    }


def build_report(
    *,
    repo_root: Path,
    config: Path,
    metrics_csv: Path,
    orfs_design_config: Path,
    activity_dir: Path,
    timeout_seconds: int,
) -> JsonDict:
    _validate_config(config)
    physical_rows = _physical_rows(metrics_csv)
    clocks = {float(row["target_clock_ns"]) for row in physical_rows}
    if len(clocks) != 1:
        raise ValueError("exact router activity requires one routed target clock")
    activity_clock_ns = next(iter(clocks))
    activity_dir.mkdir(parents=True, exist_ok=True)
    activity_manifest = build_exact_activity_manifest(
        repo_root=repo_root,
        node=5,
        out_dir=activity_dir,
        timeout_seconds=timeout_seconds,
        clock_period_ns=activity_clock_ns,
    )
    contract = activity_manifest.get("source_contract")
    if not isinstance(contract, dict) or contract.get("total_flits") != 70_948:
        raise ValueError("exact router activity does not cover the 70,948-flit contract")
    if activity_manifest.get("equivalence", {}).get("status") != "pass":
        raise ValueError("exact router multi-phase RTL equivalence did not pass")
    activity_manifest_path = activity_dir / "router_node5_exact_activity_manifest.json"
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
            timeout_seconds=timeout_seconds,
        )
        for row in physical_rows
    ]
    if any(row["total_flits"] != 70_948 for row in measurements):
        raise ValueError("routed measurements do not retain the exact 70,948-flit contract")
    feasible = [row for row in measurements if row["timing_feasible"]]
    if not feasible:
        raise ValueError("no timing-feasible bare-router point remains")
    best = min(
        feasible,
        key=lambda row: (
            row["exact_transport_energy_j"]["dynamic_plus_leakage"],
            row["die_area_um2"],
            row["critical_path_ns"],
        ),
    )
    return {
        "version": 2,
        "model": _MODEL,
        "decision": "exact_vc0_vc1_router_postroute_activity_recorded",
        "promotion_gate_pass": True,
        "invalidated_predecessor": {
            "item_id": "l2_decoder_attention_score32_noc_router_postroute_activity_power_llama7b_v1",
            "reason": "depends_on_retracted_wrong_precision_and_release_contract",
        },
        "scope": {
            "included": "node-5 router activity for exact VC0 shared contexts and four exact stats-once VC1 groups",
            "excluded": [
                "simultaneous shared-mesh VC0/VC1 arbitration",
                "aggregate links and mesh clock tree",
                "endpoint/SRAM macro power",
                "HBM/DRAM control and PHY",
            ],
        },
        "inputs": {
            "config": _portable(config, repo_root),
            "metrics_csv": _portable(metrics_csv, repo_root),
            "orfs_design_config": _portable(orfs_design_config, repo_root),
            "activity_manifest": activity_manifest_path.name,
        },
        "exact_contract": contract,
        "measurement_count": len(measurements),
        "measurements": measurements,
        "best": best,
        "next_step": "Measure the same exact phases on the routed direct 4x4 mesh, then compose endpoint/SRAM activity and recost the precision-backed Llama7B frontier.",
    }


def _write_markdown(path: Path, payload: JsonDict) -> None:
    lines = [
        "# Exact VC0/VC1 Router Post-Route Activity Power",
        "",
        f"- promotion gate: `{payload['promotion_gate_pass']}`",
        f"- measured physical points: `{payload['measurement_count']}`",
        f"- exact transport flits: `{payload['exact_contract']['total_flits']}`",
        "",
        "| util (%) | target (ns) | path (ns) | feasible | instance (um2) | cycles | energy (J) |",
        "|---:|---:|---:|:---:|---:|---:|---:|",
    ]
    for row in payload["measurements"]:
        lines.append(
            "| {core_utilization_pct:g} | {target_clock_ns:g} | {critical_path_ns:.6g} | "
            "{timing_feasible} | {instance_area_um2:.6g} | {total_cycles} | {energy:.6g} |".format(
                **row,
                energy=row["exact_transport_energy_j"]["dynamic_plus_leakage"],
            )
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--metrics-csv", type=Path, required=True)
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
        orfs_design_config=args.orfs_design_config,
        activity_dir=args.activity_dir,
        timeout_seconds=args.timeout_seconds,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_markdown(args.out_md, payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
