#!/usr/bin/env python3
"""Estimate HBM-controller realism for the llama7B attention/KV spill point."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

try:
    from npu.eval.estimate_llm_decoder_attention_kv_spill_scheduler import _find_baseline_row, _simulate_layer
except ModuleNotFoundError:
    from estimate_llm_decoder_attention_kv_spill_scheduler import _find_baseline_row, _simulate_layer

JsonDict = dict[str, Any]


def _int_list(value: str) -> list[int]:
    items = [int(item.strip()) for item in value.split(",") if item.strip()]
    if not items or any(item <= 0 for item in items):
        raise argparse.ArgumentTypeError("expected comma-separated positive integers")
    return items


def _float_list(value: str) -> list[float]:
    items = [float(item.strip()) for item in value.split(",") if item.strip()]
    if not items or any(item <= 0.0 for item in items):
        raise argparse.ArgumentTypeError("expected comma-separated positive floats")
    return items


def _str_list(value: str) -> list[str]:
    items = [item.strip() for item in value.split(",") if item.strip()]
    if not items:
        raise argparse.ArgumentTypeError("expected comma-separated strings")
    return items


def _byte_width(bits: int) -> int:
    return max(1, math.ceil(bits / 8))


def _ceil_div(a: int | float, b: int | float) -> int:
    return int(math.ceil(a / b)) if a else 0


def _tile_hbm_bytes(*, baseline_row: JsonDict, tile_tokens: int) -> float:
    hidden_size = int(baseline_row["hidden_size"])
    attention_heads = int(baseline_row["attention_heads"])
    kv_heads = int(baseline_row["kv_heads"])
    kv_bits = int(baseline_row["kv_bits"])
    head_dim = hidden_size // attention_heads
    kv_width = kv_heads * head_dim
    kv_cache_bytes = int(baseline_row["kv_cache_bytes"])
    hbm_read_share = float(baseline_row.get("hbm_bytes", 0)) / kv_cache_bytes if kv_cache_bytes else 0.0
    return 2 * tile_tokens * kv_width * _byte_width(kv_bits) * hbm_read_share


def _controller_effective_bw(
    *,
    tile_hbm_bytes: float,
    channel_count: int,
    channel_bandwidth_bytes_per_cycle: float,
    burst_bytes: int,
    request_overhead_cycles: int,
    row_hit_rate: float,
    row_miss_penalty_cycles: int,
    scheduler_efficiency: float,
) -> JsonDict:
    payload_bw = channel_count * channel_bandwidth_bytes_per_cycle * scheduler_efficiency
    payload_cycles = _ceil_div(tile_hbm_bytes, payload_bw)
    burst_count = _ceil_div(tile_hbm_bytes, burst_bytes)
    overhead_cycles = burst_count * request_overhead_cycles
    row_miss_cycles = math.ceil(burst_count * (1.0 - row_hit_rate) * row_miss_penalty_cycles)
    service_cycles = max(1, payload_cycles + overhead_cycles + row_miss_cycles)
    effective_bw = tile_hbm_bytes / service_cycles if service_cycles else 0.0
    return {
        "tile_hbm_bytes": int(tile_hbm_bytes),
        "payload_cycles": payload_cycles,
        "burst_count": burst_count,
        "overhead_cycles": overhead_cycles,
        "row_miss_cycles": row_miss_cycles,
        "service_cycles": service_cycles,
        "effective_hbm_bytes_per_cycle": round(effective_bw, 6),
    }


def build_report(
    *,
    capacity_noc_baseline: JsonDict,
    label: str,
    sequence_length: int,
    die_area_mm2: float,
    tile_tokens_list: list[int],
    prefetch_distance_tiles_list: list[int],
    channel_count_list: list[int],
    channel_bandwidth_bytes_per_cycle_list: list[float],
    burst_bytes_list: list[int],
    hbm_outstanding_list: list[int],
    request_overhead_cycles_list: list[int],
    row_hit_rate_list: list[float],
    row_miss_penalty_cycles_list: list[int],
    scheduler_efficiency_list: list[float],
    arbitration_efficiency_list: list[float],
    virtual_channel_list: list[int],
    prefetch_start_list: list[str],
    bank_interleave_tokens: int,
    bank_conflict_efficiency: float,
    router_latency_cycles_per_hop: int,
    macs_per_cycle: int,
    vector_ops_per_cycle: int,
    clock_ns: float,
) -> JsonDict:
    baseline_row = _find_baseline_row(
        capacity_noc_baseline=capacity_noc_baseline,
        label=label,
        sequence_length=sequence_length,
        die_area_mm2=die_area_mm2,
    )
    baseline_hbm_bw = float(baseline_row["hbm_bandwidth_bytes_per_cycle"])
    layers = int(baseline_row["layers"])
    rows: list[JsonDict] = []
    for tile_tokens in tile_tokens_list:
        tile_hbm_bytes = _tile_hbm_bytes(baseline_row=baseline_row, tile_tokens=tile_tokens)
        for channel_count in channel_count_list:
            for channel_bw in channel_bandwidth_bytes_per_cycle_list:
                for burst_bytes in burst_bytes_list:
                    for request_overhead in request_overhead_cycles_list:
                        for row_hit_rate in row_hit_rate_list:
                            for row_miss_penalty in row_miss_penalty_cycles_list:
                                for scheduler_efficiency in scheduler_efficiency_list:
                                    hbm_service = _controller_effective_bw(
                                        tile_hbm_bytes=tile_hbm_bytes,
                                        channel_count=channel_count,
                                        channel_bandwidth_bytes_per_cycle=channel_bw,
                                        burst_bytes=burst_bytes,
                                        request_overhead_cycles=request_overhead,
                                        row_hit_rate=row_hit_rate,
                                        row_miss_penalty_cycles=row_miss_penalty,
                                        scheduler_efficiency=scheduler_efficiency,
                                    )
                                    hbm_efficiency = min(
                                        1.0,
                                        max(0.01, hbm_service["effective_hbm_bytes_per_cycle"] / baseline_hbm_bw),
                                    )
                                    for hbm_outstanding in hbm_outstanding_list:
                                        for prefetch_distance in prefetch_distance_tiles_list:
                                            for arbitration_efficiency in arbitration_efficiency_list:
                                                for virtual_channels in virtual_channel_list:
                                                    for prefetch_start in prefetch_start_list:
                                                        layer = _simulate_layer(
                                                            baseline_row=baseline_row,
                                                            tile_tokens=tile_tokens,
                                                            prefetch_distance_tiles=prefetch_distance,
                                                            hbm_outstanding=hbm_outstanding,
                                                            hbm_efficiency=hbm_efficiency,
                                                            arbitration_efficiency=arbitration_efficiency,
                                                            virtual_channels=virtual_channels,
                                                            bank_interleave_tokens=bank_interleave_tokens,
                                                            bank_conflict_efficiency=bank_conflict_efficiency,
                                                            router_latency_cycles_per_hop=router_latency_cycles_per_hop,
                                                            prefetch_start=prefetch_start,
                                                            macs_per_cycle=macs_per_cycle,
                                                            vector_ops_per_cycle=vector_ops_per_cycle,
                                                        )
                                                        total_cycles = layer["layer_cycles"] * layers
                                                        rows.append(
                                                            {
                                                                "label": label,
                                                                "sequence_length": sequence_length,
                                                                "die_area_mm2": die_area_mm2,
                                                                "placement": baseline_row["placement"],
                                                                "kv_sharing": baseline_row["kv_sharing"],
                                                                "kv_bits": baseline_row["kv_bits"],
                                                                "kv_cache_mib": baseline_row["kv_cache_mib"],
                                                                "hbm_byte_share": baseline_row["hbm_byte_share"],
                                                                "tile_tokens": tile_tokens,
                                                                "prefetch_distance_tiles": prefetch_distance,
                                                                "hbm_outstanding": hbm_outstanding,
                                                                "channel_count": channel_count,
                                                                "channel_bandwidth_bytes_per_cycle": channel_bw,
                                                                "burst_bytes": burst_bytes,
                                                                "request_overhead_cycles": request_overhead,
                                                                "row_hit_rate": row_hit_rate,
                                                                "row_miss_penalty_cycles": row_miss_penalty,
                                                                "scheduler_efficiency": scheduler_efficiency,
                                                                "derived_hbm_efficiency": round(hbm_efficiency, 6),
                                                                "arbitration_efficiency": arbitration_efficiency,
                                                                "virtual_channels": virtual_channels,
                                                                "prefetch_start": prefetch_start,
                                                                "total_cycles": total_cycles,
                                                                "latency_us": round(total_cycles * clock_ns / 1000.0, 6),
                                                                **hbm_service,
                                                                **layer,
                                                            }
                                                        )

    rows_sorted = sorted(rows, key=lambda row: row["latency_us"])
    best = rows_sorted[0]
    dominance: dict[str, int] = {}
    for row in rows:
        key = str(row["dominant_tile_resource"])
        dominance[key] = dominance.get(key, 0) + 1
    return {
        "version": 0.1,
        "model": "llm_decoder_attention_kv_hbm_controller_llama7b_131k_v1",
        "inputs": {
            "capacity_noc_model": capacity_noc_baseline.get("model"),
            "selected_point": {
                "label": label,
                "sequence_length": sequence_length,
                "die_area_mm2": die_area_mm2,
            },
            "tile_tokens_list": tile_tokens_list,
            "prefetch_distance_tiles_list": prefetch_distance_tiles_list,
            "channel_count_list": channel_count_list,
            "channel_bandwidth_bytes_per_cycle_list": channel_bandwidth_bytes_per_cycle_list,
            "burst_bytes_list": burst_bytes_list,
            "hbm_outstanding_list": hbm_outstanding_list,
            "request_overhead_cycles_list": request_overhead_cycles_list,
            "row_hit_rate_list": row_hit_rate_list,
            "row_miss_penalty_cycles_list": row_miss_penalty_cycles_list,
            "scheduler_efficiency_list": scheduler_efficiency_list,
            "arbitration_efficiency_list": arbitration_efficiency_list,
            "virtual_channel_list": virtual_channel_list,
            "prefetch_start_list": prefetch_start_list,
            "bank_interleave_tokens": bank_interleave_tokens,
            "bank_conflict_efficiency": bank_conflict_efficiency,
            "router_latency_cycles_per_hop": router_latency_cycles_per_hop,
            "macs_per_cycle": macs_per_cycle,
            "vector_ops_per_cycle": vector_ops_per_cycle,
            "clock_ns": clock_ns,
        },
        "sweep_summary": {
            "generated_row_count": len(rows),
            "retained_top_row_count": min(50, len(rows_sorted)),
            "dominant_tile_resource_counts": dominance,
        },
        "best": best,
        "top_rows": rows_sorted[:50],
        "assumptions": [
            "This is an HBM-controller service model layered onto the llama7B 131k spill scheduler.",
            "Effective HBM service is derived from channels, per-channel bandwidth, burst size, command overhead, row-hit rate, row-miss penalty, and scheduler efficiency.",
            "The derived HBM bandwidth replaces the previous scalar HBM efficiency before running the tile-level spill scheduler.",
            "NoC/shared-SRAM service still uses the compact bank and arbitration model from the spill scheduler.",
            "This is not a DRAM timing model; it is intended to bound whether the assumed HBM efficiency is physically plausible.",
        ],
    }


def _write_markdown(path: Path, payload: JsonDict) -> None:
    best = payload["best"]
    lines = [
        "# Decoder Attention/KV HBM Controller Realism",
        "",
        f"- model: `{payload['model']}`",
        f"- generated_row_count: `{payload['sweep_summary']['generated_row_count']}`",
        f"- selected_point: `{best['label']} seq={best['sequence_length']} die={best['die_area_mm2']}mm2`",
        "",
        "## Best",
        "",
        "| tile | channels | ch_B/cyc | burst | out | row_hit | sched_eff | hbm_eff | latency_us | resource | hbm_service_cyc |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|",
        "| {tile} | {channels} | {ch_bw} | {burst} | {out} | {row_hit} | {sched} | {hbm_eff} | {lat} | {res} | {service} |".format(
            tile=best["tile_tokens"],
            channels=best["channel_count"],
            ch_bw=best["channel_bandwidth_bytes_per_cycle"],
            burst=best["burst_bytes"],
            out=best["hbm_outstanding"],
            row_hit=best["row_hit_rate"],
            sched=best["scheduler_efficiency"],
            hbm_eff=best["derived_hbm_efficiency"],
            lat=best["latency_us"],
            res=best["dominant_tile_resource"],
            service=best["service_cycles"],
        ),
        "",
        "## Top 10",
        "",
        "| rank | tile | channels | burst | out | row_hit | sched_eff | hbm_eff | latency_us | resource |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for index, row in enumerate(payload["top_rows"][:10], start=1):
        lines.append(
            "| {rank} | {tile} | {channels} | {burst} | {out} | {row_hit} | {sched} | {hbm_eff} | {lat} | {res} |".format(
                rank=index,
                tile=row["tile_tokens"],
                channels=row["channel_count"],
                burst=row["burst_bytes"],
                out=row["hbm_outstanding"],
                row_hit=row["row_hit_rate"],
                sched=row["scheduler_efficiency"],
                hbm_eff=row["derived_hbm_efficiency"],
                lat=row["latency_us"],
                res=row["dominant_tile_resource"],
            )
        )
    lines.extend(["", "## Assumptions", ""])
    lines.extend(f"- {item}" for item in payload["assumptions"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--capacity-noc-baseline", required=True)
    ap.add_argument("--label", default="llama7b_proxy")
    ap.add_argument("--sequence-length", type=int, default=131072)
    ap.add_argument("--die-area-mm2", type=float, default=400.0)
    ap.add_argument("--tile-tokens-list", type=_int_list, default=[1024, 2048, 4096])
    ap.add_argument("--prefetch-distance-tiles-list", type=_int_list, default=[2, 4, 8, 16])
    ap.add_argument("--channel-count-list", type=_int_list, default=[4, 8, 16])
    ap.add_argument("--channel-bandwidth-bytes-per-cycle-list", type=_float_list, default=[128, 256, 512])
    ap.add_argument("--burst-bytes-list", type=_int_list, default=[256, 512, 1024])
    ap.add_argument("--hbm-outstanding-list", type=_int_list, default=[2, 4, 8, 16])
    ap.add_argument("--request-overhead-cycles-list", type=_int_list, default=[4, 8, 16])
    ap.add_argument("--row-hit-rate-list", type=_float_list, default=[0.5, 0.75, 0.9])
    ap.add_argument("--row-miss-penalty-cycles-list", type=_int_list, default=[16, 32, 64])
    ap.add_argument("--scheduler-efficiency-list", type=_float_list, default=[0.6, 0.75, 0.9])
    ap.add_argument("--arbitration-efficiency-list", type=_float_list, default=[0.7, 0.85])
    ap.add_argument("--virtual-channel-list", type=_int_list, default=[2, 4])
    ap.add_argument("--prefetch-start-list", type=_str_list, default=["during_qkv"])
    ap.add_argument("--bank-interleave-tokens", type=int, default=16)
    ap.add_argument("--bank-conflict-efficiency", type=float, default=0.75)
    ap.add_argument("--router-latency-cycles-per-hop", type=int, default=2)
    ap.add_argument("--macs-per-cycle", type=int, default=524288)
    ap.add_argument("--vector-ops-per-cycle", type=int, default=65536)
    ap.add_argument("--clock-ns", type=float, default=1.0)
    ap.add_argument("--out", required=True)
    ap.add_argument("--out-md", required=True)
    args = ap.parse_args()

    baseline = json.loads(Path(args.capacity_noc_baseline).read_text(encoding="utf-8"))
    payload = build_report(
        capacity_noc_baseline=baseline,
        label=args.label,
        sequence_length=args.sequence_length,
        die_area_mm2=args.die_area_mm2,
        tile_tokens_list=args.tile_tokens_list,
        prefetch_distance_tiles_list=args.prefetch_distance_tiles_list,
        channel_count_list=args.channel_count_list,
        channel_bandwidth_bytes_per_cycle_list=args.channel_bandwidth_bytes_per_cycle_list,
        burst_bytes_list=args.burst_bytes_list,
        hbm_outstanding_list=args.hbm_outstanding_list,
        request_overhead_cycles_list=args.request_overhead_cycles_list,
        row_hit_rate_list=args.row_hit_rate_list,
        row_miss_penalty_cycles_list=args.row_miss_penalty_cycles_list,
        scheduler_efficiency_list=args.scheduler_efficiency_list,
        arbitration_efficiency_list=args.arbitration_efficiency_list,
        virtual_channel_list=args.virtual_channel_list,
        prefetch_start_list=args.prefetch_start_list,
        bank_interleave_tokens=args.bank_interleave_tokens,
        bank_conflict_efficiency=args.bank_conflict_efficiency,
        router_latency_cycles_per_hop=args.router_latency_cycles_per_hop,
        macs_per_cycle=args.macs_per_cycle,
        vector_ops_per_cycle=args.vector_ops_per_cycle,
        clock_ns=args.clock_ns,
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_markdown(Path(args.out_md), payload)
    print(json.dumps({"ok": True, "out": args.out, "out_md": args.out_md}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
