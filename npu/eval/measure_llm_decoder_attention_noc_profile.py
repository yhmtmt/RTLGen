#!/usr/bin/env python3
"""Build a bounded NoC service profile for Llama7B decoder attention."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any


JsonDict = dict[str, Any]


def _ceil_div(numerator: float, denominator: float) -> int:
    return int(math.ceil(float(numerator) / float(denominator)))


def _float_list(value: str) -> list[float]:
    return [float(item.strip()) for item in value.split(",") if item.strip()]


def _int_list(value: str) -> list[int]:
    return [int(item.strip()) for item in value.split(",") if item.strip()]


def _load_best_metrics(metrics_csv: Path) -> JsonDict | None:
    if not metrics_csv.exists():
        return None
    with metrics_csv.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    ok_rows = [row for row in rows if row.get("status") == "ok"]
    if not ok_rows:
        return None
    best = min(
        ok_rows,
        key=lambda row: (
            float(row["critical_path_ns"]),
            float(row["die_area"]),
            float(row["total_power_mw"]),
        ),
    )
    return {
        "metrics_csv": str(metrics_csv),
        "critical_path_ns": float(best["critical_path_ns"]),
        "area_um2": float(best["die_area"]),
        "power_mw": float(best["total_power_mw"]),
        "tag": best.get("tag", ""),
        "param_hash": best.get("param_hash", ""),
        "result_path": best.get("result_path", ""),
    }


def _primitive_metrics(repo_root: Path, flit_bits: int) -> JsonDict:
    fifo = _load_best_metrics(repo_root / f"runs/designs/noc/l1_noc_fifo_w{flit_bits}_d16_wrapper/metrics.csv")
    router = _load_best_metrics(repo_root / f"runs/designs/noc/l1_noc_router_p4_w{flit_bits}_wrapper/metrics.csv")
    return {
        "fifo": fifo,
        "router": router,
    }


def build_profile(args: argparse.Namespace) -> JsonDict:
    head_dim = args.hidden_size // args.attention_heads
    kv_width = args.kv_heads * head_dim
    full_tile_bytes = int(2 * args.tile_tokens * kv_width * args.kv_bits / 8)
    shared_tile_bytes = int(math.ceil(full_tile_bytes * args.shared_byte_share))
    stat_payload_bytes = args.attention_heads * 2 * args.reduction_scalar_bytes
    value_payload_bytes = args.hidden_size * args.reduction_scalar_bytes
    partial_payload_bytes = stat_payload_bytes + value_payload_bytes
    cross_tile_reduction_payload_bytes = args.active_clusters * partial_payload_bytes
    kv_write_bytes = int(2 * kv_width * args.kv_bits / 8)

    rows: list[JsonDict] = []
    repo_root = args.repo_root.resolve()
    primitive_by_width = {flit_bits: _primitive_metrics(repo_root, flit_bits) for flit_bits in args.flit_bits}
    for flit_bits in args.flit_bits:
        flit_bytes = flit_bits // 8
        for raw_bandwidth in args.raw_bandwidth_bytes_per_cycle:
            for hops in args.hops:
                for virtual_channels in args.virtual_channels:
                    vc_gain = min(1.0, args.vc_base_efficiency + args.vc_increment * (virtual_channels - 1))
                    for arbitration_efficiency in args.arbitration_efficiency:
                        aggregate_payload_bpc = raw_bandwidth / max(1, hops) * arbitration_efficiency * vc_gain
                        per_cluster_payload_bpc = aggregate_payload_bpc / max(1, args.active_clusters)
                        router_latency_cycles = hops * args.router_latency_cycles_per_hop
                        shared_tile_cycles = _ceil_div(shared_tile_bytes, per_cluster_payload_bpc) + router_latency_cycles
                        reduction_cycles = _ceil_div(cross_tile_reduction_payload_bytes, aggregate_payload_bpc) + router_latency_cycles
                        kv_write_cycles = _ceil_div(kv_write_bytes, aggregate_payload_bpc) + router_latency_cycles
                        rows.append(
                            {
                                "flit_bits": flit_bits,
                                "flit_bytes": flit_bytes,
                                "raw_bandwidth_bytes_per_cycle": raw_bandwidth,
                                "hops": hops,
                                "virtual_channels": virtual_channels,
                                "arbitration_efficiency": arbitration_efficiency,
                                "vc_gain": round(vc_gain, 6),
                                "aggregate_effective_payload_bytes_per_cycle": round(aggregate_payload_bpc, 6),
                                "per_cluster_effective_payload_bytes_per_cycle": round(per_cluster_payload_bpc, 6),
                                "shared_tile_payload_bytes": shared_tile_bytes,
                                "shared_tile_flits": _ceil_div(shared_tile_bytes, flit_bytes),
                                "shared_tile_noc_cycles": shared_tile_cycles,
                                "cross_tile_reduction_payload_bytes": cross_tile_reduction_payload_bytes,
                                "cross_tile_reduction_flits": _ceil_div(cross_tile_reduction_payload_bytes, flit_bytes),
                                "cross_tile_reduction_noc_cycles": reduction_cycles,
                                "kv_write_payload_bytes": kv_write_bytes,
                                "kv_write_flits": _ceil_div(kv_write_bytes, flit_bytes),
                                "kv_write_noc_cycles": kv_write_cycles,
                                "dominant_noc_service": max(
                                    {
                                        "shared_tile": shared_tile_cycles,
                                        "cross_tile_reduction": reduction_cycles,
                                        "kv_write": kv_write_cycles,
                                    }.items(),
                                    key=lambda item: item[1],
                                )[0],
                            }
                        )

    best_rows = sorted(rows, key=lambda row: row["shared_tile_noc_cycles"])[: min(12, len(rows))]
    worst_rows = sorted(rows, key=lambda row: row["shared_tile_noc_cycles"], reverse=True)[: min(12, len(rows))]
    return {
        "version": 1,
        "model": "llama7b_proxy",
        "profile": "decoder_attention_noc_profile",
        "parameters": {
            "sequence_length": args.sequence_length,
            "tile_tokens": args.tile_tokens,
            "tile_count": _ceil_div(args.sequence_length, args.tile_tokens),
            "hidden_size": args.hidden_size,
            "attention_heads": args.attention_heads,
            "kv_heads": args.kv_heads,
            "head_dim": head_dim,
            "kv_bits": args.kv_bits,
            "active_clusters": args.active_clusters,
            "shared_byte_share": args.shared_byte_share,
            "reduction_scalar_bytes": args.reduction_scalar_bytes,
            "router_latency_cycles_per_hop": args.router_latency_cycles_per_hop,
        },
        "traffic_quantities": {
            "full_tile_kv_bytes": full_tile_bytes,
            "shared_tile_payload_bytes": shared_tile_bytes,
            "partial_reduction_payload_bytes": partial_payload_bytes,
            "cross_tile_reduction_payload_bytes": cross_tile_reduction_payload_bytes,
            "kv_write_payload_bytes": kv_write_bytes,
        },
        "measured_primitives": primitive_by_width,
        "rows": rows,
        "best_shared_tile_rows": best_rows,
        "worst_shared_tile_rows": worst_rows,
        "remaining_abstractions": [
            "Effective payload/cycle is a bounded service model using measured FIFO/router PPA plus explicit arbitration efficiency; it is not a cycle-accurate routed NoC RTL simulation.",
            "Wire delay, topology floorplan, and adaptive routing are not modeled.",
            "The full scheduler must still choose how much traffic is local SRAM, shared SRAM, or HBM before applying this profile.",
        ],
    }


def write_report(payload: JsonDict, report: Path) -> None:
    lines = [
        "# Llama7B Attention NoC Profile",
        "",
        "## Traffic Quantities",
        "",
        "| quantity | bytes |",
        "|---|---:|",
    ]
    for key, value in payload["traffic_quantities"].items():
        lines.append(f"| {key} | {value} |")
    lines.extend(
        [
            "",
            "## Best Shared-Tile Service Rows",
            "",
            "| flit | raw B/cyc | hops | vc | arb | eff agg B/cyc | eff cluster B/cyc | tile cycles | reduction cycles |",
            "|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in payload["best_shared_tile_rows"]:
        lines.append(
            "| {flit_bits} | {raw_bandwidth_bytes_per_cycle} | {hops} | {virtual_channels} | "
            "{arbitration_efficiency} | {aggregate_effective_payload_bytes_per_cycle} | "
            "{per_cluster_effective_payload_bytes_per_cycle} | {shared_tile_noc_cycles} | "
            "{cross_tile_reduction_noc_cycles} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Measured Primitive Inputs",
            "",
        ]
    )
    for flit_bits, metrics in payload["measured_primitives"].items():
        lines.append(f"### {flit_bits}-bit flits")
        for primitive, values in metrics.items():
            if values is None:
                lines.append(f"- {primitive}: missing metrics")
            else:
                lines.append(
                    f"- {primitive}: area `{values['area_um2']}` um2, "
                    f"clock `{values['critical_path_ns']}` ns, power `{values['power_mw']}` mW"
                )
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Rows are service bounds for selected traffic; they close the hidden NoC-efficiency knobs but do not replace a full routed NoC implementation.",
        ]
    )
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--sequence-length", type=int, default=131072)
    parser.add_argument("--tile-tokens", type=int, default=512)
    parser.add_argument("--hidden-size", type=int, default=4096)
    parser.add_argument("--attention-heads", type=int, default=32)
    parser.add_argument("--kv-heads", type=int, default=4)
    parser.add_argument("--kv-bits", type=int, default=8)
    parser.add_argument("--active-clusters", type=int, default=8)
    parser.add_argument("--shared-byte-share", type=float, default=0.44005)
    parser.add_argument("--reduction-scalar-bytes", type=int, default=2)
    parser.add_argument("--flit-bits", type=_int_list, default=[128, 256])
    parser.add_argument("--raw-bandwidth-bytes-per-cycle", type=_float_list, default=[8192.0, 32768.0])
    parser.add_argument("--hops", type=_int_list, default=[1, 2, 4])
    parser.add_argument("--virtual-channels", type=_int_list, default=[1, 2, 4])
    parser.add_argument("--arbitration-efficiency", type=_float_list, default=[0.55, 0.70, 0.85])
    parser.add_argument("--vc-base-efficiency", type=float, default=0.85)
    parser.add_argument("--vc-increment", type=float, default=0.05)
    parser.add_argument("--router-latency-cycles-per-hop", type=int, default=2)
    args = parser.parse_args()

    if args.hidden_size % args.attention_heads != 0:
        raise SystemExit("--hidden-size must be divisible by --attention-heads")
    if any(flit_bits % 8 != 0 or flit_bits <= 0 for flit_bits in args.flit_bits):
        raise SystemExit("--flit-bits values must be positive multiples of 8")

    payload = build_profile(args)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_report(payload, args.report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
