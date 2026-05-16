#!/usr/bin/env python3
"""Estimate selected decoder attention/KV NoC scheduling points."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

JsonDict = dict[str, Any]


DEFAULT_SELECTED_POINTS = [
    ("gpt2_small", 131072, 100.0),
    ("gpt2_small", 131072, 200.0),
    ("gpt2_medium_proxy", 131072, 200.0),
    ("gpt2_medium_proxy", 131072, 400.0),
    ("llama7b_proxy", 131072, 400.0),
]


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


def _ceil_div(a: int | float, b: int | float) -> int:
    return int(math.ceil(a / b)) if a else 0


def _byte_width(bits: int) -> int:
    return max(1, math.ceil(bits / 8))


def _selected_points(value: str | None) -> list[tuple[str, int, float]]:
    if not value:
        return list(DEFAULT_SELECTED_POINTS)
    points: list[tuple[str, int, float]] = []
    for item in value.split(","):
        fields = [field.strip() for field in item.split(":")]
        if len(fields) != 3:
            raise argparse.ArgumentTypeError(
                "selected points must be label:sequence_length:die_mm2 entries"
            )
        points.append((fields[0], int(fields[1]), float(fields[2])))
    return points


def _point_key(row: JsonDict) -> tuple[str, int, float]:
    return (str(row["label"]), int(row["sequence_length"]), float(row["die_area_mm2"]))


def _active_banks(*, tile_tokens: int, bank_interleave_tokens: int, bank_count: int) -> int:
    touched = _ceil_div(tile_tokens, bank_interleave_tokens)
    return max(1, min(bank_count, touched))


def _resource_cycles(
    *,
    bytes_count: float,
    bank_count: int,
    active_banks: int,
    bank_bandwidth_bytes_per_cycle: float,
    bank_conflict_efficiency: float,
) -> int:
    if bytes_count <= 0:
        return 0
    bank_parallelism = max(1, min(bank_count, active_banks))
    bandwidth = bank_parallelism * bank_bandwidth_bytes_per_cycle * bank_conflict_efficiency
    return _ceil_div(bytes_count, bandwidth)


def _scheduled_rows_for_point(
    *,
    baseline_row: JsonDict,
    tile_tokens_list: list[int],
    virtual_channel_list: list[int],
    arbitration_efficiency_list: list[float],
    bank_interleave_tokens: int,
    bank_conflict_efficiency: float,
    router_latency_cycles_per_hop: int,
    macs_per_cycle: int,
    vector_ops_per_cycle: int,
    clock_ns: float,
) -> list[JsonDict]:
    layers = int(baseline_row["layers"])
    hidden_size = int(baseline_row["hidden_size"])
    attention_heads = int(baseline_row["attention_heads"])
    sequence_length = int(baseline_row["sequence_length"])
    kv_heads = int(baseline_row["kv_heads"])
    kv_bits = int(baseline_row["kv_bits"])
    head_dim = hidden_size // attention_heads
    kv_width = kv_heads * head_dim
    kv_byte_width = _byte_width(kv_bits)

    qkv_macs_per_layer = hidden_size * hidden_size + 2 * hidden_size * kv_width
    qk_value_macs_per_layer = 2 * sequence_length * hidden_size
    softmax_ops_per_layer = 5 * attention_heads * sequence_length
    producer_cycles_per_layer = _ceil_div(qkv_macs_per_layer, macs_per_cycle)
    qk_value_compute_cycles_per_layer = _ceil_div(qk_value_macs_per_layer, macs_per_cycle)
    softmax_cycles_per_layer = _ceil_div(softmax_ops_per_layer, vector_ops_per_cycle)

    kv_cache_bytes = int(baseline_row["kv_cache_bytes"])
    kv_read_bytes_total = kv_cache_bytes
    local_read_share = float(baseline_row.get("local_bytes", 0)) / kv_read_bytes_total if kv_read_bytes_total else 0.0
    shared_read_share = float(baseline_row.get("shared_bytes", 0)) / kv_read_bytes_total if kv_read_bytes_total else 0.0
    hbm_read_share = float(baseline_row.get("hbm_bytes", 0)) / kv_read_bytes_total if kv_read_bytes_total else 0.0
    kv_read_bytes_per_layer = 2 * sequence_length * kv_width * kv_byte_width
    kv_write_bytes_per_layer = 2 * kv_width * kv_byte_width

    placement = str(baseline_row["placement"])
    local_write_share = 1.0 if placement == "local_sram" else 0.0
    shared_write_share = 1.0 if placement in {"shared_sram", "shared_sram_hbm_spill"} else 0.0
    hbm_write_share = 1.0 if placement == "hbm" else 0.0

    bank_count = int(baseline_row["bank_count"])
    bank_bw = float(baseline_row["bank_bandwidth_bytes_per_cycle"])
    noc_bw = float(baseline_row["noc_bandwidth_bytes_per_cycle"])
    noc_hops = int(baseline_row["noc_hops"])
    hbm_bw = float(baseline_row["hbm_bandwidth_bytes_per_cycle"])

    rows: list[JsonDict] = []
    for tile_tokens in tile_tokens_list:
        tiles_per_layer = _ceil_div(sequence_length, tile_tokens)
        active_banks = _active_banks(
            tile_tokens=tile_tokens,
            bank_interleave_tokens=bank_interleave_tokens,
            bank_count=bank_count,
        )
        tile_read_bytes = 2 * min(tile_tokens, sequence_length) * kv_width * kv_byte_width
        local_read_bytes_per_layer = kv_read_bytes_per_layer * local_read_share
        shared_read_bytes_per_layer = kv_read_bytes_per_layer * shared_read_share
        hbm_read_bytes_per_layer = kv_read_bytes_per_layer * hbm_read_share
        local_write_bytes_per_layer = kv_write_bytes_per_layer * local_write_share
        shared_write_bytes_per_layer = kv_write_bytes_per_layer * shared_write_share
        hbm_write_bytes_per_layer = kv_write_bytes_per_layer * hbm_write_share

        local_bank_cycles = _resource_cycles(
            bytes_count=local_read_bytes_per_layer + local_write_bytes_per_layer,
            bank_count=bank_count,
            active_banks=active_banks,
            bank_bandwidth_bytes_per_cycle=bank_bw,
            bank_conflict_efficiency=bank_conflict_efficiency,
        )
        shared_bank_cycles = _resource_cycles(
            bytes_count=shared_read_bytes_per_layer + shared_write_bytes_per_layer,
            bank_count=bank_count,
            active_banks=active_banks,
            bank_bandwidth_bytes_per_cycle=bank_bw,
            bank_conflict_efficiency=bank_conflict_efficiency,
        )
        hbm_cycles = _ceil_div(hbm_read_bytes_per_layer + hbm_write_bytes_per_layer, hbm_bw)

        for virtual_channels in virtual_channel_list:
            vc_gain = min(1.0, 0.85 + 0.05 * max(0, virtual_channels - 1))
            for arbitration_efficiency in arbitration_efficiency_list:
                noc_eff_bw = (noc_bw / max(1, noc_hops)) * arbitration_efficiency * vc_gain
                noc_payload_cycles = _ceil_div(shared_read_bytes_per_layer + shared_write_bytes_per_layer, noc_eff_bw)
                noc_header_cycles = tiles_per_layer * noc_hops * router_latency_cycles_per_hop if shared_read_bytes_per_layer else 0
                noc_cycles = noc_payload_cycles + noc_header_cycles
                shared_cycles = max(shared_bank_cycles, noc_cycles)
                memory_parallel_cycles = max(local_bank_cycles, shared_cycles, hbm_cycles)
                memory_serial_cycles = local_bank_cycles + shared_cycles + hbm_cycles

                strict_layer_cycles = (
                    producer_cycles_per_layer
                    + max(qk_value_compute_cycles_per_layer, memory_serial_cycles)
                    + softmax_cycles_per_layer
                )
                overlap_layer_cycles = (
                    max(
                        producer_cycles_per_layer,
                        qk_value_compute_cycles_per_layer,
                        memory_parallel_cycles,
                    )
                    + softmax_cycles_per_layer
                )
                strict_total_cycles = strict_layer_cycles * layers
                overlap_total_cycles = overlap_layer_cycles * layers
                rows.append(
                    {
                        "label": baseline_row["label"],
                        "sequence_length": sequence_length,
                        "die_area_mm2": baseline_row["die_area_mm2"],
                        "placement": placement,
                        "kv_sharing": baseline_row["kv_sharing"],
                        "kv_bits": kv_bits,
                        "kv_cache_mib": baseline_row["kv_cache_mib"],
                        "total_sram_mib": baseline_row["total_sram_mib"],
                        "local_capacity_mib": baseline_row["local_capacity_mib"],
                        "shared_capacity_mib": baseline_row["shared_capacity_mib"],
                        "bank_count": bank_count,
                        "bank_bandwidth_bytes_per_cycle": bank_bw,
                        "noc_bandwidth_bytes_per_cycle": noc_bw,
                        "noc_hops": noc_hops,
                        "hbm_bandwidth_bytes_per_cycle": hbm_bw,
                        "tile_tokens": tile_tokens,
                        "tiles_per_layer": tiles_per_layer,
                        "tile_read_bytes": int(tile_read_bytes),
                        "active_banks": active_banks,
                        "bank_interleave_tokens": bank_interleave_tokens,
                        "bank_conflict_efficiency": bank_conflict_efficiency,
                        "virtual_channels": virtual_channels,
                        "arbitration_efficiency": arbitration_efficiency,
                        "noc_effective_bytes_per_cycle": round(noc_eff_bw, 6),
                        "producer_cycles_per_layer": producer_cycles_per_layer,
                        "qk_value_compute_cycles_per_layer": qk_value_compute_cycles_per_layer,
                        "softmax_cycles_per_layer": softmax_cycles_per_layer,
                        "local_bank_cycles_per_layer": local_bank_cycles,
                        "shared_bank_cycles_per_layer": shared_bank_cycles,
                        "noc_cycles_per_layer": noc_cycles,
                        "hbm_cycles_per_layer": hbm_cycles,
                        "memory_parallel_cycles_per_layer": memory_parallel_cycles,
                        "memory_serial_cycles_per_layer": memory_serial_cycles,
                        "strict_total_cycles": strict_total_cycles,
                        "overlap_total_cycles": overlap_total_cycles,
                        "strict_latency_us": round(strict_total_cycles * clock_ns / 1000.0, 6),
                        "overlap_latency_us": round(overlap_total_cycles * clock_ns / 1000.0, 6),
                        "overlap_gain": round(strict_total_cycles / overlap_total_cycles, 6)
                        if overlap_total_cycles
                        else 0.0,
                        "dominant_overlap_limiter": _dominant(
                            {
                                "producer": producer_cycles_per_layer,
                                "qk_value_compute": qk_value_compute_cycles_per_layer,
                                "memory_parallel": memory_parallel_cycles,
                                "softmax": softmax_cycles_per_layer,
                            }
                        ),
                    }
                )
    return rows


def _dominant(values: dict[str, int]) -> str:
    return max(values.items(), key=lambda item: item[1])[0]


def build_report(
    *,
    capacity_noc_baseline: JsonDict,
    selected_points: list[tuple[str, int, float]],
    tile_tokens_list: list[int],
    virtual_channel_list: list[int],
    arbitration_efficiency_list: list[float],
    bank_interleave_tokens: int,
    bank_conflict_efficiency: float,
    router_latency_cycles_per_hop: int,
    macs_per_cycle: int,
    vector_ops_per_cycle: int,
    clock_ns: float,
) -> JsonDict:
    baseline_rows = {_point_key(row): row for row in capacity_noc_baseline.get("best_by_die", [])}
    missing = [point for point in selected_points if point not in baseline_rows]
    if missing:
        raise ValueError(f"selected points missing from capacity baseline: {missing}")

    all_rows: list[JsonDict] = []
    for point in selected_points:
        all_rows.extend(
            _scheduled_rows_for_point(
                baseline_row=baseline_rows[point],
                tile_tokens_list=tile_tokens_list,
                virtual_channel_list=virtual_channel_list,
                arbitration_efficiency_list=arbitration_efficiency_list,
                bank_interleave_tokens=bank_interleave_tokens,
                bank_conflict_efficiency=bank_conflict_efficiency,
                router_latency_cycles_per_hop=router_latency_cycles_per_hop,
                macs_per_cycle=macs_per_cycle,
                vector_ops_per_cycle=vector_ops_per_cycle,
                clock_ns=clock_ns,
            )
        )

    best_by_point: dict[tuple[str, int, float], JsonDict] = {}
    for row in all_rows:
        key = _point_key(row)
        if key not in best_by_point or row["overlap_latency_us"] < best_by_point[key]["overlap_latency_us"]:
            best_by_point[key] = row

    limiter_counts: dict[str, int] = {}
    for row in best_by_point.values():
        limiter = str(row["dominant_overlap_limiter"])
        limiter_counts[limiter] = limiter_counts.get(limiter, 0) + 1

    return {
        "version": 0.1,
        "model": "llm_decoder_attention_kv_noc_scheduler_selected_v1",
        "inputs": {
            "capacity_noc_model": capacity_noc_baseline.get("model"),
            "selected_points": [
                {"label": label, "sequence_length": seq, "die_area_mm2": die}
                for label, seq, die in selected_points
            ],
            "tile_tokens_list": tile_tokens_list,
            "virtual_channel_list": virtual_channel_list,
            "arbitration_efficiency_list": arbitration_efficiency_list,
            "bank_interleave_tokens": bank_interleave_tokens,
            "bank_conflict_efficiency": bank_conflict_efficiency,
            "router_latency_cycles_per_hop": router_latency_cycles_per_hop,
            "macs_per_cycle": macs_per_cycle,
            "vector_ops_per_cycle": vector_ops_per_cycle,
            "clock_ns": clock_ns,
        },
        "sweep_summary": {
            "selected_point_count": len(selected_points),
            "generated_row_count": len(all_rows),
            "best_by_point_row_count": len(best_by_point),
            "limiter_counts_on_best_by_point": limiter_counts,
        },
        "best_by_point": sorted(
            best_by_point.values(),
            key=lambda row: (row["label"], row["sequence_length"], row["die_area_mm2"]),
        ),
        "all_rows": all_rows,
        "assumptions": [
            "This is a selected-point scheduler estimator, not a cycle-accurate RTL NoC simulation.",
            "Selected points come from the capacity-constrained best_by_die frontier.",
            "Strict latency serializes producer, memory resources, and compute; overlap latency is a lower-bound schedule where independent producer, compute, local SRAM, shared SRAM/NoC, and HBM resources can run concurrently.",
            "NoC scheduling accounts for hop latency, arbitration efficiency, virtual-channel throughput relief, and payload bandwidth divided by hop count.",
            "SRAM bank pressure uses tile size, bank interleave granularity, selected bank count, and a bank conflict efficiency.",
            "Producer overlap here means QKV/KV-write service overlap within the selected attention/KV datapath; inter-layer transformer dependencies are not removed.",
        ],
    }


def _write_markdown(path: Path, payload: JsonDict) -> None:
    lines = [
        "# Decoder Attention/KV Selected NoC Scheduler",
        "",
        f"- model: `{payload['model']}`",
        f"- selected_point_count: `{payload['sweep_summary']['selected_point_count']}`",
        f"- generated_row_count: `{payload['sweep_summary']['generated_row_count']}`",
        "",
        "## Best By Point",
        "",
        "| shape | seq | die_mm2 | placement | tile | vc | arb_eff | strict_us | overlap_us | gain | limiter | noc_cyc/layer | mem_parallel/layer |",
        "|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---|---:|---:|",
    ]
    for row in payload["best_by_point"]:
        lines.append(
            "| {label} | {seq} | {die} | {placement} | {tile} | {vc} | {arb} | {strict} | {overlap} | {gain} | {limiter} | {noc} | {mem} |".format(
                label=row["label"],
                seq=row["sequence_length"],
                die=row["die_area_mm2"],
                placement=row["placement"],
                tile=row["tile_tokens"],
                vc=row["virtual_channels"],
                arb=row["arbitration_efficiency"],
                strict=row["strict_latency_us"],
                overlap=row["overlap_latency_us"],
                gain=row["overlap_gain"],
                limiter=row["dominant_overlap_limiter"],
                noc=row["noc_cycles_per_layer"],
                mem=row["memory_parallel_cycles_per_layer"],
            )
        )
    lines.extend(["", "## Assumptions", ""])
    lines.extend(f"- {item}" for item in payload["assumptions"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--capacity-noc-baseline", required=True)
    ap.add_argument("--selected-points", type=_selected_points, default=list(DEFAULT_SELECTED_POINTS))
    ap.add_argument("--tile-tokens-list", type=_int_list, default=[128, 256, 512, 1024, 2048])
    ap.add_argument("--virtual-channel-list", type=_int_list, default=[1, 2, 4])
    ap.add_argument("--arbitration-efficiency-list", type=_float_list, default=[0.55, 0.7, 0.85])
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
        selected_points=args.selected_points,
        tile_tokens_list=args.tile_tokens_list,
        virtual_channel_list=args.virtual_channel_list,
        arbitration_efficiency_list=args.arbitration_efficiency_list,
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
