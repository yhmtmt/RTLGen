#!/usr/bin/env python3
"""Recompute the Llama7B attention frontier with decode-shaped M1x8 tiles."""

from __future__ import annotations

import argparse
import csv
import json
import math
from copy import deepcopy
from pathlib import Path
from typing import Any

from npu.eval.estimate_llm_decoder_attention_kv_dual_stream_physical_feasibility import (
    _scheduled_subtile_pipeline,
)


JsonDict = dict[str, Any]


def _load(path: Path) -> JsonDict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _positive(value: Any, label: str) -> float:
    result = float(value)
    if result <= 0.0:
        raise ValueError(f"{label} must be positive")
    return result


def _metrics_rows(path: Path) -> list[JsonDict]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = [dict(row) for row in csv.DictReader(handle) if row.get("status") == "ok"]
    if not rows:
        raise ValueError(f"no status=ok metrics rows: {path}")
    for row in rows:
        row["metrics_csv"] = str(path)
    return rows


def _select_metric(path: Path, *, schedule_clock_ns: float) -> JsonDict:
    rows = _metrics_rows(path)
    feasible = [row for row in rows if float(row["critical_path_ns"]) <= schedule_clock_ns]
    candidates = feasible or rows
    return min(
        candidates,
        key=lambda row: (
            float(row.get("instance_area_um2") or "inf"),
            float(row.get("critical_path_ns") or "inf"),
            float(row.get("total_power_mw") or "inf"),
        ),
    )


def _metric_provenance(row: JsonDict) -> JsonDict:
    keys = (
        "metrics_csv",
        "design",
        "platform",
        "tag",
        "status",
        "param_hash",
        "config_hash",
        "params_json",
        "critical_path_ns",
        "instance_area_um2",
        "stdcell_area_um2",
        "stdcell_count",
        "core_area_um2",
        "die_area",
        "utilization_pct",
        "total_power_mw",
    )
    return {key: row[key] for key in keys if key in row}


def _source_schedule(payload: JsonDict, *, latency_us: float) -> JsonDict:
    candidates: list[JsonDict] = []
    best = payload.get("best")
    if isinstance(best, dict):
        candidates.append(best)
    candidates.extend(row for row in payload.get("top_rows", []) if isinstance(row, dict))
    matches = [row for row in candidates if math.isclose(float(row.get("latency_us", -1.0)), latency_us, abs_tol=1e-6)]
    if not matches:
        raise ValueError(f"no schedule row matches baseline latency {latency_us}")
    return deepcopy(matches[0])


def _dense_component(row: JsonDict) -> JsonDict:
    for component in row.get("components", []):
        if isinstance(component, dict) and component.get("component") == "operational_dense_int8_gemm_fabric":
            return component
    raise ValueError(f"frontier row {row.get('candidate_id')} lacks operational dense component")


def _effective_macs(*, k_length: int, result_cycles: int) -> tuple[int, float]:
    service_cycles = 1 + k_length + result_cycles
    return service_cycles, (8.0 * k_length) / service_cycles


def _stage_service(*, schedule: JsonDict, result_cycles: int) -> JsonDict:
    hidden = int(schedule["hidden_size"])
    attention_heads = int(schedule["attention_heads"])
    kv_heads = int(schedule["kv_heads"])
    head_dim = hidden // attention_heads
    tile_tokens = int(schedule["tile_tokens"])
    qkv_k = hidden
    qk_k = head_dim
    value_k = tile_tokens
    qkv_cycles, qkv_macs = _effective_macs(k_length=qkv_k, result_cycles=result_cycles)
    qk_cycles, qk_macs = _effective_macs(k_length=qk_k, result_cycles=result_cycles)
    value_cycles, value_macs = _effective_macs(k_length=value_k, result_cycles=result_cycles)
    return {
        "command_cycles": 1,
        "result_cycles": result_cycles,
        "qkv": {"k_length": qkv_k, "service_cycles": qkv_cycles, "effective_macs_per_cycle": qkv_macs},
        "qk": {"k_length": qk_k, "service_cycles": qk_cycles, "effective_macs_per_cycle": qk_macs},
        "value": {"k_length": value_k, "service_cycles": value_cycles, "effective_macs_per_cycle": value_macs},
        "qkv_work_macs": hidden * hidden + 2 * hidden * kv_heads * head_dim,
        "tile_qk_work_macs": tile_tokens * hidden,
        "tile_value_work_macs": tile_tokens * hidden,
    }


def _replica_policies(
    *,
    schedule: JsonDict,
    tile_area_um2: float,
    service: JsonDict,
) -> list[tuple[str, int]]:
    cluster_count = int(schedule["cluster_count"])
    source_per_cluster_macs = _positive(
        schedule.get("per_cluster_macs_per_cycle")
        or math.floor(int(schedule["compute_replica_count"]) / cluster_count)
        * _positive(schedule["measured_block_macs_per_cycle"], "source block MACs"),
        "source per-cluster MACs per cycle",
    )
    nominal = cluster_count * math.ceil(source_per_cluster_macs / 8.0)
    throughput = cluster_count * math.ceil(
        source_per_cluster_macs / float(service["qk"]["effective_macs_per_cycle"])
    )
    multiplier = _positive(schedule.get("compute_area_multiplier", 1.0), "compute area multiplier")
    noncompute_area = _positive(schedule["logic_area_used_um2"], "logic area used") - _positive(
        schedule["compute_area_um2"], "compute area"
    )
    available = max(0.0, _positive(schedule["compute_budget_um2"], "compute budget") - noncompute_area)
    area_budget = max(1, int(available // (tile_area_um2 * multiplier)))
    ordered = [("nominal_peak", nominal), ("throughput_matched", throughput), ("area_budget", area_budget)]
    seen: set[int] = set()
    result: list[tuple[str, int]] = []
    for name, count in ordered:
        if count in seen:
            continue
        seen.add(count)
        result.append((name, count))
    return result


def _recompute_schedule(
    source: JsonDict,
    *,
    active_replicas: int,
    tile_delay_ns: float,
    tile_area_um2: float,
    service: JsonDict,
) -> JsonDict:
    updated = deepcopy(source)
    multiplier = _positive(source.get("compute_area_multiplier", 1.0), "compute area multiplier")
    clock_ns = max(_positive(source["clock_ns"], "source clock"), tile_delay_ns)
    qkv_macs = active_replicas * float(service["qkv"]["effective_macs_per_cycle"])
    cluster_count = int(source["cluster_count"])
    replicas_per_cluster = max(1, active_replicas // cluster_count)
    qk_macs = replicas_per_cluster * float(service["qk"]["effective_macs_per_cycle"])
    value_macs = replicas_per_cluster * float(service["value"]["effective_macs_per_cycle"])
    updated.update(
        {
            "clock_ns": clock_ns,
            "qkv_cycles": math.ceil(float(service["qkv_work_macs"]) / qkv_macs),
            "tile_qk_cycles": math.ceil(float(service["tile_qk_work_macs"]) / qk_macs),
            "tile_value_cycles": math.ceil(float(service["tile_value_work_macs"]) / value_macs),
        }
    )
    scheduled = _scheduled_subtile_pipeline(updated)
    compute_area = active_replicas * tile_area_um2 * multiplier
    noncompute_area = _positive(source["logic_area_used_um2"], "logic area used") - _positive(
        source["compute_area_um2"], "compute area"
    )
    logic_area = noncompute_area + compute_area
    return {
        **scheduled,
        "clock_ns": clock_ns,
        "active_replica_count": active_replicas,
        "area_replica_count": int(round(active_replicas * multiplier)),
        "compute_area_um2": compute_area,
        "logic_area_used_um2": logic_area,
        "logic_area_slack_um2": _positive(source["compute_budget_um2"], "compute budget") - logic_area,
        "area_fit": logic_area <= _positive(source["compute_budget_um2"], "compute budget"),
        "effective_qkv_macs_per_cycle": qkv_macs,
        "effective_qk_macs_per_cycle_per_cluster": qk_macs,
        "effective_value_macs_per_cycle_per_cluster": value_macs,
        "replicas_per_cluster_floor": replicas_per_cluster,
        "qkv_cycles": updated["qkv_cycles"],
        "tile_qk_cycles": updated["tile_qk_cycles"],
        "tile_value_cycles": updated["tile_value_cycles"],
    }


def _replace_frontier_row(
    source: JsonDict,
    *,
    interface: str,
    policy: str,
    metric: JsonDict,
    schedule: JsonDict,
    service: JsonDict,
) -> JsonDict:
    updated = deepcopy(source)
    dense = _dense_component(updated)
    old_dense_area = _positive(dense["area_um2"], "old dense area")
    new_dense_area = float(schedule["compute_area_um2"])
    area_delta_mm2 = (new_dense_area - old_dense_area) / 1.0e6
    metric_path = str(metric["metrics_csv"])
    dense.update(
        {
            "component": "decode_shaped_m1x8_score_fabric",
            "interface": interface,
            "deployment_policy": policy,
            "source": metric_path,
            "area_um2": round(new_dense_area, 6),
            "per_tile_area_um2": float(metric["instance_area_um2"]),
            "critical_path_ns": float(metric["critical_path_ns"]),
            "clock_ok": float(metric["critical_path_ns"]) <= float(schedule["clock_ns"]),
            "active_replica_count": schedule["active_replica_count"],
            "area_replica_count": schedule["area_replica_count"],
            "vectorless_power_mw_per_tile": float(metric["total_power_mw"]),
            "vectorless_power_mw_scaled_active": round(
                float(metric["total_power_mw"]) * int(schedule["active_replica_count"]), 12
            ),
            "power_accounting": "retained_activity_backed_frontier_energy",
        }
    )
    for key in ("logic_plus_service_area_mm2", "retained_logic_area_mm2", "embodied_logic_plus_score_macro_area_mm2"):
        updated[key] = round(_positive(updated[key], key) + area_delta_mm2, 12)
    base_latency = float(schedule["latency_us"])
    scaled_latency = base_latency * _positive(updated["hbm_share_scale"], "HBM share scale")
    latency = scaled_latency + float(updated.get("divider_latency_us") or 0.0)
    updated.update(
        {
            "candidate_id": f"{source['candidate_id']}_decode_m1x8_{interface}_{policy}",
            "family": "score32_separated_two_pass_decode_shaped_m1x8",
            "baseline_source_latency_us": base_latency,
            "hbm_share_scaled_latency_us": round(scaled_latency, 12),
            "latency_us": round(latency, 12),
            "token_throughput_per_s": round(1.0e6 / latency, 12),
            "decode_score_tile_interface": interface,
            "decode_score_tile_deployment_policy": policy,
            "decode_score_tile_service": service,
            "decode_score_tile_schedule": schedule,
            "decode_score_tile_metrics": _metric_provenance(metric),
            "decode_score_tile_area_delta_mm2": round(area_delta_mm2, 12),
            "timing_ok": bool(updated.get("timing_ok", True)) and bool(dense["clock_ok"]),
            "energy_recost_status": "retained_activity_backed_energy_pending_decode_tile_activity",
        }
    )
    abstractions = [
        item
        for item in (str(value) for value in updated.get("remaining_abstractions", []))
        if "inherited dense-int8 schedule" not in item.lower()
    ]
    abstractions.extend(
        [
            "decode-shaped tile token energy is retained from prior activity evidence pending VCD/SAIF calibration",
            "QKV and value-stage reuse of the selected M1x8 result interface is schedule-modeled pending composed routing and quantization RTL",
            "tile replicas, score banks, divider service, and local routing remain physically uncomposed",
        ]
    )
    updated["remaining_abstractions"] = list(dict.fromkeys(abstractions))
    return updated


def _pareto(rows: list[JsonDict]) -> list[JsonDict]:
    feasible = [row for row in rows if row["timing_ok"] and row["decode_score_tile_schedule"]["area_fit"]]
    frontier = []
    for row in feasible:
        area = float(row["embodied_logic_plus_score_macro_area_mm2"])
        latency = float(row["latency_us"])
        dominated = any(
            float(other["embodied_logic_plus_score_macro_area_mm2"]) <= area
            and float(other["latency_us"]) <= latency
            and (
                float(other["embodied_logic_plus_score_macro_area_mm2"]) < area
                or float(other["latency_us"]) < latency
            )
            for other in feasible
        )
        if not dominated:
            frontier.append(row)
    return sorted(frontier, key=lambda row: (float(row["latency_us"]), float(row["embodied_logic_plus_score_macro_area_mm2"])))


def build_report(
    *,
    operational_frontier_json: Path,
    subtile_schedule_json: Path,
    scalar_metrics_csv: Path,
    packed_metrics_csv: Path,
) -> JsonDict:
    frontier = _load(operational_frontier_json)
    source_rows = [row for row in frontier.get("rows", []) if isinstance(row, dict)]
    if not source_rows:
        raise ValueError("operational frontier has no rows")
    baseline_latency = _positive(source_rows[0]["baseline_source_latency_us"], "baseline source latency")
    source_schedule = _source_schedule(_load(subtile_schedule_json), latency_us=baseline_latency)
    schedule_clock = _positive(source_schedule["clock_ns"], "schedule clock")
    metrics = {
        "scalar": _select_metric(scalar_metrics_csv, schedule_clock_ns=schedule_clock),
        "packed": _select_metric(packed_metrics_csv, schedule_clock_ns=schedule_clock),
    }
    result_cycles = {"scalar": 8, "packed": 1}
    rows: list[JsonDict] = []
    for interface, metric in metrics.items():
        service = _stage_service(schedule=source_schedule, result_cycles=result_cycles[interface])
        policies = _replica_policies(
            schedule=source_schedule,
            tile_area_um2=_positive(metric["instance_area_um2"], "tile area"),
            service=service,
        )
        for policy, active_replicas in policies:
            schedule = _recompute_schedule(
                source_schedule,
                active_replicas=active_replicas,
                tile_delay_ns=_positive(metric["critical_path_ns"], "tile delay"),
                tile_area_um2=_positive(metric["instance_area_um2"], "tile area"),
                service=service,
            )
            for source in source_rows:
                rows.append(
                    _replace_frontier_row(
                        source,
                        interface=interface,
                        policy=policy,
                        metric=metric,
                        schedule=schedule,
                        service=service,
                    )
                )
    pareto = _pareto(rows)
    if not pareto:
        raise ValueError("no timing- and area-feasible decode-shaped rows")
    best_throughput = min(pareto, key=lambda row: float(row["latency_us"]))
    best_area = min(pareto, key=lambda row: float(row["embodied_logic_plus_score_macro_area_mm2"]))
    return {
        "version": 1,
        "model": "llm_decoder_attention_decode_score_tile_frontier_v1",
        "decision": "decode_shaped_m1x8_schedule_and_area_recosted_energy_retained",
        "inputs": {
            "operational_frontier_json": str(operational_frontier_json),
            "subtile_schedule_json": str(subtile_schedule_json),
            "scalar_metrics_csv": str(scalar_metrics_csv),
            "packed_metrics_csv": str(packed_metrics_csv),
        },
        "measurement_policy": {
            "schedule": "recompute QKV, QK, value, subtile pipeline, layer, and token cycles from exact M1x8 service",
            "area": "replace M16x8 fabric scaling with measured M1x8 area and explicit active/area replica counts",
            "energy": "retain prior activity-backed token energy; vectorless tile power is diagnostic only",
            "precision": "inherit the merged mixed-int8 Llama7B generation-quality gate",
            "cross_stage_interface": "model the same selected M1x8 drain mode for QKV, QK, and value until composed routing is measured",
        },
        "source_schedule": source_schedule,
        "selected_scalar_tile": _metric_provenance(metrics["scalar"]),
        "selected_packed_tile": _metric_provenance(metrics["packed"]),
        "rows": rows,
        "pareto_rows": pareto,
        "diagnosis": {
            "best_throughput_candidate": best_throughput["candidate_id"],
            "best_throughput_token_per_s": best_throughput["token_throughput_per_s"],
            "best_throughput_area_mm2": best_throughput["embodied_logic_plus_score_macro_area_mm2"],
            "best_area_candidate": best_area["candidate_id"],
            "best_area_mm2": best_area["embodied_logic_plus_score_macro_area_mm2"],
            "best_area_token_per_s": best_area["token_throughput_per_s"],
            "energy_promotion_blocked": True,
            "next_step": "physically compose one selected M1x8 tile, score bank, and two-pass service cluster with activity",
        },
    }


def _write_markdown(payload: JsonDict, path: Path) -> None:
    diagnosis = payload["diagnosis"]
    lines = [
        "# Llama7B decode-shaped M1x8 score-tile frontier",
        "",
        f"- decision: `{payload['decision']}`",
        f"- best throughput: `{diagnosis['best_throughput_token_per_s']}` token/s",
        f"- best throughput area: `{diagnosis['best_throughput_area_mm2']}` mm2",
        f"- best area: `{diagnosis['best_area_mm2']}` mm2",
        f"- best-area throughput: `{diagnosis['best_area_token_per_s']}` token/s",
        "- activity-backed decode-tile energy promotion: `blocked`",
        "",
        "| candidate | token/s | latency us | energy mJ/token | area mm2 | area fit |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for row in payload["pareto_rows"]:
        lines.append(
            f"| {row['candidate_id']} | {row['token_throughput_per_s']} | {row['latency_us']} | "
            f"{row['energy_mj_per_token']} | {row['embodied_logic_plus_score_macro_area_mm2']} | "
            f"{row['decode_score_tile_schedule']['area_fit']} |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--operational-frontier-json", type=Path, required=True)
    parser.add_argument("--subtile-schedule-json", type=Path, required=True)
    parser.add_argument("--scalar-metrics-csv", type=Path, required=True)
    parser.add_argument("--packed-metrics-csv", type=Path, required=True)
    parser.add_argument("--out-json", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    args = parser.parse_args()
    payload = build_report(
        operational_frontier_json=args.operational_frontier_json,
        subtile_schedule_json=args.subtile_schedule_json,
        scalar_metrics_csv=args.scalar_metrics_csv,
        packed_metrics_csv=args.packed_metrics_csv,
    )
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_markdown(payload, args.out_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
