#!/usr/bin/env python3
"""Check physical feasibility of the dual-stream sub-tile attention schedule."""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

JsonDict = dict[str, Any]


def _effective_latency_us(row: JsonDict) -> float:
    value = row.get("adjusted_latency_us_if_feasible")
    if value is None:
        value = row.get("latency_us")
    return float(value)


def _load_json(path: Path) -> JsonDict:
    return json.loads(path.read_text(encoding="utf-8"))


def _best_ok_metrics(path: Path) -> JsonDict:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = [row for row in csv.DictReader(handle) if row.get("status") == "ok"]
    if not rows:
        raise RuntimeError(f"no status=ok metrics rows in {path}")
    best = min(
        rows,
        key=lambda row: (
            float(row.get("critical_path_ns") or "inf"),
            float(row.get("die_area") or "inf"),
            float(row.get("total_power_mw") or "inf"),
        ),
    )
    return {
        "metrics_csv": str(path),
        "critical_path_ns": float(best["critical_path_ns"]),
        "die_area_um2": float(best["die_area"]),
        "total_power_mw": float(best["total_power_mw"]),
        "param_hash": best.get("param_hash", ""),
        "tag": best.get("tag", ""),
        "result_path": best.get("result_path", ""),
    }


def _best_ok_compute_metrics(path: Path) -> JsonDict:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = [row for row in csv.DictReader(handle) if row.get("status") == "ok"]
    if not rows:
        raise RuntimeError(f"no status=ok compute metrics rows in {path}")
    best = min(
        rows,
        key=lambda row: (
            float(row.get("critical_path_ns") or "inf"),
            float(row.get("instance_area_um2") or row.get("die_area") or "inf"),
            float(row.get("total_power_mw") or "inf"),
        ),
    )
    block_area = float(best.get("instance_area_um2") or best["die_area"])
    return {
        "metrics_csv": str(path),
        "critical_path_ns": float(best["critical_path_ns"]),
        "block_area_um2": block_area,
        "die_area_um2": float(best["die_area"]),
        "total_power_mw": float(best["total_power_mw"]),
        "param_hash": best.get("param_hash", ""),
        "tag": best.get("tag", ""),
        "result_path": best.get("result_path", ""),
    }


def _source_rows(payload: JsonDict, *, limit: int) -> list[JsonDict]:
    rows = list(payload.get("best_by_compute_mode") or [])
    if isinstance(payload.get("best"), dict):
        rows.insert(0, payload["best"])
    deduped: list[JsonDict] = []
    seen: set[str] = set()
    for row in rows:
        key = json.dumps(
            {
                "compute_mode": row.get("compute_mode"),
                "latency_us": row.get("latency_us"),
                "tile_service_cycles": row.get("tile_service_cycles"),
                "subtile_count": row.get("subtile_count"),
                "subtile_buffer_count": row.get("subtile_buffer_count"),
                "prefetch_distance": row.get("prefetch_distance"),
                "normalize_strategy": row.get("normalize_strategy"),
            },
            sort_keys=True,
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
        if len(deduped) >= limit:
            break
    return deduped


def _row_with_budget(
    source_row: JsonDict,
    *,
    full_value_tile: JsonDict,
    softmax_weight: JsonDict,
    composed_dual_stream: JsonDict | None,
    compute_block: JsonDict | None,
    compute_block_macs_per_cycle: int | None,
    compute_arch_name: str | None,
    buffer_area_um2_per_byte: float,
    precision_profile: str,
) -> JsonDict:
    clusters = int(source_row["cluster_count"])
    compute_multiplier = float(source_row.get("compute_area_multiplier", 1.0))
    current_compute_area = float(source_row["compute_area_um2"])
    compute_budget = float(source_row["compute_budget_um2"])
    current_l1_overhead = float(source_row["measured_l1_overhead_area_um2"])
    current_local_datapath_area = float(source_row["local_datapath_area_um2"])
    current_softmax_area = float(source_row["softmax_weight_generator_area_um2"])
    current_logic_used = float(source_row["logic_area_used_um2"])
    required_buffer_bytes = int(source_row.get("required_stream_buffer_bytes", source_row.get("tile_local_buffer_bytes", 0)))
    available_local_capacity = int(source_row.get("available_local_capacity_bytes", source_row.get("local_capacity_bytes_per_cluster", 0)))

    measured_stream_area = float(full_value_tile["die_area_um2"])
    measured_softmax_area = float(softmax_weight["die_area_um2"])
    source_clock_ns = float(source_row["clock_ns"])
    use_composed_dual_stream = composed_dual_stream is not None
    if use_composed_dual_stream:
        composed_area = float(composed_dual_stream.get("block_area_um2") or composed_dual_stream["die_area_um2"])
        composed_clock_ns = float(composed_dual_stream["critical_path_ns"])
        composed_power = float(composed_dual_stream["total_power_mw"])
        source_block_macs_per_cycle = int(source_row["measured_block_macs_per_cycle"])
        composed_replica_count = int(
            math.ceil(float(source_row["macs_per_cycle"]) / max(1, source_block_macs_per_cycle))
        )
    else:
        composed_area = 0.0
        composed_clock_ns = 0.0
        composed_power = 0.0
        composed_replica_count = 0
    stream_buffer_area = required_buffer_bytes * buffer_area_um2_per_byte

    if use_composed_dual_stream:
        # The composed wrapper contains both int8 streams, reciprocal-LUT softmax, and stream-buffer/control.
        # Replace local+softmax+compute through a single measured area term.
        selected_local_datapath_area = 0.0
        selected_softmax_area = 0.0
        selected_l1_overhead = current_l1_overhead + clusters * (
            stream_buffer_area - current_local_datapath_area - current_softmax_area
        )
    else:
        selected_local_datapath_area = compute_multiplier * measured_stream_area
        selected_softmax_area = measured_softmax_area
        selected_l1_overhead = current_l1_overhead + clusters * (
            selected_local_datapath_area
            + selected_softmax_area
            + stream_buffer_area
            - current_local_datapath_area
            - current_softmax_area
        )

    compute_substitution_enabled = use_composed_dual_stream or (compute_block is not None)
    if use_composed_dual_stream:
        target_block_area = composed_area
        target_block_macs = int(source_row["macs_per_cycle"])
        target_replica_count = composed_replica_count
        base_compute_area = target_replica_count * target_block_area
        base_compute_power = target_replica_count * composed_power
        target_block_clock = composed_clock_ns
        target_block_power = composed_power
        target_arch = "attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q10"
        compute_area_required = base_compute_area
    elif compute_block is None:
        base_compute_area = current_compute_area
        base_compute_power = float(source_row.get("compute_power_mw", source_row.get("measured_block_power_mw", 0.0)))
        target_replica_count = int(source_row["compute_replica_count"])
        target_block_area = float(source_row["measured_block_area_um2"])
        target_block_macs = int(source_row["measured_block_macs_per_cycle"])
        target_block_clock = float(source_row["measured_block_clock_ns"])
        target_block_power = float(source_row.get("measured_block_power_mw", 0.0))
        target_arch = str(source_row.get("compute_arch", ""))
        compute_area_required = base_compute_area * compute_multiplier
    else:
        target_block_area = float(compute_block["block_area_um2"])
        target_block_macs = int(compute_block_macs_per_cycle or source_row["measured_block_macs_per_cycle"])
        target_replica_count = int(math.ceil(float(source_row["macs_per_cycle"]) / max(1, target_block_macs)))
        base_compute_area = target_replica_count * target_block_area
        target_block_clock = float(compute_block["critical_path_ns"])
        target_block_power = float(compute_block["total_power_mw"])
        base_compute_power = target_replica_count * target_block_power
        target_arch = str(compute_arch_name or source_row.get("compute_arch", ""))
        compute_area_required = base_compute_area * compute_multiplier
    logic_used_required = current_logic_used + (compute_area_required - current_compute_area) + (
        selected_l1_overhead - current_l1_overhead
    )
    logic_slack_required = compute_budget - logic_used_required
    compute_area_over_budget = max(0.0, logic_used_required - compute_budget)
    required_compute_density_gain = (
        compute_area_required / max(1.0, compute_budget - selected_l1_overhead)
    )
    if compute_block is None and not use_composed_dual_stream:
        replica_count_budgeted = int(current_compute_area // max(1.0, target_block_area))
    else:
        replica_count_budgeted = int(max(0.0, compute_budget - selected_l1_overhead) // max(1.0, target_block_area))
    replica_count_required = int(
        math.ceil(target_replica_count * (compute_multiplier if not use_composed_dual_stream else 1.0))
    )
    replica_shortfall = max(0, replica_count_required - replica_count_budgeted)
    area_fit = logic_slack_required >= 0.0
    buffer_fit = required_buffer_bytes <= available_local_capacity
    feasible = area_fit and buffer_fit

    if feasible:
        if use_composed_dual_stream and composed_clock_ns > 0.0 and source_clock_ns > 0.0:
            adjusted_latency_us = float(source_row["latency_us"]) * composed_clock_ns / source_clock_ns
            adjusted_speedup = float(source_row["latency_speedup_vs_hbm_closed_source"]) * source_clock_ns / composed_clock_ns
        else:
            adjusted_latency_us = float(source_row["latency_us"])
            adjusted_speedup = float(source_row["latency_speedup_vs_hbm_closed_source"])
        adjusted_tile_service_cycles = int(source_row["tile_service_cycles"])
    else:
        adjusted_latency_us = None
        adjusted_tile_service_cycles = None
        adjusted_speedup = None
        if compute_multiplier > 1.0:
            # If the doubled stream cannot fit, the nearest already-measured same-area schedule is split_mac.
            adjusted_latency_us = None

    out = dict(source_row)
    out.update(
        {
            "dual_stream_physical_model": (
                "measured_dual_stream_composed_budget_v1"
                if use_composed_dual_stream
                else "measured_full_value_tile_budget_v1"
            ),
            "precision_profile": precision_profile,
            "measured_full_value_tile_metrics_csv": full_value_tile["metrics_csv"],
            "measured_full_value_tile_area_um2": measured_stream_area,
            "measured_full_value_tile_clock_ns": full_value_tile["critical_path_ns"],
            "measured_full_value_tile_power_mw": full_value_tile["total_power_mw"],
            "measured_softmax_weight_metrics_csv": softmax_weight["metrics_csv"],
            "measured_softmax_weight_area_um2": measured_softmax_area,
            "measured_softmax_weight_clock_ns": softmax_weight["critical_path_ns"],
            "measured_softmax_weight_power_mw": softmax_weight["total_power_mw"],
            **(
                {
                    "measured_dual_stream_composed_metrics_csv": composed_dual_stream["metrics_csv"],
                    "measured_dual_stream_composed_area_um2": composed_area,
                    "measured_dual_stream_composed_clock_ns": composed_clock_ns,
                    "measured_dual_stream_composed_power_mw": composed_power,
                    "measured_dual_stream_composed_required_replicas": composed_replica_count,
                }
                if use_composed_dual_stream
                else {}
            ),
            "stream_buffer_area_um2_per_byte": buffer_area_um2_per_byte,
            "stream_buffer_area_um2_per_cluster": round(stream_buffer_area, 6),
            "selected_local_datapath_area_um2_per_cluster": round(selected_local_datapath_area, 6),
            "selected_l1_overhead_area_um2": round(selected_l1_overhead, 6),
            "compute_area_required_um2": round(compute_area_required, 6),
            "compute_area_multiplier_required": compute_multiplier,
            "compute_substitution_enabled": compute_substitution_enabled,
            "source_compute_arch": source_row.get("compute_arch"),
            "substituted_compute_arch": target_arch if compute_substitution_enabled else None,
            "substituted_compute_metrics_csv": (
                composed_dual_stream["metrics_csv"]
                if use_composed_dual_stream
                else compute_block["metrics_csv"] if compute_block else None
            ),
            "substituted_block_area_um2": round(target_block_area, 6) if compute_substitution_enabled else None,
            "substituted_block_clock_ns": round(target_block_clock, 6) if compute_substitution_enabled else None,
            "substituted_block_power_mw": round(target_block_power, 6) if compute_substitution_enabled else None,
            "substituted_block_macs_per_cycle": target_block_macs if compute_substitution_enabled else None,
            "substituted_compute_replica_count": target_replica_count if compute_substitution_enabled else None,
            "substituted_compute_area_um2": round(base_compute_area, 6) if compute_substitution_enabled else None,
            "substituted_compute_power_mw": round(base_compute_power, 6) if compute_substitution_enabled else None,
            "logic_area_used_required_um2": round(logic_used_required, 6),
            "logic_area_slack_required_um2": round(logic_slack_required, 6),
            "compute_area_over_budget_um2": round(compute_area_over_budget, 6),
            "required_compute_density_gain": round(required_compute_density_gain, 6),
            "replica_count_required": replica_count_required,
            "replica_count_budgeted_at_current_compute_area": replica_count_budgeted,
            "replica_count_shortfall": replica_shortfall,
            "local_datapath_clock_ok": float(full_value_tile["critical_path_ns"]) <= float(source_row["clock_ns"]),
            "softmax_weight_clock_ok": float(softmax_weight["critical_path_ns"]) <= float(source_row["clock_ns"]),
            "compute_clock_ok": target_block_clock <= float(source_row["clock_ns"]),
            "area_fit": area_fit,
            "buffer_fit": buffer_fit,
            "physical_feasible": feasible,
            "adjusted_latency_us_if_feasible": adjusted_latency_us,
            "adjusted_tile_service_cycles_if_feasible": adjusted_tile_service_cycles,
            "adjusted_speedup_if_feasible": adjusted_speedup,
        }
    )
    return out


def build_report(args: argparse.Namespace) -> JsonDict:
    source = _load_json(args.subtile_pipeline_json)
    source_rows = _source_rows(source, limit=args.frontier_row_limit)
    full_value_tile = _best_ok_metrics(args.full_value_tile_metrics)
    softmax_weight = _best_ok_metrics(args.softmax_weight_metrics)
    composed_dual_stream = (
        _best_ok_compute_metrics(args.composed_dual_stream_metrics)
        if getattr(args, "composed_dual_stream_metrics", None)
        else None
    )
    compute_block = _best_ok_compute_metrics(args.compute_block_metrics) if args.compute_block_metrics else None
    quality_gate = _load_json(args.quality_gate_json) if args.quality_gate_json else None
    rows = [
        _row_with_budget(
            row,
            full_value_tile=full_value_tile,
            softmax_weight=softmax_weight,
            composed_dual_stream=composed_dual_stream,
            compute_block=compute_block,
            compute_block_macs_per_cycle=args.compute_block_macs_per_cycle,
            compute_arch_name=args.compute_arch_name,
            buffer_area_um2_per_byte=args.buffer_area_um2_per_byte,
            precision_profile=args.precision_profile,
        )
        for row in source_rows
    ]
    feasible_rows = [row for row in rows if row["physical_feasible"]]
    best_feasible = min(feasible_rows, key=_effective_latency_us) if feasible_rows else None
    best_requested = min(rows, key=lambda row: float(row["latency_us"]))
    best_area_fit = min(
        (row for row in rows if row["area_fit"]),
        key=_effective_latency_us,
        default=None,
    )
    decision = "dual_stream_feasible" if best_feasible and best_feasible.get("compute_mode") == "dual_mac" else "dual_stream_area_blocked"
    assumptions = [
        "The dual_mac schedule requires an explicit compute_area_multiplier from the sub-tile scheduler.",
        "Measured full-value tile and softmax-weight generator PPA are used for local datapath overhead only.",
        "The dense GEMM compute array is treated as already packed into the current logic budget; extra dual-stream compute must fit that same budget to be feasible.",
        "Buffer capacity is checked against measured local SRAM bytes; an optional buffer-area proxy can be added for sensitivity but defaults to zero to avoid double-counting measured local SRAM.",
    ]
    if composed_dual_stream:
        assumptions.append(
            "When composed dual-stream wrapper substitution is enabled, full-value and softmax measurements are treated as folded into the measured dual-stream RTL wrapper, and wrapper clock is used to scale feasible latency if it differs from source schedule clock."
        )
    elif compute_block:
        assumptions.append(
            "When compute-block substitution is enabled, measured block area/power/clock replace the source dense compute block, but the upstream schedule latency is not recomputed; this is an area-feasibility substitution and a conservative latency view when the substituted block clock is no slower than the source clock."
        )
    else:
        assumptions.append("No compute-block substitution was requested; dense compute area comes from the source schedule.")
    return {
        "version": 1,
        "model": args.model_name,
        "subtile_pipeline_json": str(args.subtile_pipeline_json),
        "source_model": source.get("model"),
        "inputs": {
            "frontier_row_limit": args.frontier_row_limit,
            "full_value_tile_metrics": str(args.full_value_tile_metrics),
            "softmax_weight_metrics": str(args.softmax_weight_metrics),
            "composed_dual_stream_metrics": (
                str(args.composed_dual_stream_metrics) if args.composed_dual_stream_metrics else None
            ),
            "compute_block_metrics": str(args.compute_block_metrics) if args.compute_block_metrics else None,
            "compute_block_macs_per_cycle": args.compute_block_macs_per_cycle,
            "compute_arch_name": args.compute_arch_name,
            "quality_gate_json": str(args.quality_gate_json) if args.quality_gate_json else None,
            "precision_profile": args.precision_profile,
            "buffer_area_um2_per_byte": args.buffer_area_um2_per_byte,
        },
        "quality_gate": {
            "decision": (quality_gate or {}).get("diagnosis", {}).get("decision"),
            "best_low_cost_candidate": (quality_gate or {}).get("diagnosis", {}).get("best_low_cost_candidate"),
            "best_low_cost_decision": (quality_gate or {}).get("diagnosis", {}).get("best_low_cost_decision"),
            "best_quality_candidate": (quality_gate or {}).get("diagnosis", {}).get("best_quality_candidate"),
            "best_quality_decision": (quality_gate or {}).get("diagnosis", {}).get("best_quality_decision"),
        }
        if quality_gate
        else None,
        "diagnosis": {
            "decision": decision,
            "precision_profile": args.precision_profile,
            "source_rows_used": len(source_rows),
            "physical_feasible_rows": len(feasible_rows),
            "best_requested_mode": best_requested.get("compute_mode"),
            "best_requested_latency_us": best_requested.get("latency_us"),
            "best_requested_adjusted_latency_us_if_feasible": best_requested.get("adjusted_latency_us_if_feasible"),
            "best_requested_speedup_vs_hbm_closed_source": best_requested.get("latency_speedup_vs_hbm_closed_source"),
            "best_requested_adjusted_speedup_vs_hbm_closed_source": best_requested.get("adjusted_speedup_if_feasible"),
            "best_requested_adjusted_tile_service_cycles": best_requested.get("adjusted_tile_service_cycles_if_feasible"),
            "best_requested_area_fit": best_requested.get("area_fit"),
            "best_requested_logic_slack_um2": best_requested.get("logic_area_slack_required_um2"),
            "best_requested_compute_area_over_budget_um2": best_requested.get("compute_area_over_budget_um2"),
            "best_requested_required_compute_density_gain": best_requested.get("required_compute_density_gain"),
            "best_requested_compute_substitution_enabled": best_requested.get("compute_substitution_enabled"),
            "best_requested_substituted_compute_arch": best_requested.get("substituted_compute_arch"),
            "best_requested_substituted_compute_area_um2": best_requested.get("substituted_compute_area_um2"),
            "best_requested_compute_clock_ok": best_requested.get("compute_clock_ok"),
            "best_feasible_mode": best_feasible.get("compute_mode") if best_feasible else None,
            "best_feasible_latency_us": _effective_latency_us(best_feasible) if best_feasible else None,
            "best_feasible_source_latency_us": best_feasible.get("latency_us") if best_feasible else None,
            "best_area_fit_mode": best_area_fit.get("compute_mode") if best_area_fit else None,
            "best_area_fit_latency_us": _effective_latency_us(best_area_fit) if best_area_fit else None,
            "best_area_fit_source_latency_us": best_area_fit.get("latency_us") if best_area_fit else None,
            "recommended_next_step": (
                "measure a denser dual-stream fused attention datapath or reduce compute replicas before promoting dual_mac"
                if decision == "dual_stream_area_blocked"
                else "promote dual-stream schedule into a measured RTL/PPA wrapper"
            ),
        },
        "best_requested": best_requested,
        "best_feasible": best_feasible,
        "best_area_fit": best_area_fit,
        "rows": rows,
        "assumptions": assumptions,
    }


def write_markdown(path: Path, payload: JsonDict) -> None:
    diag = payload["diagnosis"]
    best = payload["best_requested"]
    lines = [
        "# Llama7B Dual-Stream Physical Feasibility",
        "",
        f"- decision: `{diag['decision']}`",
        f"- precision profile: `{diag['precision_profile']}`",
        f"- source rows used: `{diag['source_rows_used']}`",
        f"- physical feasible rows: `{diag['physical_feasible_rows']}`",
        f"- best requested mode: `{diag['best_requested_mode']}`",
        f"- best requested latency us: `{diag['best_requested_latency_us']}`",
        f"- best requested logic slack um2: `{diag['best_requested_logic_slack_um2']}`",
        f"- best requested compute area over budget um2: `{diag['best_requested_compute_area_over_budget_um2']}`",
        f"- best requested required compute density gain: `{diag['best_requested_required_compute_density_gain']}`",
        f"- best requested compute substitution: `{diag['best_requested_compute_substitution_enabled']}`",
        f"- best requested substituted compute arch: `{diag['best_requested_substituted_compute_arch']}`",
        f"- best requested substituted compute area um2: `{diag['best_requested_substituted_compute_area_um2']}`",
        f"- recommended next step: `{diag['recommended_next_step']}`",
        "",
        "## Best Requested",
        "",
        "| mode | latency us | speedup | area fit | buffer fit | logic slack um2 | area over budget | density gain | required replicas | budget replicas | req buffer bytes |",
        "|---|---:|---:|---|---|---:|---:|---:|---:|---:|---:|",
        "| {compute_mode} | {latency_us} | {latency_speedup_vs_hbm_closed_source} | {area_fit} | "
        "{buffer_fit} | {logic_area_slack_required_um2} | {compute_area_over_budget_um2} | "
        "{required_compute_density_gain} | {replica_count_required} | "
        "{replica_count_budgeted_at_current_compute_area} | {required_stream_buffer_bytes} |".format(**best),
        "",
        "## Rows",
        "",
        "| mode | latency us | area fit | feasible | logic slack um2 | local datapath/cluster | compute area required |",
        "|---|---:|---|---|---:|---:|---:|",
    ]
    for row in payload["rows"]:
        lines.append(
            "| {compute_mode} | {latency_us} | {area_fit} | {physical_feasible} | "
            "{logic_area_slack_required_um2} | {selected_local_datapath_area_um2_per_cluster} | "
            "{compute_area_required_um2} |".format(**row)
        )
    lines.extend(["", "## Assumptions", ""])
    lines.extend(f"- {item}" for item in payload["assumptions"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--subtile-pipeline-json", type=Path, required=True)
    parser.add_argument("--full-value-tile-metrics", type=Path, required=True)
    parser.add_argument("--softmax-weight-metrics", type=Path, required=True)
    parser.add_argument("--composed-dual-stream-metrics", type=Path)
    parser.add_argument("--compute-block-metrics", type=Path)
    parser.add_argument("--compute-block-macs-per-cycle", type=int)
    parser.add_argument("--compute-arch-name")
    parser.add_argument("--quality-gate-json", type=Path)
    parser.add_argument("--precision-profile", default="exact_q8_kv8_v16_s24_w16")
    parser.add_argument(
        "--model-name",
        default="llm_decoder_attention_kv_dual_stream_physical_feasibility_llama7b_v1",
    )
    parser.add_argument("--frontier-row-limit", type=int, default=8)
    parser.add_argument("--buffer-area-um2-per-byte", type=float, default=0.0)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    args = parser.parse_args()

    payload = build_report(args)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(args.out_md, payload)
    print(json.dumps({"ok": True, "out": str(args.out), "out_md": str(args.out_md)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
