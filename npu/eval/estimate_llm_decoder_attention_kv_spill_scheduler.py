#!/usr/bin/env python3
"""Estimate tile-level decoder attention/KV spill scheduling for one hard point."""

from __future__ import annotations

import argparse
import heapq
import json
import math
from pathlib import Path
from typing import Any

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


def _ceil_div(a: int | float, b: int | float) -> int:
    return int(math.ceil(a / b)) if a else 0


def _byte_width(bits: int) -> int:
    return max(1, math.ceil(bits / 8))


def _point_key(row: JsonDict) -> tuple[str, int, float]:
    return (str(row["label"]), int(row["sequence_length"]), float(row["die_area_mm2"]))


def _find_baseline_row(
    *, capacity_noc_baseline: JsonDict, label: str, sequence_length: int, die_area_mm2: float
) -> JsonDict:
    wanted = (label, sequence_length, float(die_area_mm2))
    for row in capacity_noc_baseline.get("best_by_die", []):
        if _point_key(row) == wanted:
            return row
    raise ValueError(f"baseline point is missing from capacity best_by_die: {wanted}")


def _active_banks(*, tile_tokens: int, bank_interleave_tokens: int, bank_count: int) -> int:
    return max(1, min(bank_count, _ceil_div(tile_tokens, bank_interleave_tokens)))


def _simulate_layer(
    *,
    baseline_row: JsonDict,
    tile_tokens: int,
    prefetch_distance_tiles: int,
    hbm_outstanding: int,
    hbm_efficiency: float,
    arbitration_efficiency: float,
    virtual_channels: int,
    bank_interleave_tokens: int,
    bank_conflict_efficiency: float,
    router_latency_cycles_per_hop: int,
    prefetch_start: str,
    macs_per_cycle: int,
    vector_ops_per_cycle: int,
) -> JsonDict:
    hidden_size = int(baseline_row["hidden_size"])
    attention_heads = int(baseline_row["attention_heads"])
    sequence_length = int(baseline_row["sequence_length"])
    kv_heads = int(baseline_row["kv_heads"])
    kv_bits = int(baseline_row["kv_bits"])
    head_dim = hidden_size // attention_heads
    kv_width = kv_heads * head_dim
    kv_byte_width = _byte_width(kv_bits)

    bank_count = int(baseline_row["bank_count"])
    bank_bw = float(baseline_row["bank_bandwidth_bytes_per_cycle"])
    noc_bw = float(baseline_row["noc_bandwidth_bytes_per_cycle"])
    noc_hops = int(baseline_row["noc_hops"])
    hbm_bw = float(baseline_row["hbm_bandwidth_bytes_per_cycle"])

    kv_cache_bytes = int(baseline_row["kv_cache_bytes"])
    shared_read_share = float(baseline_row.get("shared_bytes", 0)) / kv_cache_bytes if kv_cache_bytes else 0.0
    hbm_read_share = float(baseline_row.get("hbm_bytes", 0)) / kv_cache_bytes if kv_cache_bytes else 0.0
    if str(baseline_row["placement"]) != "shared_sram_hbm_spill":
        raise ValueError(f"spill scheduler expects shared_sram_hbm_spill, got {baseline_row['placement']}")

    qkv_macs = hidden_size * hidden_size + 2 * hidden_size * kv_width
    qkv_cycles = _ceil_div(qkv_macs, macs_per_cycle)
    tile_count = _ceil_div(sequence_length, tile_tokens)
    active_banks = _active_banks(
        tile_tokens=tile_tokens,
        bank_interleave_tokens=bank_interleave_tokens,
        bank_count=bank_count,
    )
    shared_bank_bw = active_banks * bank_bw * bank_conflict_efficiency
    vc_gain = min(1.0, 0.85 + 0.05 * max(0, virtual_channels - 1))
    noc_eff_bw = (noc_bw / max(1, noc_hops)) * arbitration_efficiency * vc_gain
    hbm_eff_bw = hbm_bw * hbm_efficiency

    tile_compute_cycles = _ceil_div(2 * tile_tokens * hidden_size, macs_per_cycle)
    tile_softmax_cycles = _ceil_div(5 * attention_heads * tile_tokens, vector_ops_per_cycle)
    tile_attention_cycles = tile_compute_cycles + tile_softmax_cycles
    full_tile_bytes = 2 * tile_tokens * kv_width * kv_byte_width
    full_shared_bytes = full_tile_bytes * shared_read_share
    full_hbm_bytes = full_tile_bytes * hbm_read_share
    tile_shared_bank_cycles = _ceil_div(full_shared_bytes, shared_bank_bw)
    tile_noc_cycles = _ceil_div(full_shared_bytes, noc_eff_bw) + noc_hops * router_latency_cycles_per_hop
    tile_shared_path_cycles = max(tile_shared_bank_cycles, tile_noc_cycles)
    tile_hbm_cycles = _ceil_div(full_hbm_bytes, hbm_eff_bw)

    earliest_hbm_start = 0 if prefetch_start == "during_qkv" else qkv_cycles
    hbm_lane_heap = [0 for _ in range(max(1, hbm_outstanding))]
    heapq.heapify(hbm_lane_heap)
    shared_done: list[int] = []
    shared_free = qkv_cycles
    compute_done: list[int] = []
    compute_free = qkv_cycles
    hbm_stall_cycles = 0
    shared_stall_cycles = 0
    compute_wait_cycles = 0
    prefetch_stall_cycles = 0
    for tile_index in range(tile_count):
        window_release = earliest_hbm_start
        if tile_index > prefetch_distance_tiles:
            window_source = tile_index - prefetch_distance_tiles - 1
            window_release = max(window_release, compute_done[window_source])
        hbm_lane_free = heapq.heappop(hbm_lane_heap)
        hbm_start = max(hbm_lane_free, window_release)
        prefetch_stall_cycles += max(0, hbm_start - hbm_lane_free)
        hbm_finish = hbm_start + tile_hbm_cycles
        heapq.heappush(hbm_lane_heap, hbm_finish)
        shared_start = shared_free
        shared_finish = shared_start + tile_shared_path_cycles
        shared_done.append(shared_finish)
        shared_free = shared_finish
        ready = max(hbm_finish, shared_finish, qkv_cycles)
        compute_start = max(compute_free, ready)
        hbm_stall_cycles += max(0, hbm_finish - compute_free)
        shared_stall_cycles += max(0, shared_finish - compute_free)
        compute_wait_cycles += max(0, compute_start - compute_free)
        compute_free = compute_start + tile_attention_cycles
        compute_done.append(compute_free)

    kv_write_bytes = 2 * kv_width * kv_byte_width
    kv_write_shared_cycles = _ceil_div(kv_write_bytes, min(shared_bank_bw, noc_eff_bw))
    layer_cycles = compute_free + kv_write_shared_cycles
    return {
        "tile_count": tile_count,
        "active_banks": active_banks,
        "qkv_cycles": qkv_cycles,
        "tile_attention_cycles": tile_attention_cycles,
        "tile_shared_bank_cycles": tile_shared_bank_cycles,
        "tile_noc_cycles": tile_noc_cycles,
        "tile_shared_path_cycles": tile_shared_path_cycles,
        "tile_hbm_cycles": tile_hbm_cycles,
        "kv_write_shared_cycles": kv_write_shared_cycles,
        "layer_cycles": layer_cycles,
        "hbm_stall_cycles": hbm_stall_cycles,
        "shared_stall_cycles": shared_stall_cycles,
        "compute_wait_cycles": compute_wait_cycles,
        "prefetch_stall_cycles": prefetch_stall_cycles,
        "shared_read_share": round(shared_read_share, 6),
        "hbm_read_share": round(hbm_read_share, 6),
        "noc_effective_bytes_per_cycle": round(noc_eff_bw, 6),
        "hbm_effective_bytes_per_cycle": round(hbm_eff_bw, 6),
        "dominant_tile_resource": max(
            {
                "tile_attention": tile_attention_cycles,
                "shared_path": tile_shared_path_cycles,
                "hbm": tile_hbm_cycles,
            }.items(),
            key=lambda item: item[1],
        )[0],
    }


def build_report(
    *,
    capacity_noc_baseline: JsonDict,
    label: str,
    sequence_length: int,
    die_area_mm2: float,
    tile_tokens_list: list[int],
    prefetch_distance_tiles_list: list[int],
    hbm_outstanding_list: list[int],
    hbm_efficiency_list: list[float],
    arbitration_efficiency_list: list[float],
    virtual_channel_list: list[int],
    bank_interleave_tokens: int,
    bank_conflict_efficiency: float,
    router_latency_cycles_per_hop: int,
    prefetch_start_list: list[str],
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
    rows: list[JsonDict] = []
    layers = int(baseline_row["layers"])
    for tile_tokens in tile_tokens_list:
        for prefetch_distance_tiles in prefetch_distance_tiles_list:
            for hbm_outstanding in hbm_outstanding_list:
                for hbm_efficiency in hbm_efficiency_list:
                    for arbitration_efficiency in arbitration_efficiency_list:
                        for virtual_channels in virtual_channel_list:
                            for prefetch_start in prefetch_start_list:
                                layer = _simulate_layer(
                                    baseline_row=baseline_row,
                                    tile_tokens=tile_tokens,
                                    prefetch_distance_tiles=prefetch_distance_tiles,
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
                                        "total_sram_mib": baseline_row["total_sram_mib"],
                                        "shared_capacity_mib": baseline_row["shared_capacity_mib"],
                                        "hbm_byte_share": baseline_row["hbm_byte_share"],
                                        "tile_tokens": tile_tokens,
                                        "prefetch_distance_tiles": prefetch_distance_tiles,
                                        "hbm_outstanding": hbm_outstanding,
                                        "hbm_efficiency": hbm_efficiency,
                                        "arbitration_efficiency": arbitration_efficiency,
                                        "virtual_channels": virtual_channels,
                                        "prefetch_start": prefetch_start,
                                        "total_cycles": total_cycles,
                                        "latency_us": round(total_cycles * clock_ns / 1000.0, 6),
                                        **layer,
                                    }
                                )

    best = min(rows, key=lambda row: row["latency_us"])
    dominant_counts: dict[str, int] = {}
    for row in rows:
        key = str(row["dominant_tile_resource"])
        dominant_counts[key] = dominant_counts.get(key, 0) + 1
    top_rows = sorted(rows, key=lambda row: row["latency_us"])[:50]
    return {
        "version": 0.1,
        "model": "llm_decoder_attention_kv_spill_scheduler_llama7b_131k_v1",
        "inputs": {
            "capacity_noc_model": capacity_noc_baseline.get("model"),
            "selected_point": {
                "label": label,
                "sequence_length": sequence_length,
                "die_area_mm2": die_area_mm2,
            },
            "tile_tokens_list": tile_tokens_list,
            "prefetch_distance_tiles_list": prefetch_distance_tiles_list,
            "hbm_outstanding_list": hbm_outstanding_list,
            "hbm_efficiency_list": hbm_efficiency_list,
            "arbitration_efficiency_list": arbitration_efficiency_list,
            "virtual_channel_list": virtual_channel_list,
            "bank_interleave_tokens": bank_interleave_tokens,
            "bank_conflict_efficiency": bank_conflict_efficiency,
            "router_latency_cycles_per_hop": router_latency_cycles_per_hop,
            "prefetch_start_list": prefetch_start_list,
            "macs_per_cycle": macs_per_cycle,
            "vector_ops_per_cycle": vector_ops_per_cycle,
            "clock_ns": clock_ns,
        },
        "sweep_summary": {
            "generated_row_count": len(rows),
            "retained_top_row_count": len(top_rows),
            "dominant_tile_resource_counts": dominant_counts,
        },
        "best": best,
        "top_rows": top_rows,
        "assumptions": [
            "This is a tile-level spill scheduler estimator for the selected llama7b_proxy 131k 400 mm2 point.",
            "The KV cache residency split is inherited from the capacity/NoC best_by_die result.",
            "HBM traffic may be prefetched during or after QKV production, with finite outstanding requests and a finite prefetch window.",
            "Shared-SRAM traffic is serialized through a compact bank plus NoC path model with hop latency, arbitration efficiency, virtual-channel relief, and bank conflict efficiency.",
            "Tile attention compute waits for both shared-resident and HBM-spilled KV bytes for that tile; tile compute itself is serialized.",
            "This is still a scheduler model, not RTL NoC arbitration or SRAM macro timing.",
        ],
    }


def _write_markdown(path: Path, payload: JsonDict) -> None:
    best = payload["best"]
    lines = [
        "# Decoder Attention/KV Spill Scheduler",
        "",
        f"- model: `{payload['model']}`",
        f"- generated_row_count: `{payload['sweep_summary']['generated_row_count']}`",
        f"- selected_point: `{best['label']} seq={best['sequence_length']} die={best['die_area_mm2']}mm2`",
        "",
        "## Best",
        "",
        "| tile | prefetch_dist | hbm_out | hbm_eff | arb_eff | vc | start | latency_us | layer_cycles | tile_resource | hbm_share | hbm_stall | shared_stall |",
        "|---:|---:|---:|---:|---:|---:|---|---:|---:|---|---:|---:|---:|",
        "| {tile} | {dist} | {hbm_out} | {hbm_eff} | {arb} | {vc} | {start} | {lat} | {layer} | {res} | {hbm_share} | {hbm_stall} | {shared_stall} |".format(
            tile=best["tile_tokens"],
            dist=best["prefetch_distance_tiles"],
            hbm_out=best["hbm_outstanding"],
            hbm_eff=best["hbm_efficiency"],
            arb=best["arbitration_efficiency"],
            vc=best["virtual_channels"],
            start=best["prefetch_start"],
            lat=best["latency_us"],
            layer=best["layer_cycles"],
            res=best["dominant_tile_resource"],
            hbm_share=best["hbm_read_share"],
            hbm_stall=best["hbm_stall_cycles"],
            shared_stall=best["shared_stall_cycles"],
        ),
        "",
        "## Top 10",
        "",
        "| rank | tile | prefetch_dist | hbm_out | hbm_eff | arb_eff | vc | start | latency_us | resource |",
        "|---:|---:|---:|---:|---:|---:|---:|---|---:|---|",
    ]
    for index, row in enumerate(payload["top_rows"][:10], start=1):
        lines.append(
            "| {rank} | {tile} | {dist} | {hbm_out} | {hbm_eff} | {arb} | {vc} | {start} | {lat} | {res} |".format(
                rank=index,
                tile=row["tile_tokens"],
                dist=row["prefetch_distance_tiles"],
                hbm_out=row["hbm_outstanding"],
                hbm_eff=row["hbm_efficiency"],
                arb=row["arbitration_efficiency"],
                vc=row["virtual_channels"],
                start=row["prefetch_start"],
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
    ap.add_argument("--tile-tokens-list", type=_int_list, default=[256, 512, 1024, 2048, 4096])
    ap.add_argument("--prefetch-distance-tiles-list", type=_int_list, default=[1, 2, 4, 8, 16])
    ap.add_argument("--hbm-outstanding-list", type=_int_list, default=[1, 2, 4, 8])
    ap.add_argument("--hbm-efficiency-list", type=_float_list, default=[0.4, 0.6, 0.8])
    ap.add_argument("--arbitration-efficiency-list", type=_float_list, default=[0.55, 0.7, 0.85])
    ap.add_argument("--virtual-channel-list", type=_int_list, default=[1, 2, 4])
    ap.add_argument("--bank-interleave-tokens", type=int, default=16)
    ap.add_argument("--bank-conflict-efficiency", type=float, default=0.75)
    ap.add_argument("--router-latency-cycles-per-hop", type=int, default=2)
    ap.add_argument("--prefetch-start-list", type=_str_list, default=["after_qkv", "during_qkv"])
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
        hbm_outstanding_list=args.hbm_outstanding_list,
        hbm_efficiency_list=args.hbm_efficiency_list,
        arbitration_efficiency_list=args.arbitration_efficiency_list,
        virtual_channel_list=args.virtual_channel_list,
        bank_interleave_tokens=args.bank_interleave_tokens,
        bank_conflict_efficiency=args.bank_conflict_efficiency,
        router_latency_cycles_per_hop=args.router_latency_cycles_per_hop,
        prefetch_start_list=args.prefetch_start_list,
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
