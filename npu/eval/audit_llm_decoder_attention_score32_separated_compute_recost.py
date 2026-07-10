#!/usr/bin/env python3
"""Recost a dense-int8 producer with shared score32 attention logic."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

JsonDict = dict[str, Any]


def _load_json(path: Path) -> JsonDict:
    return json.loads(path.read_text(encoding="utf-8"))


def _as_dict(value: Any) -> JsonDict:
    return dict(value) if isinstance(value, dict) else {}


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _require_positive(row: JsonDict, key: str, source: str) -> float:
    value = _as_float(row.get(key))
    if value <= 0.0:
        raise ValueError(f"{source} must provide positive {key}")
    return value


def _quality_evidence(payload: JsonDict) -> JsonDict:
    decision = _as_dict(payload.get("decision"))
    best = _as_dict(payload.get("best_candidate"))
    status = str(decision.get("status") or best.get("decision_status") or "unknown")
    return {
        "status": status,
        "candidate_id": best.get("candidate_id"),
        "teacher_forced_nll_delta_mean": best.get("teacher_forced_nll_delta_mean"),
        "free_running_match_rate": best.get("free_running_match_rate"),
        "candidate_probability_assigned_to_reference_token_mean": best.get(
            "candidate_probability_assigned_to_reference_token_mean"
        ),
        "quality_backed": status.endswith("_pass"),
    }


def _controller_metrics(payload: JsonDict, channel_count: int = 4) -> JsonDict:
    marker = f"_c{channel_count}/"
    fallback: JsonDict | None = None
    for proposal in payload.get("proposals", []):
        proposal = _as_dict(proposal)
        metrics_ref = _as_dict(proposal.get("metrics_ref"))
        summary = _as_dict(proposal.get("metric_summary"))
        if str(metrics_ref.get("status") or "") != "ok" or not summary:
            continue
        row = {
            "critical_path_ns": _require_positive(summary, "critical_path_ns", "controller PPA"),
            "area_um2": _require_positive(summary, "die_area", "controller PPA"),
            "power_mw": _require_positive(summary, "total_power_mw", "controller PPA"),
            "metrics_csv": metrics_ref.get("metrics_csv"),
            "item_id": payload.get("item_id"),
        }
        fallback = fallback or row
        if marker in str(metrics_ref.get("metrics_csv") or ""):
            return row
    if fallback is not None:
        return fallback
    metrics = _as_dict(_as_dict(payload.get("trial_summary")).get("metrics"))
    if not metrics:
        raise ValueError("controller PPA contains no accepted physical metrics")
    return {
        "critical_path_ns": _require_positive(_as_dict(metrics.get("critical_path_ns")), "best", "controller PPA"),
        "area_um2": _require_positive(_as_dict(metrics.get("die_area")), "best", "controller PPA"),
        "power_mw": _require_positive(_as_dict(metrics.get("total_power_mw")), "best", "controller PPA"),
        "metrics_csv": None,
        "item_id": payload.get("item_id"),
    }


def _frontier_row(payload: JsonDict, family: str) -> JsonDict:
    for row in payload.get("rows", []):
        if isinstance(row, dict) and str(row.get("family")) == family:
            return dict(row)
    raise ValueError(f"quality-aware frontier is missing family {family}")


def _ratio(numerator: float, denominator: float) -> float:
    return round(numerator / max(1.0e-12, denominator), 9)


def build_report(args: argparse.Namespace) -> JsonDict:
    energy_payload = _load_json(args.mixed_int8_energy_json)
    command_payload = _load_json(args.score32_measured_command_control_json)
    quality_payload = _load_json(args.score32_quality_json)
    controller_payload = _load_json(args.hbm_controller_ppa_json)
    frontier_payload = _load_json(args.quality_aware_frontier_json)

    dense = _as_dict(energy_payload.get("best"))
    command = _as_dict(command_payload.get("best_requested"))
    quality = _quality_evidence(quality_payload)
    controller = _controller_metrics(controller_payload, channel_count=4)
    score32_reference = _frontier_row(frontier_payload, "score32_exp_lut_div")
    fp16_reference = _frontier_row(frontier_payload, "measured_exact_fp16_gqa8_kv8")

    schedule_clock_ns = _require_positive(command, "clock_ns", "score32 command-control")
    latency_us = _require_positive(dense, "latency_us", "mixed-int8 energy")
    dense_area_um2 = _require_positive(dense, "compute_area_um2", "mixed-int8 energy")
    dense_clock_ns = _require_positive(dense, "substituted_block_clock_ns", "mixed-int8 energy")
    dense_power_mw = _require_positive(dense, "substituted_compute_power_mw_only", "mixed-int8 energy")
    shared_area_um2 = _require_positive(command, "selected_l1_overhead_area_um2", "score32 command-control")
    shared_clock_ns = _require_positive(command, "measured_l1_overhead_clock_ns", "score32 command-control")
    shared_power_mw = _require_positive(command, "measured_l1_overhead_power_mw", "score32 command-control")
    dispatch_area_um2 = _require_positive(
        command, "measured_command_dispatch_control_area_um2", "score32 command-control"
    )
    dispatch_clock_ns = _require_positive(
        command, "measured_command_dispatch_control_clock_ns", "score32 command-control"
    )
    dispatch_power_mw = _require_positive(
        command, "measured_command_dispatch_control_power_mw", "score32 command-control"
    )

    components = [
        {
            "component": "dense_int8_gemm_fabric",
            "area_um2": dense_area_um2,
            "power_mw": dense_power_mw,
            "critical_path_ns": dense_clock_ns,
            "clock_ok": dense_clock_ns <= schedule_clock_ns,
            "source": dense.get("substituted_compute_metrics_csv"),
            "replica_count": dense.get("substituted_compute_replica_count"),
        },
        {
            "component": "shared_score32_vector_softmax_overhead",
            "area_um2": shared_area_um2,
            "power_mw": shared_power_mw,
            "critical_path_ns": shared_clock_ns,
            "clock_ok": shared_clock_ns <= schedule_clock_ns,
            "source": command.get("measured_softmax_weight_metrics_csv"),
            "cluster_count": command.get("cluster_count"),
        },
        {
            "component": "command_dispatch_control",
            "area_um2": dispatch_area_um2,
            "power_mw": dispatch_power_mw,
            "critical_path_ns": dispatch_clock_ns,
            "clock_ok": dispatch_clock_ns <= schedule_clock_ns,
            "source": command.get("measured_command_dispatch_control_metrics_csv"),
        },
        {
            "component": "hbm_replay_controller_c4",
            "area_um2": controller["area_um2"],
            "power_mw": controller["power_mw"],
            "critical_path_ns": controller["critical_path_ns"],
            "clock_ok": controller["critical_path_ns"] <= schedule_clock_ns,
            "source": controller.get("metrics_csv"),
        },
    ]
    timing_ok = all(bool(row["clock_ok"]) for row in components)
    logic_area_mm2 = round(sum(_as_float(row["area_um2"]) for row in components) / 1.0e6, 12)
    active_power_mw = round(sum(_as_float(row["power_mw"]) for row in components), 12)
    compute_control_energy_mj = round(active_power_mw * latency_us * 1.0e-6, 12)

    energy_components = _as_dict(dense.get("energy_components"))
    inherited = {}
    for name in ("hbm", "noc", "sram"):
        component = _as_dict(energy_components.get(name))
        inherited[name] = _require_positive(component, "energy_mj", f"mixed-int8 {name} energy")
    total_energy_mj = round(compute_control_energy_mj + sum(inherited.values()), 12)
    token_throughput_per_s = round(1_000_000.0 / latency_us, 12)

    remaining_abstractions = [
        "producer-to-score32 ready/valid queues and backpressure are not yet embodied in one composed RTL block",
        "the inherited dense-int8 schedule has not yet been replayed against the separated score32 consumer",
        "full QK-to-softmax-to-V RTL/perf-sim tensor-hash equivalence is pending for the separated composition",
        "NoC and SRAM energy remain profile-scaled rather than gate-level toggle power",
        "HBM energy is source-backed aggregate energy, not vendor current signoff",
    ]
    promotable = False
    decision = (
        "score32_separated_compute_measured_component_frontier_requires_rtl"
        if quality["quality_backed"] and timing_ok
        else "score32_separated_compute_recost_not_ready"
    )
    candidate = {
        "candidate_id": "score32_separated_dense_int8_shared_vector_softmax_c16_hbm_c4",
        "precision_profile": "q8_k8_v8_a32_s32_w16_exp_lut_div_b20_int8_compute",
        "latency_us": latency_us,
        "token_throughput_per_s": token_throughput_per_s,
        "energy_mj_per_token": total_energy_mj,
        "compute_control_energy_mj_per_token": compute_control_energy_mj,
        "hbm_energy_mj_per_token": inherited["hbm"],
        "noc_energy_mj_per_token": inherited["noc"],
        "sram_energy_mj_per_token": inherited["sram"],
        "logic_area_mm2": logic_area_mm2,
        "die_area_mm2": _as_float(command.get("die_area_mm2"), _as_float(dense.get("die_area_mm2"))),
        "active_power_mw": active_power_mw,
        "schedule_clock_ns": schedule_clock_ns,
        "timing_ok": timing_ok,
        "quality_backed": quality["quality_backed"],
        "quality": quality,
        "promotable": promotable,
        "abstraction_status": "measured_components_unmeasured_composition",
        "components": components,
        "remaining_abstractions": remaining_abstractions,
    }

    comparisons = {
        "vs_current_score32": {
            "candidate_id": score32_reference.get("candidate_id"),
            "throughput_ratio": _ratio(token_throughput_per_s, _as_float(score32_reference.get("token_throughput_per_s"))),
            "energy_ratio": _ratio(total_energy_mj, _as_float(score32_reference.get("energy_mj_per_token"))),
            "logic_area_ratio": _ratio(logic_area_mm2, _as_float(score32_reference.get("compute_area_mm2"))),
        },
        "vs_exact_fp16": {
            "candidate_id": fp16_reference.get("candidate_id"),
            "throughput_ratio": _ratio(token_throughput_per_s, _as_float(fp16_reference.get("token_throughput_per_s"))),
            "energy_ratio": _ratio(total_energy_mj, _as_float(fp16_reference.get("energy_mj_per_token"))),
            "logic_area_ratio": _ratio(logic_area_mm2, _as_float(fp16_reference.get("compute_area_mm2"))),
        },
    }
    return {
        "version": 1,
        "model": "llm_decoder_attention_score32_separated_compute_recost_v1",
        "decision": decision,
        "inputs": {
            "mixed_int8_energy_json": str(args.mixed_int8_energy_json),
            "score32_measured_command_control_json": str(args.score32_measured_command_control_json),
            "score32_quality_json": str(args.score32_quality_json),
            "hbm_controller_ppa_json": str(args.hbm_controller_ppa_json),
            "quality_aware_frontier_json": str(args.quality_aware_frontier_json),
        },
        "candidate": candidate,
        "comparisons": comparisons,
        "diagnosis": {
            "decision": decision,
            "timing_ok": timing_ok,
            "quality_backed": quality["quality_backed"],
            "promotable": promotable,
            "full_wrapper_replication_removed": True,
            "old_full_wrapper_replica_count": command.get("substituted_compute_replica_count"),
            "old_full_wrapper_area_um2": command.get("substituted_block_area_um2"),
            "old_full_wrapper_power_mw": command.get("substituted_block_power_mw"),
            "recommended_next_step": (
                "Build and measure the separated producer/consumer RTL composition, then run full-path tensor-hash equivalence."
                if quality["quality_backed"] and timing_ok
                else "Resolve failed quality or component timing evidence before composing RTL."
            ),
            "remaining_abstractions": remaining_abstractions,
        },
        "assumptions": [
            "Dense-int8 latency and external HBM/NoC/SRAM traffic are inherited unchanged from the measured mixed-int8 schedule.",
            "The selected score32/vector overhead is shared at cluster scope instead of replicated with every GEMM lane.",
            "All component powers are conservatively charged for the full token latency.",
            "Measured-component recost is evidence for prioritizing RTL work, not evidence that the composition is physically promotable.",
        ],
    }


def write_markdown(path: Path, payload: JsonDict) -> None:
    candidate = payload["candidate"]
    lines = [
        "# Score32 Separated Compute Recost",
        "",
        f"- decision: `{payload['decision']}`",
        f"- latency us: `{candidate['latency_us']}`",
        f"- throughput token/s: `{candidate['token_throughput_per_s']}`",
        f"- total energy mJ/token: `{candidate['energy_mj_per_token']}`",
        f"- logic area mm2: `{candidate['logic_area_mm2']}`",
        f"- quality backed: `{candidate['quality_backed']}`",
        f"- promotable: `{candidate['promotable']}`",
        "",
        "## Components",
        "",
        "| component | area um2 | power mW | path ns | clock ok |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in candidate["components"]:
        lines.append(
            "| {component} | {area_um2} | {power_mw} | {critical_path_ns} | {clock_ok} |".format(**row)
        )
    lines.extend(["", "## Remaining Abstractions", ""])
    lines.extend(f"- {item}" for item in candidate["remaining_abstractions"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mixed-int8-energy-json", type=Path, required=True)
    parser.add_argument("--score32-measured-command-control-json", type=Path, required=True)
    parser.add_argument("--score32-quality-json", type=Path, required=True)
    parser.add_argument("--hbm-controller-ppa-json", type=Path, required=True)
    parser.add_argument("--quality-aware-frontier-json", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    args = parser.parse_args()
    payload = build_report(args)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(args.out_md, payload)
    print(json.dumps({"ok": True, "decision": payload["decision"], "out": str(args.out)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
