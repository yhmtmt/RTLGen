#!/usr/bin/env python3
"""Re-sweep on-chip service knobs on top of the HBM-closed Llama7B frontier."""

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

from npu.eval import estimate_llm_decoder_attention_kv_onchip_service_schedule as onchip  # noqa: E402

JsonDict = dict[str, Any]


def _float_list(value: str) -> list[float]:
    items = [float(item.strip()) for item in value.split(",") if item.strip()]
    if not items or any(item < 0.0 for item in items):
        raise argparse.ArgumentTypeError("expected comma-separated nonnegative floats")
    return items


def _int_list(value: str) -> list[int]:
    items = [int(item.strip()) for item in value.split(",") if item.strip()]
    if not items or any(item <= 0 for item in items):
        raise argparse.ArgumentTypeError("expected comma-separated positive integers")
    return items


def _str_list(value: str) -> list[str]:
    items = [item.strip() for item in value.split(",") if item.strip()]
    if not items:
        raise argparse.ArgumentTypeError("expected comma-separated names")
    return items


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
                "topology": row.get("topology"),
                "tile_hbm_cycles": row.get("tile_hbm_cycles"),
                "controller_service_cycles": row.get("controller_service_cycles"),
                "channel_count": row.get("channel_count"),
                "channel_bandwidth_bytes_per_cycle": row.get("channel_bandwidth_bytes_per_cycle"),
                "burst_bytes": row.get("burst_bytes"),
                "hbm_outstanding": row.get("hbm_outstanding"),
                "row_hit_rate": row.get("row_hit_rate"),
                "scheduler_efficiency": row.get("scheduler_efficiency"),
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
    source = _load_json(args.measured_hbm_service_json)
    source_rows = _source_rows(source, limit=args.frontier_row_limit)
    if not source_rows:
        raise RuntimeError("no HBM-closed source rows found")

    best: JsonDict | None = None
    generated = 0
    heap_counter = 0
    top_heap: list[tuple[float, int, JsonDict]] = []
    dominance = Counter()
    schedule_counts = Counter()
    hbm_counts = Counter()
    best_by_policy: dict[tuple[Any, ...], JsonDict] = {}
    best_by_queue: dict[tuple[Any, ...], JsonDict] = {}
    best_by_hbm_service: dict[tuple[Any, ...], JsonDict] = {}

    for source_row in source_rows:
        for schedule_policy in args.schedule_policy:
            for bank_policy in args.bank_arbiter_policy:
                for endpoint_queue_depth_bytes in args.endpoint_queue_depth_bytes:
                    for bank_queue_depth_bytes in args.bank_queue_depth_bytes:
                        for router_latency_cycles_per_hop in args.router_latency_cycles_per_hop:
                            for packet_payload_bytes in args.packet_payload_bytes:
                                for prefetch_overlap_fraction in args.prefetch_overlap_fraction:
                                    if schedule_policy != "prefetch_overlap" and prefetch_overlap_fraction != 0.0:
                                        continue
                                    if schedule_policy == "prefetch_overlap" and prefetch_overlap_fraction <= 0.0:
                                        continue
                                    row = onchip._annotate_service(
                                        source_row,
                                        schedule_policy=schedule_policy,
                                        bank_arbiter_policy=bank_policy,
                                        endpoint_queue_depth_bytes=endpoint_queue_depth_bytes,
                                        bank_queue_depth_bytes=bank_queue_depth_bytes,
                                        router_latency_cycles_per_hop=router_latency_cycles_per_hop,
                                        packet_payload_bytes=packet_payload_bytes,
                                        prefetch_overlap_fraction=prefetch_overlap_fraction,
                                    )
                                    row.update(
                                        {
                                            "hbm_closed_onchip_schedule_model": (
                                                "hbm_closed_cycle_stepped_sram_bank_endpoint_router_v1"
                                            ),
                                            "source_latency_us": source_row.get("latency_us"),
                                            "source_dominant_tile_resource": source_row.get("dominant_tile_resource"),
                                            "source_onchip_shared_service_cycles": source_row.get(
                                                "onchip_shared_service_cycles"
                                            ),
                                            "source_tile_memory_cycles": source_row.get("tile_memory_cycles"),
                                            "source_tile_service_cycles": source_row.get("tile_service_cycles"),
                                            "latency_slowdown_vs_hbm_closed_source": round(
                                                float(row["latency_us"])
                                                / max(1e-9, float(source_row.get("latency_us", row["latency_us"]))),
                                                6,
                                            ),
                                        }
                                    )
                                    generated += 1
                                    dominance[str(row["dominant_tile_resource"])] += 1
                                    schedule_counts[str(row["schedule_policy"])] += 1
                                    hbm_counts[str(row.get("dominant_tile_resource") == "hbm")] += 1
                                    if best is None or float(row["latency_us"]) < float(best["latency_us"]):
                                        best = row
                                    _push_top(top_heap, row, counter=heap_counter, limit=args.top_k)
                                    heap_counter += 1
                                    _best_update(best_by_policy, ("schedule_policy", "bank_arbiter_policy"), row)
                                    _best_update(
                                        best_by_queue,
                                        (
                                            "endpoint_queue_depth_bytes",
                                            "bank_queue_depth_bytes",
                                            "router_latency_cycles_per_hop",
                                            "packet_payload_bytes",
                                        ),
                                        row,
                                    )
                                    _best_update(
                                        best_by_hbm_service,
                                        (
                                            "channel_count",
                                            "channel_bandwidth_bytes_per_cycle",
                                            "burst_bytes",
                                            "hbm_outstanding",
                                            "row_hit_rate",
                                            "scheduler_efficiency",
                                        ),
                                        row,
                                    )

    if best is None:
        raise RuntimeError("no HBM-closed on-chip schedule rows generated")
    top_rows = [entry[2] for entry in sorted(top_heap, key=lambda entry: (entry[2]["latency_us"], entry[1]))]
    return {
        "version": 1,
        "model": "llm_decoder_attention_kv_hbm_closed_onchip_schedule_llama7b_v1",
        "measured_hbm_service_json": str(args.measured_hbm_service_json),
        "source_model": source.get("model"),
        "inputs": {
            "frontier_row_limit": args.frontier_row_limit,
            "schedule_policy": args.schedule_policy,
            "bank_arbiter_policy": args.bank_arbiter_policy,
            "endpoint_queue_depth_bytes": args.endpoint_queue_depth_bytes,
            "bank_queue_depth_bytes": args.bank_queue_depth_bytes,
            "router_latency_cycles_per_hop": args.router_latency_cycles_per_hop,
            "packet_payload_bytes": args.packet_payload_bytes,
            "prefetch_overlap_fraction": args.prefetch_overlap_fraction,
        },
        "sweep_summary": {
            "source_rows_used": len(source_rows),
            "generated_row_count": generated,
            "dominant_tile_resource_counts": dict(sorted(dominance.items())),
            "schedule_policy_counts": dict(sorted(schedule_counts.items())),
            "hbm_dominant_counts": dict(sorted(hbm_counts.items())),
            "best_latency_us": best["latency_us"],
            "best_latency_slowdown_vs_hbm_closed_source": best["latency_slowdown_vs_hbm_closed_source"],
            "best_dominant_tile_resource": best["dominant_tile_resource"],
        },
        "best": best,
        "top_rows": top_rows,
        "best_by_policy": sorted(best_by_policy.values(), key=lambda row: row["latency_us"])[:100],
        "best_by_queue": sorted(best_by_queue.values(), key=lambda row: row["latency_us"])[:100],
        "best_by_hbm_service": sorted(best_by_hbm_service.values(), key=lambda row: row["latency_us"])[:100],
        "assumptions": [
            "HBM service cycles and controller parameters are inherited from the measured-HBM service source rows.",
            "This pass re-sweeps SRAM bank arbitration, endpoint queues, bank queues, packet payload, router hop latency, schedule staggering, and prefetch overlap.",
            "The model is still an analytic on-chip service simulator; it does not generate or prove full NoC RTL.",
            "Compute, measured SRAM capacity, local datapath PPA, endpoint/router/FIFO primitive PPA, and KV quality assumptions are inherited unchanged.",
        ],
    }


def write_markdown(path: Path, payload: JsonDict) -> None:
    best = payload["best"]
    lines = [
        "# Llama7B HBM-Closed On-Chip Schedule Closure",
        "",
        f"- source rows used: `{payload['sweep_summary']['source_rows_used']}`",
        f"- generated rows: `{payload['sweep_summary']['generated_row_count']}`",
        f"- dominant resources: `{payload['sweep_summary']['dominant_tile_resource_counts']}`",
        "",
        "## Best",
        "",
        "| latency us | vs HBM source | resource | schedule | bank policy | endpoint q | bank q | router hop | packet | hbm cycles | shared service | exposed shared |",
        "|---:|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|",
        "| {latency_us} | {latency_slowdown_vs_hbm_closed_source} | {dominant_tile_resource} | "
        "{schedule_policy} | {bank_arbiter_policy} | {endpoint_queue_depth_bytes} | "
        "{bank_queue_depth_bytes} | {router_latency_cycles_per_hop} | {packet_payload_bytes} | "
        "{tile_hbm_cycles} | {onchip_shared_service_cycles} | {onchip_exposed_shared_cycles} |".format(**best),
        "",
        "## Best By Policy",
        "",
        "| schedule | bank policy | latency us | vs source | resource | shared service | exposed shared |",
        "|---|---|---:|---:|---|---:|---:|",
    ]
    for row in payload["best_by_policy"][:30]:
        lines.append(
            "| {schedule_policy} | {bank_arbiter_policy} | {latency_us} | "
            "{latency_slowdown_vs_hbm_closed_source} | {dominant_tile_resource} | "
            "{onchip_shared_service_cycles} | {onchip_exposed_shared_cycles} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Best By Queue/Router",
            "",
            "| endpoint q | bank q | router hop | packet | latency us | penalties | resource |",
            "|---:|---:|---:|---:|---:|---|---|",
        ]
    )
    for row in payload["best_by_queue"][:30]:
        penalties = f"endpoint={row['onchip_endpoint_queue_penalty_cycles']},bank={row['onchip_bank_queue_penalty_cycles']}"
        lines.append(
            "| {endpoint_queue_depth_bytes} | {bank_queue_depth_bytes} | {router_latency_cycles_per_hop} | "
            "{packet_payload_bytes} | {latency_us} | {penalties} | {dominant_tile_resource} |".format(
                **row,
                penalties=penalties,
            )
        )
    lines.extend(["", "## Assumptions", ""])
    lines.extend(f"- {item}" for item in payload["assumptions"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--measured-hbm-service-json", type=Path, required=True)
    parser.add_argument("--frontier-row-limit", type=int, default=64)
    parser.add_argument("--schedule-policy", type=_str_list, default=["static_wave", "staggered_wave", "prefetch_overlap"])
    parser.add_argument("--bank-arbiter-policy", type=_str_list, default=["round_robin", "locality_first", "age_based"])
    parser.add_argument("--endpoint-queue-depth-bytes", type=_int_list, default=[1024, 2048, 8192, 32768])
    parser.add_argument("--bank-queue-depth-bytes", type=_int_list, default=[1024, 2048, 8192, 32768])
    parser.add_argument("--router-latency-cycles-per-hop", type=_int_list, default=[1, 2, 4])
    parser.add_argument("--packet-payload-bytes", type=_int_list, default=[64, 128, 256])
    parser.add_argument("--prefetch-overlap-fraction", type=_float_list, default=[0.0, 0.25, 0.5, 0.75])
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
