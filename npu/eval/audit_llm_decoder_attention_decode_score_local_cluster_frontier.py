#!/usr/bin/env python3
"""Correct the Llama7B decode frontier with the measured local-cluster boundary."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any


JsonDict = dict[str, Any]


def _load(path: Path) -> JsonDict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _ok_metrics(path: Path) -> list[JsonDict]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = [dict(row) for row in csv.DictReader(handle) if row.get("status") == "ok"]
    if not rows:
        raise ValueError(f"no status=ok metrics rows: {path}")
    return rows


def _selected_metric(path: Path) -> JsonDict:
    rows = _ok_metrics(path)
    return min(rows, key=lambda row: (float(row["critical_path_ns"]), float(row["instance_area_um2"])))


def _metric_provenance(row: JsonDict, *, metrics_csv: Path) -> JsonDict:
    keys = (
        "design",
        "platform",
        "config_hash",
        "param_hash",
        "tag",
        "status",
        "critical_path_ns",
        "die_area",
        "total_power_mw",
        "instance_area_um2",
        "stdcell_area_um2",
        "stdcell_count",
        "core_area_um2",
        "utilization_pct",
        "flow_elapsed_seconds",
        "params_json",
    )
    return {"metrics_csv": str(metrics_csv), **{key: row[key] for key in keys if key in row}}


def _source_schedule(frontier: JsonDict) -> JsonDict:
    schedule = frontier.get("source_schedule")
    if not isinstance(schedule, dict):
        raise ValueError("frontier lacks source_schedule")
    return schedule


def _cluster_service(
    *,
    schedule: JsonDict,
    score_lanes: int,
    value_lanes: int,
    scale_lanes: int,
    divider_cycles: int,
    value_response_latency: int,
) -> JsonDict:
    hidden = int(schedule["hidden_size"])
    heads = int(schedule["attention_heads"])
    head_dim = hidden // heads
    sequence = int(schedule["sequence_length"])
    if sequence % score_lanes:
        raise ValueError("sequence length must be divisible by score lanes")
    if head_dim % value_lanes:
        raise ValueError("head dimension must be divisible by value lanes")
    blocks = sequence // score_lanes
    value_slices = head_dim // value_lanes
    scale_cycles = math.ceil(score_lanes / scale_lanes)
    fill_cycles_per_block = 1 + head_dim + 1 + scale_cycles + 1
    replay_cycles_per_block = max(3, value_response_latency + 2)
    command_cycles = (
        1
        + blocks * fill_cycles_per_block
        + blocks * replay_cycles_per_block
        + divider_cycles
        + 1
    )
    return {
        "score_lanes": score_lanes,
        "value_lanes": value_lanes,
        "score_scale_lanes_per_cycle": scale_lanes,
        "head_dim": head_dim,
        "sequence_length": sequence,
        "blocks_per_command": blocks,
        "value_slices_per_head": value_slices,
        "commands_per_layer": heads * value_slices,
        "fill_cycles_per_block": fill_cycles_per_block,
        "replay_cycles_per_block": replay_cycles_per_block,
        "divider_cycles_per_command": divider_cycles,
        "result_accept_cycles": 1,
        "command_service_cycles": command_cycles,
        "value_response_latency_cycles": value_response_latency,
        "service_semantics": "no_stall_ready_valid_lower_bound",
    }


def _row(
    *,
    cluster_count: int,
    service: JsonDict,
    schedule: JsonDict,
    cluster_metric: JsonDict,
    dense_tile_area_um2: float,
    dense_tile_macs_per_cycle: float,
) -> JsonDict:
    budget = float(schedule["compute_budget_um2"])
    cluster_area = float(cluster_metric["instance_area_um2"])
    cluster_area_total = cluster_count * cluster_area
    qkv_output_tiles = int(schedule["hidden_size"]) // 8 + (
        2 * int(schedule["kv_heads"]) * int(service["head_dim"]) // 8
    )
    dense_count = min(qkv_output_tiles, max(0, math.floor((budget - cluster_area_total) / dense_tile_area_um2)))
    area_fit = dense_count > 0 and cluster_area_total + dense_count * dense_tile_area_um2 <= budget
    qkv_work = int(schedule["hidden_size"]) ** 2 + 2 * int(schedule["hidden_size"]) * int(
        schedule["kv_heads"]
    ) * int(service["head_dim"])
    qkv_cycles = math.ceil(qkv_work / (dense_count * dense_tile_macs_per_cycle)) if dense_count else None
    waves = math.ceil(int(service["commands_per_layer"]) / cluster_count)
    attention_cycles = waves * int(service["command_service_cycles"])
    fixed_cycles = int(schedule.get("command_dispatch_cycles", 0)) + int(schedule.get("kv_write_cycles", 0))
    layer_cycles = qkv_cycles + attention_cycles + fixed_cycles if qkv_cycles is not None else None
    clock_ns = max(float(schedule["clock_ns"]), float(cluster_metric["critical_path_ns"]))
    total_cycles = layer_cycles * int(schedule["layers"]) if layer_cycles is not None else None
    latency_us = total_cycles * clock_ns / 1000.0 if total_cycles is not None else None
    noncompute_logic = float(schedule["logic_area_used_um2"]) - float(schedule["compute_area_um2"])
    logic_area = noncompute_logic + cluster_area_total + dense_count * dense_tile_area_um2
    sram_area = float(schedule.get("measured_shared_sram_used_area_um2", 0.0)) + float(
        schedule.get("measured_tile_local_sram_area_um2", 0.0)
    )
    return {
        "candidate_id": f"decode_score_local_cluster_c{cluster_count}_vl{service['value_response_latency_cycles']}",
        "cluster_count": cluster_count,
        "cluster_waves_per_layer": waves,
        "dense_qkv_tile_count": dense_count,
        "dense_qkv_useful_parallelism_limit": qkv_output_tiles,
        "qkv_cycles": qkv_cycles,
        "attention_cycles": attention_cycles,
        "layer_cycles": layer_cycles,
        "total_cycles": total_cycles,
        "clock_ns": clock_ns,
        "latency_us": round(latency_us, 6) if latency_us is not None else None,
        "token_throughput_per_s": round(1.0e6 / latency_us, 12) if latency_us else None,
        "cluster_area_mm2": round(cluster_area_total / 1.0e6, 9),
        "dense_qkv_area_mm2": round(dense_count * dense_tile_area_um2 / 1.0e6, 9),
        "compute_budget_slack_mm2": round(
            (budget - cluster_area_total - dense_count * dense_tile_area_um2) / 1.0e6, 9
        ),
        "logic_area_mm2": round(logic_area / 1.0e6, 9),
        "embodied_logic_plus_shared_sram_area_mm2": round((logic_area + sram_area) / 1.0e6, 9),
        "compute_budget_area_fit": area_fit,
        "timing_feasible": float(cluster_metric["critical_path_ns"]) <= clock_ns,
        "energy_mj_per_token": None,
        "energy_status": "blocked_pending_cluster_switching_activity",
    }


def build_report(
    *,
    prior_frontier_json: Path,
    cluster_metrics_csv: Path,
    equivalence_json: Path,
    cluster_counts: list[int],
    value_response_latencies: list[int],
    dense_tile_area_um2: float | None = None,
    dense_tile_macs_per_cycle: float | None = None,
) -> JsonDict:
    frontier = _load(prior_frontier_json)
    equivalence = _load(equivalence_json)
    if not equivalence.get("equivalence_pass"):
        raise ValueError("composed local-cluster equivalence did not pass")
    schedule = _source_schedule(frontier)
    metric = _selected_metric(cluster_metrics_csv)
    source_tile = frontier.get("selected_scalar_tile")
    if not isinstance(source_tile, dict):
        source_tile = frontier.get("selected_packed_tile")
    if not isinstance(source_tile, dict) and (dense_tile_area_um2 is None or dense_tile_macs_per_cycle is None):
        raise ValueError("frontier lacks a measured M1x8 QKV tile")
    source_service = frontier.get("rows", [{}])[0].get("decode_score_tile_service", {})
    qkv_service = source_service.get("qkv", {}) if isinstance(source_service, dict) else {}
    if dense_tile_area_um2 is None:
        dense_tile_area_um2 = float(source_tile["instance_area_um2"])
    if dense_tile_macs_per_cycle is None:
        dense_tile_macs_per_cycle = float(qkv_service["effective_macs_per_cycle"])
    rows: list[JsonDict] = []
    services: dict[int, JsonDict] = {}
    for latency in value_response_latencies:
        service = _cluster_service(
            schedule=schedule,
            score_lanes=8,
            value_lanes=8,
            scale_lanes=1,
            divider_cycles=480,
            value_response_latency=latency,
        )
        services[latency] = service
        for count in cluster_counts:
            rows.append(
                _row(
                    cluster_count=count,
                    service=service,
                    schedule=schedule,
                    cluster_metric=metric,
                    dense_tile_area_um2=dense_tile_area_um2,
                    dense_tile_macs_per_cycle=dense_tile_macs_per_cycle,
                )
            )
    feasible = [row for row in rows if row["compute_budget_area_fit"] and row["timing_feasible"]]
    if not feasible:
        raise ValueError("no feasible cluster-count row")
    best = max(feasible, key=lambda row: float(row["token_throughput_per_s"]))
    prior_best = max(float(row["token_throughput_per_s"]) for row in frontier.get("pareto_rows", []))
    return {
        "version": 1,
        "model": "llm_decoder_attention_decode_score_local_cluster_frontier_v1",
        "decision": "prior_decode_score_tile_frontier_retracted_composed_cluster_lower_bound_only",
        "inputs": {
            "prior_frontier_json": str(prior_frontier_json),
            "cluster_metrics_csv": str(cluster_metrics_csv),
            "equivalence_json": str(equivalence_json),
        },
        "selected_cluster_metric": _metric_provenance(metric, metrics_csv=cluster_metrics_csv),
        "dense_qkv_tile": {
            "source": source_tile,
            "area_um2": dense_tile_area_um2,
            "effective_macs_per_cycle": dense_tile_macs_per_cycle,
            "shape": "M1x8 autoregressive decode",
        },
        "equivalence": {
            "decision": equivalence.get("decision"),
            "equivalence_pass": equivalence.get("equivalence_pass"),
            "score_tensor_hash": equivalence.get("score_tensor_hash"),
            "final_tensor_hash": equivalence.get("final_tensor_hash"),
        },
        "services": {str(key): value for key, value in services.items()},
        "rows": rows,
        "diagnosis": {
            "prior_best_token_throughput_per_s_retracted": prior_best,
            "best_no_stall_candidate": best["candidate_id"],
            "best_no_stall_token_throughput_upper_bound_per_s": best["token_throughput_per_s"],
            "best_no_stall_latency_lower_bound_us": best["latency_us"],
            "best_no_stall_area_mm2": best["embodied_logic_plus_shared_sram_area_mm2"],
            "reason": (
                "The prior frontier scaled bare M1x8 tiles as QKV, QK, and value compute. The composed RTL "
                "owns one 512 KiB score bank and emits only eight of 128 value dimensions, requiring 16 "
                "commands per head and explicit fill, replay, and division service."
            ),
            "promotion_blocked": True,
            "next_architecture": (
                "Split the QK producer/score bank from replicated value-slice accumulators so one score fill "
                "and replay stream serves all 16 value slices; then measure composed routing and activity."
            ),
        },
        "remaining_abstractions": [
            "The latency is a no-stall lower bound; producer, key/value broadcast, NoC, and SRAM contention are not closed.",
            "Dense QKV tile area and MAC/cycle are inherited measured values, not composed with the cluster.",
            "Cluster power is vectorless; token energy is withheld pending VCD/SAIF switching activity.",
            "FakeRAM LEF/LIB views remain physical proxies without SRAM GDS signoff.",
            "External command score multiplier/shift derivation remains outside the cluster.",
        ],
    }


def _write_markdown(payload: JsonDict, path: Path) -> None:
    diagnosis = payload["diagnosis"]
    lines = [
        "# Llama7B composed decode-score cluster correction",
        "",
        f"- decision: `{payload['decision']}`",
        f"- retracted prior best: `{diagnosis['prior_best_token_throughput_per_s_retracted']}` token/s",
        f"- composed no-stall throughput upper bound: `{diagnosis['best_no_stall_token_throughput_upper_bound_per_s']}` token/s",
        f"- corresponding area: `{diagnosis['best_no_stall_area_mm2']}` mm2",
        "- energy promotion: `blocked`",
        "",
        "| candidate | clusters | waves/layer | QKV tiles | latency us | token/s | area mm2 | fit |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| {row['candidate_id']} | {row['cluster_count']} | {row['cluster_waves_per_layer']} | "
            f"{row['dense_qkv_tile_count']} | {row['latency_us']} | {row['token_throughput_per_s']} | "
            f"{row['embodied_logic_plus_shared_sram_area_mm2']} | {row['compute_budget_area_fit']} |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prior-frontier-json", type=Path, required=True)
    parser.add_argument("--cluster-metrics-csv", type=Path, required=True)
    parser.add_argument("--equivalence-json", type=Path, required=True)
    parser.add_argument("--cluster-counts", default="32,64,96,128,144,147")
    parser.add_argument("--value-response-latencies", default="1,4,8")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    args = parser.parse_args()
    payload = build_report(
        prior_frontier_json=args.prior_frontier_json,
        cluster_metrics_csv=args.cluster_metrics_csv,
        equivalence_json=args.equivalence_json,
        cluster_counts=[int(value) for value in args.cluster_counts.split(",")],
        value_response_latencies=[int(value) for value in args.value_response_latencies.split(",")],
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_markdown(payload, args.out_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
