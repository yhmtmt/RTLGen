#!/usr/bin/env python3
"""Estimate output-projection producer latency under weight-memory hierarchy choices."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


JsonDict = dict[str, Any]


def _load_json(path: str | Path) -> JsonDict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object: {path}")
    return data


def _int_list(value: str) -> list[int]:
    parsed = [int(item.strip()) for item in value.split(",") if item.strip()]
    if not parsed or any(item <= 0 for item in parsed):
        raise argparse.ArgumentTypeError("expected comma-separated positive integers")
    return parsed


def _float_list(value: str) -> list[float]:
    parsed = [float(item.strip()) for item in value.split(",") if item.strip()]
    if not parsed or any(item < 0.0 for item in parsed):
        raise argparse.ArgumentTypeError("expected comma-separated non-negative floats")
    return parsed


def _ceil_div(a: int | float, b: int | float) -> int:
    if b <= 0:
        raise ValueError("divisor must be positive")
    return int(math.ceil(a / b))


def _byte_width(bits: int) -> int:
    return max(1, math.ceil(bits / 8))


def _producer_latency(row: JsonDict) -> float:
    return float(
        row.get("calibrated_coupled_latency_us_per_token")
        or row.get("coupled_latency_us_per_token")
        or row.get("producer_latency_us_per_token")
        or 0.0
    )


def _baseline_by_shape(calibration: JsonDict) -> dict[tuple[int, int], JsonDict]:
    best: dict[tuple[int, int], JsonDict] = {}
    for row in calibration.get("calibrated_coupled_ranker_sweep", []):
        if not isinstance(row, dict) or row.get("status") != "ok":
            continue
        key = (int(row.get("hidden_size", 0) or 0), int(row.get("vocab_size", 0) or 0))
        if key[0] <= 0 or key[1] <= 0:
            continue
        if key not in best or _producer_latency(row) < _producer_latency(best[key]):
            best[key] = row
    return best


def _focus_shapes(frontier: JsonDict) -> list[JsonDict]:
    shapes: list[JsonDict] = []
    seen: set[tuple[str, int, int, int]] = set()
    for row in frontier.get("focus_summary", []):
        if not isinstance(row, dict):
            continue
        key = (
            str(row.get("label") or ""),
            int(row.get("sequence_length", 0) or 0),
            int(row.get("hidden_size", 0) or 0),
            int(row.get("vocab_size", 0) or 0),
        )
        if not key[0] or key[1] <= 0 or key[2] <= 0 or key[3] <= 0 or key in seen:
            continue
        seen.add(key)
        shapes.append(row)
    return shapes


def _latency_row(
    *,
    shape: JsonDict,
    producer_lanes: int,
    macs_per_cycle: int,
    offchip_bw_bytes_per_cycle: float,
    local_cache_bw_bytes_per_cycle: float,
    cache_capacity_mb: float,
    target_cache_hit_rate: float,
    weight_bits: int,
    activation_bits: int,
    clock_ns: float,
) -> JsonDict:
    vocab_size = int(shape["vocab_size"])
    hidden_size = int(shape["hidden_size"])
    tile_count = _ceil_div(vocab_size, producer_lanes)
    weight_bytes_per_tile = producer_lanes * hidden_size * _byte_width(weight_bits)
    total_weight_bytes = tile_count * weight_bytes_per_tile
    hidden_bytes = hidden_size * _byte_width(activation_bits)
    macs_per_tile = producer_lanes * hidden_size
    cache_capacity_bytes = int(cache_capacity_mb * 1024 * 1024)
    capacity_limited_hit_rate = min(target_cache_hit_rate, cache_capacity_bytes / total_weight_bytes)
    capacity_limited_hit_rate = max(0.0, min(1.0, capacity_limited_hit_rate))
    offchip_weight_bytes_per_tile = weight_bytes_per_tile * (1.0 - capacity_limited_hit_rate)
    local_weight_bytes_per_tile = weight_bytes_per_tile * capacity_limited_hit_rate
    compute_cycles_per_tile = _ceil_div(macs_per_tile, macs_per_cycle)
    offchip_weight_cycles_per_tile = _ceil_div(offchip_weight_bytes_per_tile, offchip_bw_bytes_per_cycle)
    local_weight_cycles_per_tile = (
        _ceil_div(local_weight_bytes_per_tile, local_cache_bw_bytes_per_cycle)
        if local_weight_bytes_per_tile > 0.0
        else 0
    )
    parallel_weight_cycles_per_tile = max(offchip_weight_cycles_per_tile, local_weight_cycles_per_tile)
    serial_weight_cycles_per_tile = offchip_weight_cycles_per_tile + local_weight_cycles_per_tile
    hidden_load_cycles = _ceil_div(hidden_bytes, offchip_bw_bytes_per_cycle)
    producer_ii_parallel = max(compute_cycles_per_tile, parallel_weight_cycles_per_tile)
    producer_ii_serial = max(compute_cycles_per_tile, serial_weight_cycles_per_tile)
    producer_latency_cycles_parallel = hidden_load_cycles + compute_cycles_per_tile
    producer_latency_cycles_serial = hidden_load_cycles + compute_cycles_per_tile
    total_cycles_parallel = producer_latency_cycles_parallel + max(0, tile_count - 1) * producer_ii_parallel
    total_cycles_serial = producer_latency_cycles_serial + max(0, tile_count - 1) * producer_ii_serial
    return {
        "label": shape.get("label"),
        "sequence_length": shape.get("sequence_length"),
        "hidden_size": hidden_size,
        "vocab_size": vocab_size,
        "producer_lanes": producer_lanes,
        "tile_count": tile_count,
        "macs_per_cycle": macs_per_cycle,
        "offchip_bw_bytes_per_cycle": offchip_bw_bytes_per_cycle,
        "local_cache_bw_bytes_per_cycle": local_cache_bw_bytes_per_cycle,
        "cache_capacity_mb": cache_capacity_mb,
        "target_cache_hit_rate": target_cache_hit_rate,
        "effective_cache_hit_rate": round(capacity_limited_hit_rate, 6),
        "weight_bits": weight_bits,
        "activation_bits": activation_bits,
        "weight_bytes_per_tile": weight_bytes_per_tile,
        "weight_bytes_per_token": total_weight_bytes,
        "resident_weight_mb": round(total_weight_bytes / (1024 * 1024), 6),
        "cache_weight_mb": round(min(cache_capacity_bytes, total_weight_bytes) / (1024 * 1024), 6),
        "compute_cycles_per_tile": compute_cycles_per_tile,
        "offchip_weight_cycles_per_tile": offchip_weight_cycles_per_tile,
        "local_weight_cycles_per_tile": local_weight_cycles_per_tile,
        "parallel_weight_cycles_per_tile": parallel_weight_cycles_per_tile,
        "serial_weight_cycles_per_tile": serial_weight_cycles_per_tile,
        "producer_ii_cycles_parallel": producer_ii_parallel,
        "producer_ii_cycles_serial": producer_ii_serial,
        "producer_latency_us_parallel": round(total_cycles_parallel * clock_ns / 1000.0, 6),
        "producer_latency_us_serial": round(total_cycles_serial * clock_ns / 1000.0, 6),
        "parallel_limiter": (
            "compute_array" if compute_cycles_per_tile >= parallel_weight_cycles_per_tile else "weight_memory"
        ),
        "serial_limiter": (
            "compute_array" if compute_cycles_per_tile >= serial_weight_cycles_per_tile else "weight_memory"
        ),
    }


def _best(rows: list[JsonDict], key: str) -> JsonDict | None:
    return min(
        rows,
        key=lambda row: (
            float(row.get(key, float("inf"))),
            float(row.get("cache_capacity_mb", float("inf"))),
            int(row.get("producer_lanes", 10**9)),
        ),
        default=None,
    )


def build_report(
    *,
    frontier: JsonDict,
    calibration: JsonDict,
    producer_lanes_list: list[int],
    macs_per_cycle_list: list[int],
    offchip_bw_bytes_per_cycle_list: list[float],
    local_cache_bw_bytes_per_cycle_list: list[float],
    cache_capacity_mb_list: list[float],
    cache_hit_rate_list: list[float],
    weight_bits: int,
    activation_bits: int,
    clock_ns: float,
) -> JsonDict:
    baselines = _baseline_by_shape(calibration)
    rows: list[JsonDict] = []
    focus = _focus_shapes(frontier)
    for shape in focus:
        for lanes in producer_lanes_list:
            for macs in macs_per_cycle_list:
                for offchip_bw in offchip_bw_bytes_per_cycle_list:
                    for local_bw in local_cache_bw_bytes_per_cycle_list:
                        for cache_mb in cache_capacity_mb_list:
                            for hit_rate in cache_hit_rate_list:
                                rows.append(
                                    _latency_row(
                                        shape=shape,
                                        producer_lanes=lanes,
                                        macs_per_cycle=macs,
                                        offchip_bw_bytes_per_cycle=offchip_bw,
                                        local_cache_bw_bytes_per_cycle=local_bw,
                                        cache_capacity_mb=cache_mb,
                                        target_cache_hit_rate=hit_rate,
                                        weight_bits=weight_bits,
                                        activation_bits=activation_bits,
                                        clock_ns=clock_ns,
                                    )
                                )

    shape_summaries: list[JsonDict] = []
    for shape in focus:
        key = (int(shape["hidden_size"]), int(shape["vocab_size"]))
        shape_rows = [
            row
            for row in rows
            if int(row["hidden_size"]) == key[0] and int(row["vocab_size"]) == key[1]
        ]
        baseline = baselines.get(key)
        baseline_us = _producer_latency(baseline) if baseline else None
        best_parallel = _best(shape_rows, "producer_latency_us_parallel")
        best_serial = _best(shape_rows, "producer_latency_us_serial")
        compute_bound_rows = [row for row in shape_rows if row["parallel_limiter"] == "compute_array"]
        min_compute_bound_cache = _best(compute_bound_rows, "cache_capacity_mb")
        shape_summaries.append(
            {
                "label": shape.get("label"),
                "sequence_length": shape.get("sequence_length"),
                "hidden_size": key[0],
                "vocab_size": key[1],
                "baseline_producer_us": baseline_us,
                "baseline_choice": (
                    {
                        "producer_lanes": baseline.get("producer_lanes"),
                        "macs_per_cycle": baseline.get("macs_per_cycle"),
                        "producer_ii_cycles": baseline.get("producer_ii_cycles"),
                        "calibrated_ranker_latency_us_per_token": baseline.get(
                            "calibrated_ranker_latency_us_per_token"
                        ),
                    }
                    if baseline
                    else None
                ),
                "best_parallel": best_parallel,
                "best_serial": best_serial,
                "best_parallel_speedup_vs_baseline": (
                    round(baseline_us / best_parallel["producer_latency_us_parallel"], 6)
                    if baseline_us and best_parallel and best_parallel["producer_latency_us_parallel"] > 0
                    else None
                ),
                "best_serial_speedup_vs_baseline": (
                    round(baseline_us / best_serial["producer_latency_us_serial"], 6)
                    if baseline_us and best_serial and best_serial["producer_latency_us_serial"] > 0
                    else None
                ),
                "min_compute_bound_cache_parallel": min_compute_bound_cache,
            }
        )

    return {
        "version": 0.1,
        "model": "decoder_output_projection_producer_memory_hierarchy_v1",
        "inputs": {
            "frontier_model": frontier.get("model"),
            "calibration_model": calibration.get("model"),
            "producer_lanes_list": producer_lanes_list,
            "macs_per_cycle_list": macs_per_cycle_list,
            "offchip_bw_bytes_per_cycle_list": offchip_bw_bytes_per_cycle_list,
            "local_cache_bw_bytes_per_cycle_list": local_cache_bw_bytes_per_cycle_list,
            "cache_capacity_mb_list": cache_capacity_mb_list,
            "cache_hit_rate_list": cache_hit_rate_list,
            "weight_bits": weight_bits,
            "activation_bits": activation_bits,
            "clock_ns": clock_ns,
        },
        "summary": {
            "shape_count": len(focus),
            "row_count": len(rows),
            "best_parallel_global": _best(rows, "producer_latency_us_parallel"),
            "best_serial_global": _best(rows, "producer_latency_us_serial"),
        },
        "shape_summaries": shape_summaries,
        "memory_hierarchy_sweep": rows,
        "decision": {
            "decision": "producer_memory_hierarchy_estimated",
            "next_step": (
                "Use the cache-capacity and bandwidth boundary to decide whether to measure a resident/sharded "
                "weight-cache producer or to revisit the output-projection mapping."
            ),
        },
        "assumptions": [
            "This is an analytical producer service model; it does not include a routed SRAM/cache macro.",
            "Cache capacity constrains the effective weight hit rate by resident bytes divided by output-projection weight bytes.",
            "Parallel latency assumes local-cache hits and off-chip misses are served by independent paths; serial latency sums them conservatively.",
            "Hidden vector load is still charged once from off-chip memory.",
            "Ranker latency is excluded because the calibrated frontier showed measured r64/r128 ranker service is not dominant.",
        ],
    }


def write_markdown(path: str | Path, payload: JsonDict) -> None:
    lines = [
        "# Decoder Output-Projection Producer Memory Hierarchy",
        "",
        f"- model: `{payload['model']}`",
        f"- decision: `{payload['decision']['decision']}`",
        f"- row_count: `{payload['summary']['row_count']}`",
        "",
        "## Shape Summary",
        "",
        "| shape | seq | baseline_us | best_parallel_us | parallel_speedup | best_serial_us | serial_speedup | resident_weight_mb | best_cache_mb | best_hit | best_limiter |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in payload["shape_summaries"]:
        best = row.get("best_parallel") or {}
        serial = row.get("best_serial") or {}
        lines.append(
            "| {label} | {seq} | {base} | {best_us} | {speedup} | {serial_us} | {serial_speedup} | {resident} | {cache} | {hit} | {limiter} |".format(
                label=row.get("label"),
                seq=row.get("sequence_length"),
                base=row.get("baseline_producer_us"),
                best_us=best.get("producer_latency_us_parallel"),
                speedup=row.get("best_parallel_speedup_vs_baseline"),
                serial_us=serial.get("producer_latency_us_serial"),
                serial_speedup=row.get("best_serial_speedup_vs_baseline"),
                resident=best.get("resident_weight_mb"),
                cache=best.get("cache_capacity_mb"),
                hit=best.get("effective_cache_hit_rate"),
                limiter=best.get("parallel_limiter"),
            )
        )
    lines.extend(["", "## Assumptions", ""])
    for item in payload["assumptions"]:
        lines.append(f"- {item}")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--frontier", required=True)
    ap.add_argument("--calibration", required=True)
    ap.add_argument("--producer-lanes-list", type=_int_list, default=[64, 128, 256])
    ap.add_argument("--macs-per-cycle-list", type=_int_list, default=[32768, 65536, 131072])
    ap.add_argument("--offchip-bw-bytes-per-cycle-list", type=_float_list, default=[256.0, 1024.0, 4096.0])
    ap.add_argument("--local-cache-bw-bytes-per-cycle-list", type=_float_list, default=[1024.0, 4096.0, 16384.0])
    ap.add_argument("--cache-capacity-mb-list", type=_float_list, default=[0.0, 8.0, 32.0, 128.0, 256.0])
    ap.add_argument("--cache-hit-rate-list", type=_float_list, default=[0.0, 0.5, 0.9, 0.99, 1.0])
    ap.add_argument("--weight-bits", type=int, default=16)
    ap.add_argument("--activation-bits", type=int, default=16)
    ap.add_argument("--clock-ns", type=float, default=1.0)
    ap.add_argument("--out", required=True)
    ap.add_argument("--out-md", required=True)
    args = ap.parse_args()
    payload = build_report(
        frontier=_load_json(args.frontier),
        calibration=_load_json(args.calibration),
        producer_lanes_list=args.producer_lanes_list,
        macs_per_cycle_list=args.macs_per_cycle_list,
        offchip_bw_bytes_per_cycle_list=args.offchip_bw_bytes_per_cycle_list,
        local_cache_bw_bytes_per_cycle_list=args.local_cache_bw_bytes_per_cycle_list,
        cache_capacity_mb_list=args.cache_capacity_mb_list,
        cache_hit_rate_list=args.cache_hit_rate_list,
        weight_bits=args.weight_bits,
        activation_bits=args.activation_bits,
        clock_ns=args.clock_ns,
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(args.out_md, payload)
    print(json.dumps({"ok": True, "out": str(out), "out_md": args.out_md}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
