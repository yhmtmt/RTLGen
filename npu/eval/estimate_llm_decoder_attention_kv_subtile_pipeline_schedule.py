#!/usr/bin/env python3
"""Estimate sub-tile pipelined QK/softmax/V schedules for the Llama7B attention frontier."""

from __future__ import annotations

import argparse
import heapq
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

JsonDict = dict[str, Any]


def _int_list(value: str) -> list[int]:
    items = [int(item.strip()) for item in value.split(",") if item.strip()]
    if not items or any(item <= 0 for item in items):
        raise argparse.ArgumentTypeError("expected comma-separated positive integers")
    return items


def _nonnegative_int_list(value: str) -> list[int]:
    items = [int(item.strip()) for item in value.split(",") if item.strip()]
    if not items or any(item < 0 for item in items):
        raise argparse.ArgumentTypeError("expected comma-separated nonnegative integers")
    return items


def _str_list(value: str) -> list[str]:
    items = [item.strip() for item in value.split(",") if item.strip()]
    if not items:
        raise argparse.ArgumentTypeError("expected comma-separated names")
    return items


def _ceil_div(numerator: int | float, denominator: int | float) -> int:
    if numerator <= 0:
        return 0
    return int(math.ceil(float(numerator) / max(1.0, float(denominator))))


def _load_json(path: Path) -> JsonDict:
    return json.loads(path.read_text(encoding="utf-8"))


def _source_rows(payload: JsonDict, *, limit: int) -> list[JsonDict]:
    rows = list(payload.get("top_rows") or [])
    if not rows and isinstance(payload.get("best"), dict):
        rows = [payload["best"]]
    deduped: list[JsonDict] = []
    seen: set[str] = set()
    for row in rows:
        key = json.dumps(
            {
                "latency_us": row.get("latency_us"),
                "cluster_count": row.get("cluster_count"),
                "active_clusters": row.get("active_clusters"),
                "tile_hbm_cycles": row.get("tile_hbm_cycles"),
                "tile_attention_cycles": row.get("tile_attention_cycles"),
                "tile_qk_cycles": row.get("tile_qk_cycles"),
                "tile_stats_cycles": row.get("tile_stats_cycles"),
                "tile_value_cycles": row.get("tile_value_cycles"),
                "schedule_policy": row.get("schedule_policy"),
                "bank_arbiter_policy": row.get("bank_arbiter_policy"),
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


def _compute_stage_cycles(row: JsonDict, *, subtiles: int, compute_mode: str) -> tuple[int, int]:
    qk_base = int(row["tile_qk_cycles"])
    value_base = int(row["tile_value_cycles"])
    if compute_mode == "shared_mac":
        scale = 1.0
    elif compute_mode == "split_mac":
        scale = 2.0
    elif compute_mode == "dual_mac":
        scale = 1.0
    else:
        raise ValueError(f"unknown compute mode: {compute_mode}")
    return _ceil_div(qk_base * scale, subtiles), _ceil_div(value_base * scale, subtiles)


def _subtile_buffer_bytes(row: JsonDict, *, subtiles: int, buffer_count: int, prefetch_distance: int) -> int:
    full_tile_bytes = int(row.get("onchip_full_tile_bytes", row.get("tile_hbm_bytes", 0)))
    subtile_payload = _ceil_div(full_tile_bytes, subtiles)
    hidden_size = int(row.get("hidden_size", 4096))
    attention_heads = int(row.get("attention_heads", 32))
    scalar_bytes = 2
    stats_bytes = attention_heads * 2 * scalar_bytes
    partial_value_bytes = hidden_size * scalar_bytes
    live_buffers = max(buffer_count, prefetch_distance + 1)
    return live_buffers * subtile_payload + stats_bytes + partial_value_bytes


def _scheduled_pipeline(
    row: JsonDict,
    *,
    subtiles: int,
    buffer_count: int,
    prefetch_distance: int,
    normalize_strategy: str,
    compute_mode: str,
    softmax_latency_per_subtile: int,
    online_rescale_penalty_cycles: int,
) -> JsonDict:
    qk_sub, value_sub = _compute_stage_cycles(row, subtiles=subtiles, compute_mode=compute_mode)
    stats_sub = _ceil_div(int(row["tile_stats_cycles"]), subtiles) + softmax_latency_per_subtile
    hbm_sub = _ceil_div(int(row["tile_hbm_cycles"]), subtiles)
    local_sub = _ceil_div(int(row.get("tile_local_sram_cycles", 0)), subtiles)
    shared_sub = _ceil_div(int(row.get("tile_shared_path_cycles", 0)), subtiles)
    memory_aux_sub = max(local_sub, shared_sub)

    buffer_bytes = _subtile_buffer_bytes(
        row,
        subtiles=subtiles,
        buffer_count=buffer_count,
        prefetch_distance=prefetch_distance,
    )
    local_capacity = int(row.get("local_capacity_bytes_per_cluster", row.get("tile_local_buffer_bytes", 0)))
    legal = buffer_bytes <= local_capacity and prefetch_distance < buffer_count
    if normalize_strategy == "online_correction" and subtiles < 2:
        legal = False

    hbm_end = [max(0, index + 1 - prefetch_distance) * hbm_sub for index in range(subtiles)]
    qk_end: list[int] = []
    stats_end: list[int] = []
    value_end: list[int] = []
    shared_gemm_free = 0
    qk_free = 0
    value_free = 0
    stats_free = 0

    for index in range(subtiles):
        # A prefetch distance of N means the scheduler tries to keep N later blocks in flight,
        # but a block still cannot compute before its own payload has arrived.
        qk_start = max(qk_free, hbm_end[index], index * memory_aux_sub)
        if compute_mode == "shared_mac":
            qk_start = max(qk_start, shared_gemm_free)
        qk_done = qk_start + qk_sub
        qk_end.append(qk_done)
        qk_free = qk_done
        if compute_mode == "shared_mac":
            shared_gemm_free = qk_done

        stats_start = max(stats_free, qk_done)
        stats_done = stats_start + stats_sub
        stats_end.append(stats_done)
        stats_free = stats_done

        if normalize_strategy == "full_tile_normalize":
            continue
        value_start = max(value_free, stats_done + online_rescale_penalty_cycles, hbm_end[index])
        if compute_mode == "shared_mac":
            value_start = max(value_start, shared_gemm_free)
        value_done = value_start + value_sub
        value_end.append(value_done)
        value_free = value_done
        if compute_mode == "shared_mac":
            shared_gemm_free = value_done

    if normalize_strategy == "full_tile_normalize":
        all_stats_done = stats_end[-1]
        for index in range(subtiles):
            value_start = max(value_free, all_stats_done, hbm_end[index])
            if compute_mode == "shared_mac":
                value_start = max(value_start, shared_gemm_free)
            value_done = value_start + value_sub
            value_end.append(value_done)
            value_free = value_done
            if compute_mode == "shared_mac":
                shared_gemm_free = value_done
    elif normalize_strategy != "online_correction":
        raise ValueError(f"unknown normalize strategy: {normalize_strategy}")

    hbm_exposed_cycles = hbm_end[-1]
    pipeline_cycles = max(value_end[-1], hbm_exposed_cycles, subtiles * memory_aux_sub)
    residual_memory_cycles = max(int(row.get("tile_local_sram_cycles", 0)), int(row.get("tile_shared_path_cycles", 0)))
    tile_service_cycles = max(pipeline_cycles, residual_memory_cycles)
    layer_cycles = (
        int(row["qkv_cycles"])
        + int(row["tile_waves"]) * tile_service_cycles
        + int(row.get("command_dispatch_cycles", 0))
        + int(row["cross_tile_reduction_cycles"])
        + int(row["kv_write_cycles"])
    )
    total_cycles = layer_cycles * int(row["layers"])
    clock_ns = float(row["clock_ns"])
    latency_us = round(total_cycles * clock_ns / 1000.0, 6)
    compute_area_multiplier = {
        "shared_mac": 1.0,
        "split_mac": 1.0,
        "dual_mac": 2.0,
    }[compute_mode]
    dominant = max(
        {
            "pipeline_attention": pipeline_cycles,
            "hbm_exposed": hbm_exposed_cycles,
            "local_sram": int(row.get("tile_local_sram_cycles", 0)),
            "shared_path": int(row.get("tile_shared_path_cycles", 0)),
            "cross_tile_reduction": int(row["cross_tile_reduction_cycles"]),
        }.items(),
        key=lambda item: item[1],
    )[0]
    out = dict(row)
    out.update(
        {
            "subtile_pipeline_model": "qk_softmax_value_streaming_v1",
            "subtile_count": subtiles,
            "subtile_buffer_count": buffer_count,
            "prefetch_distance": prefetch_distance,
            "normalize_strategy": normalize_strategy,
            "compute_mode": compute_mode,
            "compute_area_multiplier": compute_area_multiplier,
            "softmax_latency_per_subtile": softmax_latency_per_subtile,
            "online_rescale_penalty_cycles": online_rescale_penalty_cycles,
            "subtile_qk_cycles": qk_sub,
            "subtile_stats_cycles": stats_sub,
            "subtile_value_cycles": value_sub,
            "subtile_hbm_cycles": hbm_sub,
            "hbm_exposed_cycles": hbm_exposed_cycles,
            "subtile_aux_memory_cycles": memory_aux_sub,
            "required_stream_buffer_bytes": buffer_bytes,
            "available_local_capacity_bytes": local_capacity,
            "schedule_legal": legal,
            "pipeline_attention_cycles": pipeline_cycles,
            "pipeline_residual_memory_cycles": residual_memory_cycles,
            "tile_attention_cycles": pipeline_cycles,
            "tile_service_cycles": tile_service_cycles,
            "tile_memory_cycles": max(int(row["tile_hbm_cycles"]), residual_memory_cycles),
            "layer_cycles": layer_cycles,
            "total_cycles": total_cycles,
            "latency_us": latency_us,
            "dominant_tile_resource": dominant,
            "latency_speedup_vs_hbm_closed_source": round(float(row["latency_us"]) / max(1e-9, latency_us), 6),
            "tile_service_speedup_vs_source": round(
                float(row["tile_service_cycles"]) / max(1.0, float(tile_service_cycles)),
                6,
            ),
            "hbm_floor_gap_cycles": tile_service_cycles - int(row["tile_hbm_cycles"]),
        }
    )
    return out


def _push_top(heap: list[tuple[float, int, JsonDict]], row: JsonDict, *, counter: int, limit: int) -> None:
    entry = (-float(row["latency_us"]), counter, row)
    if len(heap) < limit:
        heapq.heappush(heap, entry)
    elif entry[0] > heap[0][0]:
        heapq.heapreplace(heap, entry)


def _best_update(target: dict[tuple[Any, ...], JsonDict], keys: tuple[str, ...], row: JsonDict) -> None:
    key = tuple(row.get(item) for item in keys)
    current = target.get(key)
    if current is None or float(row["latency_us"]) < float(current["latency_us"]):
        target[key] = row


def build_report(args: argparse.Namespace) -> JsonDict:
    source = _load_json(args.hbm_closed_onchip_schedule_json)
    source_rows = _source_rows(source, limit=args.frontier_row_limit)
    if not source_rows:
        raise RuntimeError("no HBM-closed on-chip source rows found")

    generated = 0
    legal_count = 0
    best: JsonDict | None = None
    heap_counter = 0
    top_heap: list[tuple[float, int, JsonDict]] = []
    dominance = Counter()
    legal_by_mode = Counter()
    best_by_compute_mode: dict[tuple[Any, ...], JsonDict] = {}
    best_by_normalize_strategy: dict[tuple[Any, ...], JsonDict] = {}
    best_by_subtile_count: dict[tuple[Any, ...], JsonDict] = {}

    for source_row in source_rows:
        for subtiles in args.subtile_count:
            if subtiles > int(source_row["tile_tokens"]):
                continue
            for buffer_count in args.subtile_buffer_count:
                for prefetch_distance in args.prefetch_distance:
                    for normalize_strategy in args.normalize_strategy:
                        for compute_mode in args.compute_mode:
                            for softmax_latency in args.softmax_latency_per_subtile:
                                for online_penalty in args.online_rescale_penalty_cycles:
                                    row = _scheduled_pipeline(
                                        source_row,
                                        subtiles=subtiles,
                                        buffer_count=buffer_count,
                                        prefetch_distance=prefetch_distance,
                                        normalize_strategy=normalize_strategy,
                                        compute_mode=compute_mode,
                                        softmax_latency_per_subtile=softmax_latency,
                                        online_rescale_penalty_cycles=online_penalty,
                                    )
                                    generated += 1
                                    if not bool(row["schedule_legal"]):
                                        continue
                                    legal_count += 1
                                    dominance[str(row["dominant_tile_resource"])] += 1
                                    legal_by_mode[str(row["compute_mode"])] += 1
                                    if best is None or float(row["latency_us"]) < float(best["latency_us"]):
                                        best = row
                                    _push_top(top_heap, row, counter=heap_counter, limit=args.top_k)
                                    heap_counter += 1
                                    _best_update(best_by_compute_mode, ("compute_mode",), row)
                                    _best_update(best_by_normalize_strategy, ("normalize_strategy", "compute_mode"), row)
                                    _best_update(best_by_subtile_count, ("subtile_count", "compute_mode"), row)

    if best is None:
        raise RuntimeError("no legal sub-tile pipeline schedule rows generated")
    top_rows = [entry[2] for entry in sorted(top_heap, key=lambda entry: (entry[2]["latency_us"], entry[1]))]
    return {
        "version": 1,
        "model": "llm_decoder_attention_kv_subtile_pipeline_schedule_llama7b_v1",
        "hbm_closed_onchip_schedule_json": str(args.hbm_closed_onchip_schedule_json),
        "source_model": source.get("model"),
        "inputs": {
            "frontier_row_limit": args.frontier_row_limit,
            "subtile_count": args.subtile_count,
            "subtile_buffer_count": args.subtile_buffer_count,
            "prefetch_distance": args.prefetch_distance,
            "normalize_strategy": args.normalize_strategy,
            "compute_mode": args.compute_mode,
            "softmax_latency_per_subtile": args.softmax_latency_per_subtile,
            "online_rescale_penalty_cycles": args.online_rescale_penalty_cycles,
        },
        "sweep_summary": {
            "source_rows_used": len(source_rows),
            "generated_row_count": generated,
            "legal_row_count": legal_count,
            "dominant_tile_resource_counts": dict(sorted(dominance.items())),
            "legal_compute_mode_counts": dict(sorted(legal_by_mode.items())),
            "best_latency_us": best["latency_us"],
            "best_latency_speedup_vs_hbm_closed_source": best["latency_speedup_vs_hbm_closed_source"],
            "best_tile_service_cycles": best["tile_service_cycles"],
            "best_hbm_floor_gap_cycles": best["hbm_floor_gap_cycles"],
            "best_compute_mode": best["compute_mode"],
            "best_normalize_strategy": best["normalize_strategy"],
        },
        "best": best,
        "top_rows": top_rows,
        "best_by_compute_mode": sorted(best_by_compute_mode.values(), key=lambda row: row["latency_us"])[:100],
        "best_by_normalize_strategy": sorted(
            best_by_normalize_strategy.values(),
            key=lambda row: row["latency_us"],
        )[:100],
        "best_by_subtile_count": sorted(best_by_subtile_count.values(), key=lambda row: row["latency_us"])[:100],
        "assumptions": [
            "The source row is the measured-SRAM, measured-HBM, HBM-closed on-chip schedule frontier.",
            "shared_mac keeps QK and V on one measured MAC resource; split_mac partitions the same resource; dual_mac models independent QK and V streams and therefore carries a compute_area_multiplier of 2.",
            "full_tile_normalize requires all subtile stats before V starts; online_correction allows V to stream after each subtile stats result with an explicit rescale penalty.",
            "A row is legal only if the required stream buffer fits local capacity and prefetch_distance is less than the available subtile buffer count.",
            "This is a scheduling feasibility model, not RTL or PPA for the pipelined datapath.",
        ],
    }


def write_markdown(path: Path, payload: JsonDict) -> None:
    best = payload["best"]
    lines = [
        "# Llama7B Sub-Tile Pipelined Attention Schedule",
        "",
        f"- source rows used: `{payload['sweep_summary']['source_rows_used']}`",
        f"- generated rows: `{payload['sweep_summary']['generated_row_count']}`",
        f"- legal rows: `{payload['sweep_summary']['legal_row_count']}`",
        f"- dominant resources: `{payload['sweep_summary']['dominant_tile_resource_counts']}`",
        "",
        "## Best",
        "",
        "| latency us | speedup | tile service | resource | mode | normalize | subtiles | buffers | prefetch | softmax/sub | rescale | area mult | hbm gap | req buffer |",
        "|---:|---:|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        "| {latency_us} | {latency_speedup_vs_hbm_closed_source} | {tile_service_cycles} | "
        "{dominant_tile_resource} | {compute_mode} | {normalize_strategy} | {subtile_count} | "
        "{subtile_buffer_count} | {prefetch_distance} | {softmax_latency_per_subtile} | "
        "{online_rescale_penalty_cycles} | {compute_area_multiplier} | {hbm_floor_gap_cycles} | "
        "{required_stream_buffer_bytes} |".format(**best),
        "",
        "## Best By Compute Mode",
        "",
        "| mode | latency us | speedup | tile service | resource | normalize | subtiles | area mult | hbm gap |",
        "|---|---:|---:|---:|---|---|---:|---:|---:|",
    ]
    for row in payload["best_by_compute_mode"]:
        lines.append(
            "| {compute_mode} | {latency_us} | {latency_speedup_vs_hbm_closed_source} | "
            "{tile_service_cycles} | {dominant_tile_resource} | {normalize_strategy} | "
            "{subtile_count} | {compute_area_multiplier} | {hbm_floor_gap_cycles} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Best By Normalize Strategy",
            "",
            "| normalize | mode | latency us | speedup | tile service | subtiles | softmax/sub | rescale |",
            "|---|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in payload["best_by_normalize_strategy"]:
        lines.append(
            "| {normalize_strategy} | {compute_mode} | {latency_us} | "
            "{latency_speedup_vs_hbm_closed_source} | {tile_service_cycles} | {subtile_count} | "
            "{softmax_latency_per_subtile} | {online_rescale_penalty_cycles} |".format(**row)
        )
    lines.extend(["", "## Assumptions", ""])
    lines.extend(f"- {item}" for item in payload["assumptions"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hbm-closed-onchip-schedule-json", type=Path, required=True)
    parser.add_argument("--frontier-row-limit", type=int, default=48)
    parser.add_argument("--subtile-count", type=_int_list, default=[1, 2, 4, 8, 16, 32])
    parser.add_argument("--subtile-buffer-count", type=_int_list, default=[1, 2, 3, 4])
    parser.add_argument("--prefetch-distance", type=_nonnegative_int_list, default=[0, 1, 2, 3])
    parser.add_argument("--normalize-strategy", type=_str_list, default=["full_tile_normalize", "online_correction"])
    parser.add_argument("--compute-mode", type=_str_list, default=["shared_mac", "split_mac", "dual_mac"])
    parser.add_argument("--softmax-latency-per-subtile", type=_nonnegative_int_list, default=[0, 1, 2, 4])
    parser.add_argument("--online-rescale-penalty-cycles", type=_nonnegative_int_list, default=[0, 1, 2, 4])
    parser.add_argument("--top-k", type=int, default=50)
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
