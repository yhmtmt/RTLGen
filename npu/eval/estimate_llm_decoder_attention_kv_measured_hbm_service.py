#!/usr/bin/env python3
"""Apply an explicit HBM service model to the measured-SRAM Llama7B frontier."""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from npu.eval import estimate_llm_decoder_attention_kv_onchip_service_schedule as onchip  # noqa: E402

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


def _ceil_div(numerator: int | float, denominator: int | float) -> int:
    if numerator <= 0:
        return 0
    return int(math.ceil(float(numerator) / max(1.0, float(denominator))))


def _load_json(path: Path) -> JsonDict:
    return json.loads(path.read_text(encoding="utf-8"))


def _hbm_service(
    *,
    tile_hbm_bytes: float,
    channel_count: int,
    channel_bandwidth_bytes_per_cycle: float,
    burst_bytes: int,
    hbm_outstanding: int,
    request_overhead_cycles: int,
    row_hit_rate: float,
    row_miss_penalty_cycles: int,
    scheduler_efficiency: float,
) -> JsonDict:
    payload_bw = channel_count * channel_bandwidth_bytes_per_cycle * scheduler_efficiency
    payload_cycles = _ceil_div(tile_hbm_bytes, payload_bw)
    burst_count = _ceil_div(tile_hbm_bytes, burst_bytes)
    row_miss_count = int(math.ceil(burst_count * max(0.0, 1.0 - row_hit_rate)))
    overhead_cycles = _ceil_div(burst_count, hbm_outstanding) * request_overhead_cycles
    row_miss_cycles = _ceil_div(row_miss_count, hbm_outstanding) * row_miss_penalty_cycles
    service_cycles = max(1, payload_cycles + overhead_cycles + row_miss_cycles)
    return {
        "tile_hbm_bytes": int(math.ceil(tile_hbm_bytes)),
        "payload_hbm_bytes_per_cycle": round(payload_bw, 6),
        "payload_cycles": payload_cycles,
        "burst_count": burst_count,
        "row_miss_count": row_miss_count,
        "overhead_cycles": overhead_cycles,
        "row_miss_cycles": row_miss_cycles,
        "controller_service_cycles": service_cycles,
        "effective_hbm_bytes_per_cycle": round(tile_hbm_bytes / service_cycles, 6),
    }


def _controller_row(
    source_row: JsonDict,
    *,
    channel_count: int,
    channel_bandwidth_bytes_per_cycle: float,
    burst_bytes: int,
    hbm_outstanding: int,
    request_overhead_cycles: int,
    row_hit_rate: float,
    row_miss_penalty_cycles: int,
    scheduler_efficiency: float,
) -> JsonDict:
    tile_hbm_bytes = onchip._full_tile_bytes(source_row) * float(source_row["hbm_byte_share"])
    service = _hbm_service(
        tile_hbm_bytes=tile_hbm_bytes,
        channel_count=channel_count,
        channel_bandwidth_bytes_per_cycle=channel_bandwidth_bytes_per_cycle,
        burst_bytes=burst_bytes,
        hbm_outstanding=hbm_outstanding,
        request_overhead_cycles=request_overhead_cycles,
        row_hit_rate=row_hit_rate,
        row_miss_penalty_cycles=row_miss_penalty_cycles,
        scheduler_efficiency=scheduler_efficiency,
    )
    raw_effective = float(source_row.get("effective_hbm_bytes_per_cycle", 0.0) or 0.0)
    adjusted = dict(source_row)
    adjusted.update(
        {
            "measured_hbm_service_model": "channel_burst_row_window_v1",
            "source_effective_hbm_bytes_per_cycle": raw_effective,
            "source_tile_hbm_cycles": int(source_row.get("tile_hbm_cycles", 0)),
            "channel_count": channel_count,
            "channel_bandwidth_bytes_per_cycle": channel_bandwidth_bytes_per_cycle,
            "burst_bytes": burst_bytes,
            "hbm_outstanding": hbm_outstanding,
            "request_overhead_cycles": request_overhead_cycles,
            "row_hit_rate": row_hit_rate,
            "row_miss_penalty_cycles": row_miss_penalty_cycles,
            "scheduler_efficiency": scheduler_efficiency,
            "tile_hbm_cycles": service["controller_service_cycles"],
            "effective_hbm_bytes_per_cycle": service["effective_hbm_bytes_per_cycle"],
            "derived_hbm_efficiency_vs_source": round(
                service["effective_hbm_bytes_per_cycle"] / raw_effective,
                6,
            )
            if raw_effective > 0.0
            else None,
            **service,
        }
    )
    return onchip._annotate_service(
        adjusted,
        schedule_policy=str(adjusted["schedule_policy"]),
        bank_arbiter_policy=str(adjusted["bank_arbiter_policy"]),
        endpoint_queue_depth_bytes=int(adjusted["endpoint_queue_depth_bytes"]),
        bank_queue_depth_bytes=int(adjusted["bank_queue_depth_bytes"]),
        router_latency_cycles_per_hop=int(adjusted["router_latency_cycles_per_hop"]),
        packet_payload_bytes=int(adjusted["packet_payload_bytes"]),
        prefetch_overlap_fraction=float(adjusted["prefetch_overlap_fraction"]),
    )


def build_report(args: argparse.Namespace) -> JsonDict:
    source = _load_json(args.measured_sram_rebalance_json)
    source_rows = list(source.get("top_rows") or [])
    if not source_rows and isinstance(source.get("best"), dict):
        source_rows = [source["best"]]
    source_rows = source_rows[: args.frontier_row_limit]
    if not source_rows:
        raise RuntimeError("no source rows found")

    rows: list[JsonDict] = []
    for source_row in source_rows:
        for channel_count in args.channel_count:
            for channel_bw in args.channel_bandwidth_bytes_per_cycle:
                for burst_bytes in args.burst_bytes:
                    for hbm_outstanding in args.hbm_outstanding:
                        for request_overhead in args.request_overhead_cycles:
                            for row_hit_rate in args.row_hit_rate:
                                for row_miss_penalty in args.row_miss_penalty_cycles:
                                    for scheduler_efficiency in args.scheduler_efficiency:
                                        rows.append(
                                            _controller_row(
                                                source_row,
                                                channel_count=channel_count,
                                                channel_bandwidth_bytes_per_cycle=channel_bw,
                                                burst_bytes=burst_bytes,
                                                hbm_outstanding=hbm_outstanding,
                                                request_overhead_cycles=request_overhead,
                                                row_hit_rate=row_hit_rate,
                                                row_miss_penalty_cycles=row_miss_penalty,
                                                scheduler_efficiency=scheduler_efficiency,
                                            )
                                        )
    rows_sorted = sorted(rows, key=lambda item: float(item["latency_us"]))
    dominance = Counter(str(row["dominant_tile_resource"]) for row in rows)
    best = rows_sorted[0]
    return {
        "version": 1,
        "model": "llm_decoder_attention_kv_measured_hbm_service_llama7b_v1",
        "measured_sram_rebalance_json": str(args.measured_sram_rebalance_json),
        "source_model": source.get("model"),
        "sweep_summary": {
            "source_rows_used": len(source_rows),
            "generated_row_count": len(rows),
            "best_latency_us": best["latency_us"],
            "best_hbm_byte_share": best["hbm_byte_share"],
            "best_effective_hbm_bytes_per_cycle": best["effective_hbm_bytes_per_cycle"],
            "best_source_effective_hbm_bytes_per_cycle": best["source_effective_hbm_bytes_per_cycle"],
            "best_derived_hbm_efficiency_vs_source": best["derived_hbm_efficiency_vs_source"],
            "dominant_tile_resource_counts": dict(sorted(dominance.items())),
        },
        "best": best,
        "top_rows": rows_sorted[: args.top_k],
        "assumptions": [
            "Payload cycles are bounded by channel_count * channel_bandwidth_bytes_per_cycle * scheduler_efficiency.",
            "Burst command overhead and row-miss penalties are batched by the outstanding-request window.",
            "The model refines HBM service on top of the measured-SRAM rebalance frontier; compute, SRAM, endpoint, and NoC parameters are inherited.",
            "This is an analytic HBM service bound, not a full DRAM timing simulator with bank groups, refresh, turnarounds, or address mapping.",
        ],
    }


def write_markdown(path: Path, payload: JsonDict) -> None:
    best = payload["best"]
    lines = [
        "# Llama7B Measured-HBM Service Closure",
        "",
        f"- source rows used: `{payload['sweep_summary']['source_rows_used']}`",
        f"- generated rows: `{payload['sweep_summary']['generated_row_count']}`",
        f"- dominant resources: `{payload['sweep_summary']['dominant_tile_resource_counts']}`",
        "",
        "## Best",
        "",
        "| latency us | resource | hbm share | eff B/cyc | source eff B/cyc | eff/source | channels | ch B/cyc | burst | outstanding | row hit | sched eff | service cycles |",
        "|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        "| {latency_us} | {dominant_tile_resource} | {hbm_byte_share} | {effective_hbm_bytes_per_cycle} | "
        "{source_effective_hbm_bytes_per_cycle} | {derived_hbm_efficiency_vs_source} | {channel_count} | "
        "{channel_bandwidth_bytes_per_cycle} | {burst_bytes} | {hbm_outstanding} | {row_hit_rate} | "
        "{scheduler_efficiency} | {controller_service_cycles} |".format(**best),
        "",
        "## Top Rows",
        "",
        "| rank | latency us | resource | eff/source | channels | ch B/cyc | burst | outstanding | row hit | sched eff |",
        "|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for index, row in enumerate(payload["top_rows"][:30], start=1):
        lines.append(
            "| {rank} | {latency_us} | {dominant_tile_resource} | {derived_hbm_efficiency_vs_source} | "
            "{channel_count} | {channel_bandwidth_bytes_per_cycle} | {burst_bytes} | {hbm_outstanding} | "
            "{row_hit_rate} | {scheduler_efficiency} |".format(rank=index, **row)
        )
    lines.extend(["", "## Assumptions", ""])
    lines.extend(f"- {item}" for item in payload["assumptions"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--measured-sram-rebalance-json", type=Path, required=True)
    parser.add_argument("--frontier-row-limit", type=int, default=16)
    parser.add_argument("--channel-count", type=_int_list, default=[4, 8, 16])
    parser.add_argument("--channel-bandwidth-bytes-per-cycle", type=_float_list, default=[256, 512, 1024])
    parser.add_argument("--burst-bytes", type=_int_list, default=[256, 512, 1024])
    parser.add_argument("--hbm-outstanding", type=_int_list, default=[4, 8, 16, 32])
    parser.add_argument("--request-overhead-cycles", type=_int_list, default=[2, 4, 8])
    parser.add_argument("--row-hit-rate", type=_float_list, default=[0.5, 0.75, 0.9])
    parser.add_argument("--row-miss-penalty-cycles", type=_int_list, default=[8, 16, 32])
    parser.add_argument("--scheduler-efficiency", type=_float_list, default=[0.6, 0.75, 0.9])
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
