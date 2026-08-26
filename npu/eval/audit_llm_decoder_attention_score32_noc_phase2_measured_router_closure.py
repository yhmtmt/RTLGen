#!/usr/bin/env python3
"""Conservatively recost the score32 NoC Phase 2 schedule with a measured router primitive."""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any


JsonDict = dict[str, Any]

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_PHASE2_SCHEDULE_JSON = Path(
    "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
    "decoder_attention_score32_noc_phase2_schedule__"
    "l2_decoder_attention_score32_noc_phase2_schedule_llama7b_v1_r1.json"
)
_DEFAULT_PHASE1_ROUTER_PROMOTION_JSON = Path(
    "control_plane/shadow_exports/l1_promotions/l1_segmented_xy_mesh_noc_phase1_v1_r7.json"
)
_EXPECTED_PHASE2_PROFILE = "decoder_attention_score32_noc_phase2_schedule"
_EXPECTED_PHASE2_VERSION = 2
_EXPECTED_PHASE2_ITEM_ID = "l2_decoder_attention_score32_noc_phase2_schedule_llama7b_v1_r1"
_EXPECTED_PHASE1_ITEM_ID = "l1_segmented_xy_mesh_noc_phase1_v1_r7"
_EXPECTED_WAVES = 8
_EXPECTED_TILES = 128
_EXPECTED_ROUTERS = 16
_EXPECTED_ROUTER_PORTS = 5
_EXPECTED_ROUTER_WIDTH_BITS = 256
_EXPECTED_ROUTER_VCS = 4
_EXPECTED_ROUTER_DEPTH = 4


def _load_json(path: Path) -> JsonDict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _portable_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(_REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _as_float(value: Any, label: str) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be a finite number") from exc
    if not math.isfinite(numeric):
        raise ValueError(f"{label} must be a finite number")
    return numeric


def _as_int(value: Any, label: str) -> int:
    numeric = _as_float(value, label)
    if int(numeric) != numeric:
        raise ValueError(f"{label} must be an integer")
    return int(numeric)


def _as_positive_float(value: Any, label: str) -> float:
    numeric = _as_float(value, label)
    if numeric <= 0.0:
        raise ValueError(f"{label} must be positive")
    return numeric


def _require_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise ValueError(f"{label} must be {expected!r}, got {actual!r}")


def _require_fields(payload: JsonDict, fields: list[str], *, label: str) -> None:
    missing = [field for field in fields if field not in payload]
    if missing:
        raise ValueError(f"{label} is missing required quantities: {', '.join(missing)}")


def _parse_item_id(path: Path) -> str:
    stem = path.stem
    if "__" in stem:
        return stem.split("__", 1)[1]
    return stem


def _parse_router_shape(design_hint: str) -> dict[str, int]:
    pattern = re.compile(r"_p(?P<ports>\d+)_w(?P<width>\d+)_vc(?P<vcs>\d+)_d(?P<depth>\d+)")
    match = pattern.search(design_hint)
    if not match:
        raise ValueError(f"unable to parse segmented router shape from {design_hint!r}")
    return {
        "ports": int(match.group("ports")),
        "width_bits": int(match.group("width")),
        "virtual_channels": int(match.group("vcs")),
        "depth": int(match.group("depth")),
    }


def _validate_phase2_schedule(payload: JsonDict, *, source_path: Path) -> dict[str, Any]:
    item_id = _parse_item_id(source_path)
    _require_equal(item_id, _EXPECTED_PHASE2_ITEM_ID, "phase2 item_id")
    _require_equal(payload.get("profile"), _EXPECTED_PHASE2_PROFILE, "phase2 profile")
    _require_equal(payload.get("version"), _EXPECTED_PHASE2_VERSION, "phase2 version")

    source_contract = payload.get("source_contract")
    mapping = payload.get("mapping")
    simulation = payload.get("simulation")
    traffic_quantities = payload.get("traffic_quantities")
    schedule_parameters = payload.get("schedule_parameters")
    if not isinstance(source_contract, dict):
        raise ValueError("phase2 schedule is missing source_contract")
    if not isinstance(mapping, dict):
        raise ValueError("phase2 schedule is missing mapping")
    if not isinstance(simulation, dict):
        raise ValueError("phase2 schedule is missing simulation")
    if not isinstance(traffic_quantities, dict):
        raise ValueError("phase2 schedule is missing traffic_quantities")
    if not isinstance(schedule_parameters, dict):
        raise ValueError("phase2 schedule is missing schedule_parameters")

    _require_equal(source_contract.get("coverage"), "workload_complete", "phase2 workload coverage")
    _require_fields(
        source_contract,
        [
            "active_clusters",
            "cluster_count",
            "declared_tile_waves",
            "simulated_wave_count",
            "compute_clock_ns",
            "noc_clock_ns",
            "compute_layer_time_ns",
        ],
        label="phase2 source_contract",
    )
    _require_fields(
        simulation,
        [
            "cycles_to_drain",
            "drain_time_ns",
            "drain_within_source_compute_layer_envelope",
            "drain_minus_compute_layer_time_ns",
            "scheduled_packet_count",
            "scheduled_flit_count",
            "router_contention_cycles",
            "endpoint_input_stall_cycles_total",
        ],
        label="phase2 simulation",
    )
    _require_fields(
        mapping,
        [
            "cluster_endpoints",
            "root_endpoint",
        ],
        label="phase2 mapping",
    )
    _require_fields(
        traffic_quantities,
        [
            "tile_count",
            "simulated_tiles",
            "shared_tile_payload_bytes",
            "partial_reduction_payload_bytes",
        ],
        label="phase2 traffic_quantities",
    )
    _require_fields(
        schedule_parameters,
        [
            "wave_start_compute_cycles",
            "wave_start_noc_cycles",
            "reduction_release_compute_cycles",
            "reduction_release_noc_cycles",
            "compute_to_noc_clock_ratio",
            "release_conversion",
        ],
        label="phase2 schedule_parameters",
    )
    _require_equal(
        source_contract.get("simulated_wave_count"),
        source_contract.get("declared_tile_waves"),
        "phase2 simulated/declared waves",
    )
    _require_equal(
        traffic_quantities.get("simulated_tiles"),
        traffic_quantities.get("tile_count"),
        "phase2 simulated/declared tile count",
    )
    _require_equal(source_contract.get("declared_tile_waves"), _EXPECTED_WAVES, "phase2 declared waves")
    _require_equal(traffic_quantities.get("tile_count"), _EXPECTED_TILES, "phase2 tile count")
    _require_equal(source_contract.get("cluster_count"), _EXPECTED_ROUTERS, "phase2 router count")
    _require_equal(
        schedule_parameters.get("release_conversion"),
        "ceil(compute_cycles * compute_clock_ns / noc_clock_ns)",
        "phase2 release conversion",
    )

    cluster_endpoints = mapping.get("cluster_endpoints")
    if not isinstance(cluster_endpoints, list) or not all(isinstance(item, int) for item in cluster_endpoints):
        raise ValueError("phase2 cluster_endpoints must be a list of integers")

    root_endpoint = _as_int(mapping.get("root_endpoint"), "phase2 root_endpoint")
    max_endpoint = max(cluster_endpoints + [root_endpoint]) if cluster_endpoints else root_endpoint
    router_component_count = max(
        _as_int(source_contract.get("cluster_count"), "phase2 cluster_count"),
        max_endpoint + 1,
    )
    _require_equal(router_component_count, _EXPECTED_ROUTERS, "phase2 inferred router count")

    noc_clock_ns = _as_positive_float(source_contract.get("noc_clock_ns"), "phase2 noc_clock_ns")
    drain_cycles = _as_int(simulation.get("cycles_to_drain"), "phase2 cycles_to_drain")
    drain_time_ns = _as_positive_float(simulation.get("drain_time_ns"), "phase2 drain_time_ns")
    if not math.isclose(drain_time_ns, drain_cycles * noc_clock_ns, rel_tol=1e-12, abs_tol=1e-9):
        raise ValueError("phase2 drain_time_ns is inconsistent with cycles_to_drain * noc_clock_ns")

    return {
        "item_id": item_id,
        "source_contract": source_contract,
        "mapping": mapping,
        "simulation": simulation,
        "traffic_quantities": traffic_quantities,
        "schedule_parameters": schedule_parameters,
        "router_component_count": router_component_count,
    }


def _proposal_metric(proposal: JsonDict) -> JsonDict:
    metrics_ref = proposal.get("metrics_ref")
    metric_summary = proposal.get("metric_summary")
    if not isinstance(metrics_ref, dict) or not isinstance(metric_summary, dict):
        raise ValueError("phase1 proposal entry must contain metrics_ref and metric_summary")
    metrics_csv = str(metrics_ref.get("metrics_csv") or "")
    design = str(metrics_ref.get("design") or Path(metrics_csv).parent.name or "")
    if not design:
        raise ValueError("phase1 proposal entry is missing design identity")
    return {
        "design": design,
        "metrics_csv": metrics_csv,
        "param_hash": str(metrics_ref.get("param_hash") or ""),
        "tag": str(metrics_ref.get("tag") or ""),
        "result_path": str(metrics_ref.get("result_path") or ""),
        "work_result_json": str(metrics_ref.get("work_result_json") or ""),
        "critical_path_ns": _as_positive_float(metric_summary.get("critical_path_ns"), "phase1 critical_path_ns"),
        "area_um2": _as_positive_float(metric_summary.get("die_area"), "phase1 die_area"),
        "power_mw": _as_positive_float(metric_summary.get("total_power_mw"), "phase1 total_power_mw"),
    }


def _validate_phase1_router_promotion(payload: JsonDict) -> dict[str, Any]:
    _require_equal(payload.get("item_id"), _EXPECTED_PHASE1_ITEM_ID, "phase1 item_id")
    _require_equal(payload.get("task_type"), "l1_sweep", "phase1 task_type")

    evaluation_record = payload.get("evaluation_record")
    proposals = payload.get("proposals")
    if not isinstance(evaluation_record, dict):
        raise ValueError("phase1 router promotion is missing evaluation_record")
    if not isinstance(proposals, list):
        raise ValueError("phase1 router promotion is missing proposals")
    if not bool(evaluation_record.get("physical_metrics_present")):
        raise ValueError("phase1 router promotion must provide physical metrics")
    if evaluation_record.get("timing_feasible") is False:
        raise ValueError("phase1 router promotion is not timing-feasible")

    candidates: list[JsonDict] = []
    for proposal in proposals:
        if not isinstance(proposal, dict):
            continue
        metric = _proposal_metric(proposal)
        if "segmented_xy_router" not in metric["design"] and "segmented_xy_router" not in metric["metrics_csv"]:
            continue
        shape = _parse_router_shape(metric["design"] or metric["metrics_csv"])
        metric.update(shape)
        if (
            metric["ports"] == _EXPECTED_ROUTER_PORTS
            and metric["width_bits"] == _EXPECTED_ROUTER_WIDTH_BITS
            and metric["virtual_channels"] == _EXPECTED_ROUTER_VCS
            and metric["depth"] == _EXPECTED_ROUTER_DEPTH
        ):
            candidates.append(metric)
    if not candidates:
        raise ValueError("phase1 router promotion does not contain the expected p5/w256/vc4/d4 primitive")

    best = min(
        candidates,
        key=lambda item: (item["critical_path_ns"], item["area_um2"], item["power_mw"]),
    )
    return {
        "item_id": str(payload["item_id"]),
        "source_commit": str(payload.get("source_commit") or ""),
        "evaluation_record": evaluation_record,
        "router_metric": best,
    }


def build_report(args: argparse.Namespace) -> JsonDict:
    repo_root = args.repo_root.resolve()
    phase2_schedule_path = repo_root / args.phase2_schedule_json
    phase1_router_path = repo_root / args.phase1_router_promotion_json

    phase2 = _validate_phase2_schedule(_load_json(phase2_schedule_path), source_path=phase2_schedule_path)
    phase1 = _validate_phase1_router_promotion(_load_json(phase1_router_path))

    source_contract = phase2["source_contract"]
    mapping = phase2["mapping"]
    simulation = phase2["simulation"]
    traffic_quantities = phase2["traffic_quantities"]
    schedule_parameters = phase2["schedule_parameters"]
    router_metric = phase1["router_metric"]

    source_noc_clock_ns = _as_positive_float(source_contract["noc_clock_ns"], "phase2 noc_clock_ns")
    measured_router_clock_ns = float(router_metric["critical_path_ns"])
    effective_noc_clock_ns = max(source_noc_clock_ns, measured_router_clock_ns)
    drain_cycles = _as_int(simulation["cycles_to_drain"], "phase2 cycles_to_drain")
    analytic_drain_time_ns = _as_float(simulation["drain_time_ns"], "phase2 drain_time_ns")
    measured_router_drain_time_ns = drain_cycles * effective_noc_clock_ns
    compute_layer_time_ns = _as_float(source_contract["compute_layer_time_ns"], "phase2 compute_layer_time_ns")
    within_envelope = measured_router_drain_time_ns <= compute_layer_time_ns
    envelope_slack_ns = compute_layer_time_ns - measured_router_drain_time_ns
    router_count = int(phase2["router_component_count"])
    router_area_sum_um2 = router_count * float(router_metric["area_um2"])
    router_power_sum_mw = router_count * float(router_metric["power_mw"])

    payload = {
        "version": 1,
        "model": "llama7b_proxy",
        "profile": "decoder_attention_score32_noc_phase2_measured_router_closure",
        "decision": "score32_noc_phase2_measured_router_closure_recorded",
        "source_items": {
            "phase2_schedule": phase2["item_id"],
            "phase1_router_primitive": phase1["item_id"],
        },
        "source_artifacts": {
            "phase2_schedule_json": _portable_path(phase2_schedule_path),
            "phase1_router_promotion_json": _portable_path(phase1_router_path),
        },
        "validated_source_contract": {
            "coverage": str(source_contract["coverage"]),
            "active_clusters": _as_int(source_contract["active_clusters"], "phase2 active_clusters"),
            "cluster_count": _as_int(source_contract["cluster_count"], "phase2 cluster_count"),
            "cluster_endpoints": list(mapping["cluster_endpoints"]),
            "root_endpoint": _as_int(mapping["root_endpoint"], "phase2 root_endpoint"),
            "declared_tile_waves": _as_int(source_contract["declared_tile_waves"], "phase2 declared_tile_waves"),
            "tile_count": _as_int(traffic_quantities["tile_count"], "phase2 tile_count"),
            "shared_tile_payload_bytes": _as_int(
                traffic_quantities["shared_tile_payload_bytes"],
                "phase2 shared_tile_payload_bytes",
            ),
            "partial_reduction_payload_bytes": _as_int(
                traffic_quantities["partial_reduction_payload_bytes"],
                "phase2 partial_reduction_payload_bytes",
            ),
            "scheduled_packet_count": _as_int(simulation["scheduled_packet_count"], "phase2 scheduled_packet_count"),
            "scheduled_flit_count": _as_int(simulation["scheduled_flit_count"], "phase2 scheduled_flit_count"),
            "router_contention_cycles": _as_int(
                simulation["router_contention_cycles"],
                "phase2 router_contention_cycles",
            ),
            "endpoint_input_stall_cycles_total": _as_int(
                simulation["endpoint_input_stall_cycles_total"],
                "phase2 endpoint_input_stall_cycles_total",
            ),
            "compute_clock_ns": _as_float(source_contract["compute_clock_ns"], "phase2 compute_clock_ns"),
            "source_schedule_noc_clock_ns": source_noc_clock_ns,
            "compute_layer_time_ns": compute_layer_time_ns,
            "release_conversion": str(schedule_parameters["release_conversion"]),
        },
        "measured_router_primitive": {
            "design": router_metric["design"],
            "metrics_csv": router_metric["metrics_csv"],
            "param_hash": router_metric["param_hash"],
            "tag": router_metric["tag"],
            "result_path": router_metric["result_path"],
            "work_result_json": router_metric["work_result_json"],
            "ports": router_metric["ports"],
            "width_bits": router_metric["width_bits"],
            "virtual_channels": router_metric["virtual_channels"],
            "depth": router_metric["depth"],
            "critical_path_ns": measured_router_clock_ns,
            "area_um2": float(router_metric["area_um2"]),
            "power_mw": float(router_metric["power_mw"]),
            "evaluation_record": {
                "evaluation_mode": str(phase1["evaluation_record"].get("evaluation_mode") or ""),
                "clock_period_ns": phase1["evaluation_record"].get("clock_period_ns"),
                "timing_slack_ns": phase1["evaluation_record"].get("timing_slack_ns"),
            },
        },
        "conservative_recost": {
            "method": "no_reroute_absolute_cycle_upper_bound",
            "selection_rule": "max(source_schedule_noc_clock_ns, measured_router_critical_path_ns)",
            "source_schedule_noc_clock_ns": source_noc_clock_ns,
            "measured_router_critical_path_ns": measured_router_clock_ns,
            "effective_noc_clock_ns": effective_noc_clock_ns,
            "estimated_mesh_frequency_mhz_lower_bound": 1000.0 / effective_noc_clock_ns,
            "drain_cycles": drain_cycles,
            "analytic_drain_time_ns": analytic_drain_time_ns,
            "no_reroute_upper_bound_drain_time_ns": measured_router_drain_time_ns,
            "added_time_ns_vs_analytic_schedule": measured_router_drain_time_ns - analytic_drain_time_ns,
            "within_source_compute_layer_envelope": within_envelope,
            "source_compute_layer_envelope_slack_ns": envelope_slack_ns,
        },
        "router_component_accounting": {
            "label": "router-only area lower bound and activity-dependent power component estimate; not aggregate placed-mesh PPA",
            "router_count": router_count,
            "single_router_area_um2": float(router_metric["area_um2"]),
            "single_router_power_mw": float(router_metric["power_mw"]),
            "area_um2_lower_bound": router_area_sum_um2,
            "power_mw_component_sum_estimate": router_power_sum_mw,
            "power_bound_status": "not_a_bound_without_workload_matched_router_activity",
            "excluded_effects": [
                "aggregate mesh wiring and repeater power/area",
                "4x4 floorplan congestion and placement interaction",
                "clock-tree growth across the full mesh",
                "endpoint packetizer/descriptors and endpoint SRAM queues",
                "shared SRAM macros and placement adapters",
                "HBM/DRAM service and controller logic",
                "root-finalizer internal compute after root ingress",
            ],
        },
        "closure_diagnosis": {
            "clock_envelope": (
                "measured_router_clock_preserves_source_compute_envelope"
                if within_envelope
                else "measured_router_clock_exceeds_source_compute_envelope"
            ),
            "area_power_scope": "router_area_lower_bound_and_activity_dependent_power_component_estimate",
            "aggregate_mesh_physical_closure": "not_claimed",
        },
        "explicit_assumptions": [
            "The Phase 2 schedule artifact is already the corrected clock-domain v2 report and is treated as workload-complete for this closure step.",
            "The measured router primitive is consumed exactly as a single five-port 256-bit VC4 depth-4 router anchor from Phase 1.",
            "Clock recost is a conservative no-reroute upper bound: absolute cycle indices from the 1 ns schedule are multiplied by the slower of the declared NoC clock and measured single-router critical path.",
            "Area is a router-only lower bound across the explicit 4x4 mesh; power is only a component estimate because the primitive activity assumption is not workload matched.",
            "No linear claim is made that a summed router component total equals a placed 4x4 mesh macro or full cluster fabric PPA.",
        ],
        "remaining_abstractions": [
            "Aggregate 4x4 mesh wiring, placement congestion, and clock-tree effects are still unmeasured and explicitly excluded from the reported router component sum.",
            "Endpoint packetizer/descriptors, endpoint SRAM queues, and source-retention control remain outside this recost result.",
            "Shared SRAM placement/floorplan adaptation remains the explicit NoC-memory closure gap carried from the Phase 2 schedule.",
            "HBM/DRAM service timing and controller implementation remain out of scope.",
            "Root-finalizer internal compute after root ingress remains out of scope; this audit stops at NoC delivery to the root endpoint.",
        ],
        "required_follow_on_evidence": [
            "Rerun release conversion and mesh routing at the measured router clock; do not promote the no-reroute upper bound as exact schedule timing.",
            "Measured aggregate mesh or hierarchy composition evidence that captures full-fabric wiring and congestion.",
            "Endpoint/SRAM placement closure merged with the corrected Phase 2 schedule before any ranking update.",
            "HBM/DRAM and root-finalizer compute evidence for end-to-end closure.",
        ],
    }
    return payload


def write_report(payload: JsonDict, report_path: Path) -> None:
    lines = [
        "# Llama7B Score32 NoC Phase 2 Measured-Router Closure",
        "",
        "## Sources",
        "",
        f"- phase2 schedule: `{payload['source_items']['phase2_schedule']}`",
        f"- phase1 router primitive: `{payload['source_items']['phase1_router_primitive']}`",
        f"- phase2 artifact: `{payload['source_artifacts']['phase2_schedule_json']}`",
        f"- phase1 artifact: `{payload['source_artifacts']['phase1_router_promotion_json']}`",
        "",
        "## Conservative Clock Recost",
        "",
        f"- source schedule NoC clock ns: `{payload['conservative_recost']['source_schedule_noc_clock_ns']}`",
        f"- measured router critical path ns: `{payload['conservative_recost']['measured_router_critical_path_ns']}`",
        f"- effective NoC clock ns: `{payload['conservative_recost']['effective_noc_clock_ns']}`",
        f"- drain cycles: `{payload['conservative_recost']['drain_cycles']}`",
        f"- analytic drain time ns: `{payload['conservative_recost']['analytic_drain_time_ns']}`",
        f"- no-reroute upper-bound drain time ns: `{payload['conservative_recost']['no_reroute_upper_bound_drain_time_ns']}`",
        f"- added drain time ns: `{payload['conservative_recost']['added_time_ns_vs_analytic_schedule']}`",
        f"- within source compute envelope: `{payload['conservative_recost']['within_source_compute_layer_envelope']}`",
        f"- source envelope slack ns: `{payload['conservative_recost']['source_compute_layer_envelope_slack_ns']}`",
        "",
        "## Router Primitive",
        "",
        f"- design: `{payload['measured_router_primitive']['design']}`",
        f"- ports/width/vcs/depth: `{payload['measured_router_primitive']['ports']}` / `{payload['measured_router_primitive']['width_bits']}` / `{payload['measured_router_primitive']['virtual_channels']}` / `{payload['measured_router_primitive']['depth']}`",
        f"- critical path ns: `{payload['measured_router_primitive']['critical_path_ns']}`",
        f"- area um2: `{payload['measured_router_primitive']['area_um2']}`",
        f"- power mW: `{payload['measured_router_primitive']['power_mw']}`",
        "",
        "## Router Component Sum Lower Bound",
        "",
        f"- label: `{payload['router_component_accounting']['label']}`",
        f"- router count: `{payload['router_component_accounting']['router_count']}`",
        f"- lower-bound area um2: `{payload['router_component_accounting']['area_um2_lower_bound']}`",
        f"- activity-dependent power component estimate mW: `{payload['router_component_accounting']['power_mw_component_sum_estimate']}`",
        "",
        "## Remaining Abstractions",
        "",
    ]
    for item in payload["remaining_abstractions"]:
        lines.append(f"- {item}")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--phase2-schedule-json", type=Path, default=_DEFAULT_PHASE2_SCHEDULE_JSON)
    parser.add_argument(
        "--phase1-router-promotion-json",
        type=Path,
        default=_DEFAULT_PHASE1_ROUTER_PROMOTION_JSON,
    )
    parser.add_argument("--json-out", type=Path, required=True)
    parser.add_argument("--report-out", type=Path, required=True)
    args = parser.parse_args()

    payload = build_report(args)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_report(payload, args.report_out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
