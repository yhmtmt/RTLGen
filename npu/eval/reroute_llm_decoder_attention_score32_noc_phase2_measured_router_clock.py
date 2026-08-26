#!/usr/bin/env python3
"""Rerun the complete score32 mesh schedule at measured router clock bounds."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from npu.eval import measure_llm_decoder_attention_score32_noc_phase2_schedule as phase2_schedule  # noqa: E402
from npu.eval.audit_llm_decoder_attention_score32_noc_phase2_measured_router_closure import (  # noqa: E402
    _load_json,
    _validate_phase1_router_promotion,
    _validate_phase2_schedule,
)

JsonDict = dict[str, Any]

DEFAULT_BASELINE_SCHEDULE = Path(
    "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
    "decoder_attention_score32_noc_phase2_schedule__"
    "l2_decoder_attention_score32_noc_phase2_schedule_llama7b_v1_r1.json"
)
DEFAULT_ROUTER_PROMOTION = Path(
    "control_plane/shadow_exports/l1_promotions/l1_segmented_xy_mesh_noc_phase1_v1_r7.json"
)


def _schedule_args(args: argparse.Namespace, *, noc_clock_ns: float) -> argparse.Namespace:
    return argparse.Namespace(
        repo_root=args.repo_root,
        source_json=args.source_json,
        measured_l1_costs=args.measured_l1_costs,
        out=args.out,
        report=args.report,
        wave_limit=None,
        packet_payload_bytes=256,
        cluster_endpoints=None,
        root_endpoint=15,
        shared_vc=0,
        reduction_vc=1,
        compute_clock_ns=None,
        noc_clock_ns=noc_clock_ns,
        max_cycles=args.max_cycles,
    )


def _compact_schedule(
    payload: JsonDict,
    *,
    expected_wave_count: int = 8,
    expected_tile_count: int = 128,
) -> JsonDict:
    if payload.get("version") != 2 or payload.get("profile") != "decoder_attention_score32_noc_phase2_schedule":
        raise ValueError("rerouted schedule must preserve the Phase 2 v2 profile")
    source = payload.get("source_contract")
    traffic = payload.get("traffic_quantities")
    simulation = payload.get("simulation")
    parameters = payload.get("schedule_parameters")
    if not all(isinstance(item, dict) for item in (source, traffic, simulation, parameters)):
        raise ValueError("rerouted schedule is missing required sections")
    if source.get("coverage") != "workload_complete":
        raise ValueError("rerouted schedule must remain workload_complete")
    if expected_wave_count <= 0 or expected_tile_count <= 0:
        raise ValueError("expected workload dimensions must be positive")
    if (
        source.get("declared_tile_waves") != expected_wave_count
        or source.get("simulated_wave_count") != expected_wave_count
    ):
        raise ValueError(
            f"rerouted schedule must cover exactly {expected_wave_count} waves"
        )
    if (
        traffic.get("tile_count") != expected_tile_count
        or traffic.get("simulated_tiles") != expected_tile_count
    ):
        raise ValueError(
            f"rerouted schedule must cover exactly {expected_tile_count} tiles"
        )
    if simulation.get("scheduled_flit_count") != simulation.get("delivered_flit_count"):
        raise ValueError("rerouted schedule must deliver every scheduled flit")
    return {
        "noc_clock_ns": source["noc_clock_ns"],
        "compute_clock_ns": source["compute_clock_ns"],
        "compute_layer_time_ns": source["compute_layer_time_ns"],
        "cycles_to_drain": simulation["cycles_to_drain"],
        "drain_time_ns": simulation["drain_time_ns"],
        "drain_within_source_compute_layer_envelope": simulation[
            "drain_within_source_compute_layer_envelope"
        ],
        "drain_minus_compute_layer_time_ns": simulation["drain_minus_compute_layer_time_ns"],
        "scheduled_packet_count": simulation["scheduled_packet_count"],
        "scheduled_flit_count": simulation["scheduled_flit_count"],
        "delivered_flit_count": simulation["delivered_flit_count"],
        "router_contention_cycles": simulation["router_contention_cycles"],
        "endpoint_input_stall_cycles_total": simulation["endpoint_input_stall_cycles_total"],
        "wave_start_noc_cycles": parameters["wave_start_noc_cycles"],
        "reduction_release_noc_cycles": parameters["reduction_release_noc_cycles"],
        "release_conversion": parameters["release_conversion"],
    }


def build_report(args: argparse.Namespace) -> JsonDict:
    repo_root = args.repo_root.resolve()
    baseline_path = repo_root / args.baseline_schedule_json
    router_path = repo_root / args.router_promotion_json
    baseline_payload = _load_json(baseline_path)
    baseline = _validate_phase2_schedule(baseline_payload, source_path=baseline_path)
    router = _validate_phase1_router_promotion(_load_json(router_path))

    source_clock_ns = float(baseline["source_contract"]["noc_clock_ns"])
    measured_clock_ns = float(router["router_metric"]["critical_path_ns"])
    conservative_clock_ns = max(source_clock_ns, measured_clock_ns)

    requested_cases = [
        ("primitive_critical_path_diagnostic", measured_clock_ns),
        ("conservative_no_faster_than_source", conservative_clock_ns),
    ]
    schedules_by_clock: dict[float, JsonDict] = {}
    cases: list[JsonDict] = []
    baseline_drain_ns = float(baseline["simulation"]["drain_time_ns"])
    for case_name, clock_ns in requested_cases:
        if clock_ns not in schedules_by_clock:
            schedules_by_clock[clock_ns] = _compact_schedule(
                phase2_schedule.build_report(_schedule_args(args, noc_clock_ns=clock_ns))
            )
        schedule = schedules_by_clock[clock_ns]
        cases.append(
            {
                "case": case_name,
                "promotion_status": (
                    "diagnostic_primitive_clock_not_aggregate_mesh_closure"
                    if case_name == "primitive_critical_path_diagnostic" and clock_ns < source_clock_ns
                    else "conservative_schedule_bound"
                ),
                "schedule": schedule,
                "drain_time_delta_ns_vs_source_1ns_schedule": float(schedule["drain_time_ns"])
                - baseline_drain_ns,
            }
        )

    return {
        "version": 1,
        "model": "llama7b_proxy",
        "profile": "decoder_attention_score32_noc_phase2_measured_router_clock_reroute",
        "decision": "score32_noc_phase2_measured_router_clock_reroute_recorded",
        "source_items": {
            "baseline_schedule": baseline["item_id"],
            "router_primitive": router["item_id"],
        },
        "clock_contract": {
            "source_schedule_noc_clock_ns": source_clock_ns,
            "measured_router_critical_path_ns": measured_clock_ns,
            "conservative_effective_clock_ns": conservative_clock_ns,
            "release_conversion_and_mesh_routing_rerun": True,
            "absolute_1ns_cycle_timeline_reused": False,
        },
        "cases": cases,
        "area_power_scope": {
            "aggregate_mesh_physical_closure": "not_claimed",
            "router_power_activity_match": "not_measured",
        },
        "remaining_abstractions": [
            "Aggregate 4x4 mesh links, repeaters, placement congestion, and clock-tree effects remain unmeasured.",
            "Router dynamic power remains activity dependent until workload-matched switching evidence is measured.",
            "Endpoint packetizers, descriptor/source-retention control, and endpoint/shared SRAM placement remain unmeasured.",
            "HBM/DRAM timing, controller implementation, and vendor current signoff remain external envelopes.",
            "Root-finalizer internal compute after root ingress remains outside this routing result.",
        ],
    }


def write_report(payload: JsonDict, path: Path) -> None:
    lines = [
        "# Llama7B Score32 Measured-Router-Clock Reroute",
        "",
        f"- source NoC clock ns: `{payload['clock_contract']['source_schedule_noc_clock_ns']}`",
        f"- measured router critical path ns: `{payload['clock_contract']['measured_router_critical_path_ns']}`",
        f"- conservative effective clock ns: `{payload['clock_contract']['conservative_effective_clock_ns']}`",
        "- release conversion and mesh routing rerun: `true`",
        "",
        "## Cases",
        "",
    ]
    for case in payload["cases"]:
        schedule = case["schedule"]
        lines.extend(
            [
                f"### {case['case']}",
                "",
                f"- promotion status: `{case['promotion_status']}`",
                f"- NoC clock ns: `{schedule['noc_clock_ns']}`",
                f"- drain cycles: `{schedule['cycles_to_drain']}`",
                f"- drain time ns: `{schedule['drain_time_ns']}`",
                f"- within compute envelope: `{schedule['drain_within_source_compute_layer_envelope']}`",
                "",
            ]
        )
    lines.extend(["## Remaining Abstractions", ""])
    lines.extend(f"- {item}" for item in payload["remaining_abstractions"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--source-json", type=Path, default=phase2_schedule.DEFAULT_SOURCE_JSON)
    parser.add_argument("--measured-l1-costs", type=Path, default=phase2_schedule.DEFAULT_MEASURED_L1_COSTS)
    parser.add_argument("--baseline-schedule-json", type=Path, default=DEFAULT_BASELINE_SCHEDULE)
    parser.add_argument("--router-promotion-json", type=Path, default=DEFAULT_ROUTER_PROMOTION)
    parser.add_argument("--max-cycles", type=int, default=1000000)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    payload = build_report(args)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_report(payload, args.report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
