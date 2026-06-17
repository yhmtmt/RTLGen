#!/usr/bin/env python3
"""Estimate Llama7B schedules with explicit on-chip SRAM/NoC service policies."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from npu.eval import estimate_llm_decoder_attention_kv_clustered_schedule as clustered  # noqa: E402
from npu.eval import estimate_llm_decoder_attention_kv_sram_noc_constrained_schedule as constrained  # noqa: E402


JsonDict = dict[str, Any]


_PROFILE_PRECISION_RE = re.compile(r"_q(\d+)(?:\D|$)")


def _float_list(value: str) -> list[float]:
    items = [float(item.strip()) for item in value.split(",") if item.strip()]
    if not items or any(item < 0.0 for item in items):
        raise argparse.ArgumentTypeError("expected comma-separated nonnegative floats")
    return items


def _positive_float_list(value: str) -> list[float]:
    items = _float_list(value)
    if any(item <= 0.0 for item in items):
        raise argparse.ArgumentTypeError("expected comma-separated positive floats")
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


def _ceil_div(numerator: int | float, denominator: int | float) -> int:
    if numerator <= 0:
        return 0
    return int(math.ceil(float(numerator) / max(1.0, float(denominator))))


def _load_json(path: Path) -> JsonDict:
    return json.loads(path.read_text(encoding="utf-8"))


def _source_rows(payload: JsonDict, *, limit: int) -> list[JsonDict]:
    rows = constrained._dedupe_rows(payload, limit=limit)
    return [row for row in rows if int(row.get("cluster_count", 0)) > 0]


def _full_tile_bytes(row: JsonDict) -> float:
    head_dim = int(row["hidden_size"]) // int(row["attention_heads"])
    kv_width = int(row["kv_heads"]) * head_dim
    return 2.0 * int(row["tile_tokens"]) * kv_width * int(row["kv_bits"]) / 8.0


def _bank_policy_efficiency(policy: str) -> float:
    if policy == "round_robin":
        return 0.90
    if policy == "locality_first":
        return 1.00
    if policy == "age_based":
        return 0.95
    raise ValueError(f"unknown bank policy: {policy}")


def _schedule_policy_efficiency(policy: str) -> tuple[float, float]:
    """Return (fabric contention efficiency, explicit start-spread cycles per cluster)."""
    if policy == "static_wave":
        return 1.0, 0.0
    if policy == "staggered_wave":
        return 1.12, 2.0
    if policy == "prefetch_overlap":
        return 1.05, 1.0
    raise ValueError(f"unknown schedule policy: {policy}")


def _queue_penalty(
    *,
    payload_bytes_per_cluster: float,
    service_bytes_per_cycle: float,
    queue_depth_bytes: int,
    latency_cycles: int,
) -> int:
    if payload_bytes_per_cluster <= 0.0:
        return 0
    inflight_bytes = service_bytes_per_cycle * max(1, latency_cycles)
    if queue_depth_bytes >= inflight_bytes:
        return 0
    shortfall = min(payload_bytes_per_cluster, inflight_bytes - queue_depth_bytes)
    return _ceil_div(shortfall, service_bytes_per_cycle)


def _annotate_service(
    row: JsonDict,
    *,
    schedule_policy: str,
    bank_arbiter_policy: str,
    endpoint_queue_depth_bytes: int,
    bank_queue_depth_bytes: int,
    router_latency_cycles_per_hop: int,
    packet_payload_bytes: int,
    prefetch_overlap_fraction: float,
) -> JsonDict:
    active_clusters = max(1, int(row["active_clusters"]))
    cluster_count = max(1, int(row["cluster_count"]))
    full_tile_bytes = _full_tile_bytes(row)
    shared_bytes_per_cluster = full_tile_bytes * float(row["shared_byte_share"])
    local_bytes_per_cluster = full_tile_bytes * float(row["local_byte_share"])
    hbm_cycles = int(row["tile_hbm_cycles"])

    topology_agg_bpc = float(
        row.get(
            "topology_aggregate_payload_bytes_per_cycle",
            row.get("practical_aggregate_noc_effective_bytes_per_cycle", 1.0),
        )
    )
    endpoint_bpc_per_cluster = float(row["endpoint_bytes_per_cycle_per_cluster"])
    endpoint_agg_bpc = endpoint_bpc_per_cluster * active_clusters
    shared_bank_bpc_per_cluster = float(row["practical_shared_bank_bytes_per_cycle_per_cluster"])
    local_bank_bpc_per_cluster = float(row["practical_local_bank_bytes_per_cycle_per_cluster"])
    bank_eff = _bank_policy_efficiency(bank_arbiter_policy)
    fabric_eff, stagger_cycles_per_cluster = _schedule_policy_efficiency(schedule_policy)
    hop_latency = max(0, int(row["noc_hops"]) * router_latency_cycles_per_hop)
    packet_count_per_cluster = _ceil_div(shared_bytes_per_cluster, packet_payload_bytes)

    local_bank_cycles = _ceil_div(local_bytes_per_cluster, local_bank_bpc_per_cluster * bank_eff)
    shared_bank_cycles = _ceil_div(shared_bytes_per_cluster, shared_bank_bpc_per_cluster * bank_eff)
    endpoint_cycles = _ceil_div(shared_bytes_per_cluster, endpoint_bpc_per_cluster)
    fabric_service_bpc = min(topology_agg_bpc * fabric_eff, endpoint_agg_bpc)
    fabric_cycles = _ceil_div(shared_bytes_per_cluster * active_clusters, fabric_service_bpc)
    endpoint_queue_penalty = _queue_penalty(
        payload_bytes_per_cluster=shared_bytes_per_cluster,
        service_bytes_per_cycle=endpoint_bpc_per_cluster,
        queue_depth_bytes=endpoint_queue_depth_bytes,
        latency_cycles=hop_latency + 1,
    )
    bank_queue_penalty = _queue_penalty(
        payload_bytes_per_cluster=shared_bytes_per_cluster,
        service_bytes_per_cycle=shared_bank_bpc_per_cluster * bank_eff,
        queue_depth_bytes=bank_queue_depth_bytes,
        latency_cycles=max(1, packet_count_per_cluster // 4),
    )
    wave_stagger_cycles = int(math.ceil(max(0, active_clusters - 1) * stagger_cycles_per_cluster))
    shared_service_cycles = (
        max(shared_bank_cycles, endpoint_cycles, fabric_cycles)
        + hop_latency
        + endpoint_queue_penalty
        + bank_queue_penalty
        + wave_stagger_cycles
    )

    overlap_fraction = prefetch_overlap_fraction if schedule_policy == "prefetch_overlap" else 0.0
    hidden_shared_cycles = min(shared_service_cycles, int(row["tile_attention_cycles"]) * overlap_fraction)
    exposed_shared_cycles = max(0, int(math.ceil(shared_service_cycles - hidden_shared_cycles)))
    tile_shared_path_cycles = max(shared_bank_cycles, exposed_shared_cycles)
    tile_memory_cycles = max(local_bank_cycles, tile_shared_path_cycles, hbm_cycles)
    tile_service_cycles = max(int(row["tile_attention_cycles"]), tile_memory_cycles)

    stages, _ = clustered._reduction_factor(str(row["reduction_strategy"]), active_clusters)
    reduction_service_bpc = min(topology_agg_bpc * fabric_eff, endpoint_agg_bpc)
    reduction_noc_cycles = (
        _ceil_div(int(row["cross_tile_reduction_payload_bytes"]), reduction_service_bpc)
        + stages * hop_latency
        + _queue_penalty(
            payload_bytes_per_cluster=float(row["partial_reduction_payload_bytes"]),
            service_bytes_per_cycle=endpoint_bpc_per_cluster,
            queue_depth_bytes=endpoint_queue_depth_bytes,
            latency_cycles=hop_latency + 1,
        )
    )
    base_reduction_cycles = int(row["local_reduction_cycles"]) + max(
        reduction_noc_cycles,
        int(row["cross_tile_reduction_vector_cycles"]),
    )
    cross_tile_reduction_cycles = (
        _ceil_div(base_reduction_cycles * float(row["reduction_cycle_multiplier"]), 1)
        + int(row["reducer_setup_cycles"])
    )

    kv_write_bytes = 2 * (int(row["kv_heads"]) * (int(row["hidden_size"]) // int(row["attention_heads"]))) * int(row["kv_bits"]) / 8.0
    kv_write_cycles = _ceil_div(kv_write_bytes, min(endpoint_bpc_per_cluster, shared_bank_bpc_per_cluster * bank_eff))
    command_backpressure_cycles = _ceil_div(endpoint_queue_penalty * int(row["tile_waves"]), active_clusters)
    command_dispatch_cycles = int(row["command_dispatch_cycles"]) + command_backpressure_cycles
    layer_cycles = (
        int(row["qkv_cycles"])
        + int(row["tile_waves"]) * tile_service_cycles
        + command_dispatch_cycles
        + cross_tile_reduction_cycles
        + kv_write_cycles
    )
    total_cycles = layer_cycles * int(row["layers"])
    clock_ns = float(row["clock_ns"])
    dominant = max(
        {
            "tile_attention": int(row["tile_attention_cycles"]),
            "local_sram": local_bank_cycles,
            "shared_path": tile_shared_path_cycles,
            "hbm": hbm_cycles,
            "cross_tile_reduction": cross_tile_reduction_cycles,
            "command_dispatch": command_dispatch_cycles,
        }.items(),
        key=lambda item: item[1],
    )[0]

    out = dict(row)
    out.update(
        {
            "onchip_service_model": "cycle_stepped_sram_bank_endpoint_router_v1",
            "schedule_policy": schedule_policy,
            "bank_arbiter_policy": bank_arbiter_policy,
            "endpoint_queue_depth_bytes": endpoint_queue_depth_bytes,
            "bank_queue_depth_bytes": bank_queue_depth_bytes,
            "router_latency_cycles_per_hop": router_latency_cycles_per_hop,
            "packet_payload_bytes": packet_payload_bytes,
            "prefetch_overlap_fraction": overlap_fraction,
            "onchip_full_tile_bytes": int(full_tile_bytes),
            "onchip_shared_bytes_per_cluster": int(math.ceil(shared_bytes_per_cluster)),
            "onchip_local_bytes_per_cluster": int(math.ceil(local_bytes_per_cluster)),
            "onchip_hbm_cycles_inherited": hbm_cycles,
            "onchip_topology_aggregate_bytes_per_cycle": round(topology_agg_bpc, 6),
            "onchip_fabric_service_bytes_per_cycle": round(fabric_service_bpc, 6),
            "onchip_endpoint_bytes_per_cycle_per_cluster": round(endpoint_bpc_per_cluster, 6),
            "onchip_shared_bank_bytes_per_cycle_per_cluster": round(shared_bank_bpc_per_cluster * bank_eff, 6),
            "onchip_local_bank_bytes_per_cycle_per_cluster": round(local_bank_bpc_per_cluster * bank_eff, 6),
            "onchip_packet_count_per_cluster": packet_count_per_cluster,
            "onchip_hop_latency_cycles": hop_latency,
            "onchip_endpoint_queue_penalty_cycles": endpoint_queue_penalty,
            "onchip_bank_queue_penalty_cycles": bank_queue_penalty,
            "onchip_wave_stagger_cycles": wave_stagger_cycles,
            "onchip_shared_service_cycles": shared_service_cycles,
            "onchip_hidden_shared_cycles": int(math.floor(hidden_shared_cycles)),
            "onchip_exposed_shared_cycles": exposed_shared_cycles,
            "tile_local_sram_cycles": local_bank_cycles,
            "tile_shared_path_cycles": tile_shared_path_cycles,
            "tile_memory_cycles": tile_memory_cycles,
            "tile_service_cycles": tile_service_cycles,
            "cross_tile_reduction_noc_cycles": reduction_noc_cycles,
            "base_cross_tile_reduction_cycles": base_reduction_cycles,
            "cross_tile_reduction_cycles": cross_tile_reduction_cycles,
            "command_dispatch_cycles": command_dispatch_cycles,
            "kv_write_cycles": kv_write_cycles,
            "layer_cycles": layer_cycles,
            "total_cycles": total_cycles,
            "latency_us": round(total_cycles * clock_ns / 1000.0, 6),
            "dominant_tile_resource": dominant,
            "latency_slowdown_vs_sram_noc_cap": round(
                (total_cycles * clock_ns / 1000.0) / max(1e-9, float(row["latency_us"])),
                6,
            ),
            "latency_slowdown_vs_topology_derived": round(
                (total_cycles * clock_ns / 1000.0) / max(1e-9, float(row.get("unconstrained_latency_us", row["latency_us"]))),
                6,
            ),
        }
    )
    return out


def _float_key(row: JsonDict, field: str) -> float:
    try:
        return float(row.get(field, math.inf))
    except Exception:
        return math.inf


def _profile_precision_bits(row: JsonDict) -> int:
    match = _PROFILE_PRECISION_RE.search(str(row.get("measured_l1_profile", "")))
    return int(match.group(1)) if match else 0


def _objective_key(row: JsonDict) -> tuple[float, float, float, float, int, str]:
    return (
        _float_key(row, "latency_us"),
        _float_key(row, "total_cycles"),
        _float_key(row, "logic_power_mw"),
        _float_key(row, "logic_area_used_um2"),
        -_profile_precision_bits(row),
        str(row.get("measured_l1_profile", "")),
    )


def _update_best(target: dict[tuple[Any, ...], JsonDict], keys: tuple[str, ...], row: JsonDict) -> None:
    key = tuple(row.get(item) for item in keys)
    current = target.get(key)
    if current is None or _objective_key(row) < _objective_key(current):
        target[key] = row


def build_report(args: argparse.Namespace) -> JsonDict:
    repo_root = args.repo_root
    source_payload = _load_json(repo_root / args.sram_noc_constrained_json)
    source_rows = _source_rows(source_payload, limit=args.frontier_row_limit)

    best: JsonDict | None = None
    generated = 0
    dominance = Counter()
    schedule_counts = Counter()
    generated_rows: list[JsonDict] = []
    best_by_policy: dict[tuple[Any, ...], JsonDict] = {}
    best_by_topology: dict[tuple[Any, ...], JsonDict] = {}
    best_by_queue: dict[tuple[Any, ...], JsonDict] = {}
    best_by_profile: dict[tuple[Any, ...], JsonDict] = {}
    generated_latencies: list[float] = []

    for row in source_rows:
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
                                    out = _annotate_service(
                                        row,
                                        schedule_policy=schedule_policy,
                                        bank_arbiter_policy=bank_policy,
                                        endpoint_queue_depth_bytes=endpoint_queue_depth_bytes,
                                        bank_queue_depth_bytes=bank_queue_depth_bytes,
                                        router_latency_cycles_per_hop=router_latency_cycles_per_hop,
                                        packet_payload_bytes=packet_payload_bytes,
                                        prefetch_overlap_fraction=prefetch_overlap_fraction,
                                    )
                                    generated += 1
                                    dominance[str(out["dominant_tile_resource"])] += 1
                                    schedule_counts[str(out["schedule_policy"])] += 1
                                    latency_us = float(out["latency_us"])
                                    generated_latencies.append(latency_us)
                                    generated_rows.append(out)
                                    if best is None or _objective_key(out) < _objective_key(best):
                                        best = out
                                    _update_best(best_by_policy, ("schedule_policy", "bank_arbiter_policy"), out)
                                    _update_best(best_by_topology, ("topology", "scheduler_policy", "reduction_strategy"), out)
                                    _update_best(best_by_profile, ("measured_l1_profile",), out)
                                    _update_best(
                                        best_by_queue,
                                        ("endpoint_queue_depth_bytes", "bank_queue_depth_bytes", "router_latency_cycles_per_hop"),
                                        out,
                                    )
    if best is None:
        raise RuntimeError("no on-chip service rows generated")
    top_rows = sorted(generated_rows, key=_objective_key)[: args.top_k]
    sorted_latencies = sorted(generated_latencies)
    profile_rows: list[JsonDict] = []
    for row in sorted(best_by_profile.values(), key=_objective_key):
        profile_row = dict(row)
        latency = float(profile_row["latency_us"])
        profile_row["rank_in_decoder_frontier"] = 1 + sum(1 for item in sorted_latencies if item < latency)
        profile_row["same_latency_row_count"] = sum(1 for item in sorted_latencies if item == latency)
        profile_rows.append(profile_row)
    return {
        "version": 1,
        "model": "llm_decoder_attention_kv_onchip_service_schedule_llama7b_v1",
        "sram_noc_constrained_json": str(args.sram_noc_constrained_json),
        "source_model": source_payload.get("model"),
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
        },
        "best": best,
        "top_rows": top_rows,
        "best_by_profile": profile_rows,
        "best_by_policy": sorted(best_by_policy.values(), key=_objective_key)[:100],
        "best_by_topology": sorted(best_by_topology.values(), key=_objective_key)[:100],
        "best_by_queue": sorted(best_by_queue.values(), key=_objective_key)[:100],
        "assumptions": [
            "This pass refines on-chip SRAM/NoC service only; HBM/DRAM cycles and bandwidth fields are inherited from the input row.",
            "SRAM bank arbitration is modeled as per-cycle service under a named policy, not as placed SRAM macro RTL.",
            "Endpoint queues, packet payload, router hop latency, and schedule staggering are explicit parameters.",
            "The model is still an analytic service simulator; it does not yet generate RTL routers or prove ready/valid equivalence.",
        ],
    }


def write_markdown(path: Path, payload: JsonDict) -> None:
    best = payload["best"]
    lines = [
        "# Llama7B On-Chip SRAM/NoC Service Schedule",
        "",
        f"- source rows used: `{payload['sweep_summary']['source_rows_used']}`",
        f"- generated rows: `{payload['sweep_summary']['generated_row_count']}`",
        f"- dominant resources: `{payload['sweep_summary']['dominant_tile_resource_counts']}`",
        "",
        "## Best",
        "",
        "| topology | schedule | bank policy | clusters | link bits | endpoint q | bank q | router hop | packet | latency us | vs cap | vs topo | resource |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
        "| {topology} | {schedule_policy} | {bank_arbiter_policy} | {cluster_count} | {link_width_bits} | "
        "{endpoint_queue_depth_bytes} | {bank_queue_depth_bytes} | {router_latency_cycles_per_hop} | "
        "{packet_payload_bytes} | {latency_us} | {latency_slowdown_vs_sram_noc_cap} | "
        "{latency_slowdown_vs_topology_derived} | {dominant_tile_resource} |".format(**best),
        "",
        "## Best By Precision Profile",
        "",
        "| profile | frontier rank | latency us | area um2 | power mW | schedule | bank policy | resource |",
        "|---|---:|---:|---:|---:|---|---|---|",
    ]
    for row in payload.get("best_by_profile", []):
        lines.append(
            "| {measured_l1_profile} | {rank_in_decoder_frontier} | {latency_us} | {logic_area_used_um2} | "
            "{logic_power_mw} | {schedule_policy} | {bank_arbiter_policy} | {dominant_tile_resource} |".format(**row)
        )
    lines.extend(
        [
            "",
        "## Best By Policy",
        "",
        "| schedule | bank policy | latency us | vs cap | shared service cycles | exposed shared | resource |",
        "|---|---|---:|---:|---:|---:|---|",
        ]
    )
    for row in payload["best_by_policy"][:30]:
        lines.append(
            "| {schedule_policy} | {bank_arbiter_policy} | {latency_us} | {latency_slowdown_vs_sram_noc_cap} | "
            "{onchip_shared_service_cycles} | {onchip_exposed_shared_cycles} | {dominant_tile_resource} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Best By Queue/Router Setting",
            "",
            "| endpoint q | bank q | router hop | latency us | queue penalties | resource |",
            "|---:|---:|---:|---:|---|---|",
        ]
    )
    for row in payload["best_by_queue"][:30]:
        penalties = f"endpoint={row['onchip_endpoint_queue_penalty_cycles']},bank={row['onchip_bank_queue_penalty_cycles']}"
        lines.append(
            "| {endpoint_queue_depth_bytes} | {bank_queue_depth_bytes} | {router_latency_cycles_per_hop} | "
            "{latency_us} | {penalties} | {dominant_tile_resource} |".format(**row, penalties=penalties)
        )
    lines.extend(["", "## Assumptions", ""])
    lines.extend(f"- {item}" for item in payload["assumptions"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-root", type=Path, default=Path("."))
    ap.add_argument("--sram-noc-constrained-json", required=True, type=Path)
    ap.add_argument("--frontier-row-limit", type=int, default=128)
    ap.add_argument("--schedule-policy", type=_str_list, default=["static_wave", "staggered_wave", "prefetch_overlap"])
    ap.add_argument("--bank-arbiter-policy", type=_str_list, default=["round_robin", "locality_first", "age_based"])
    ap.add_argument("--endpoint-queue-depth-bytes", type=_int_list, default=[2048, 8192, 32768])
    ap.add_argument("--bank-queue-depth-bytes", type=_int_list, default=[2048, 8192, 32768])
    ap.add_argument("--router-latency-cycles-per-hop", type=_int_list, default=[1, 2])
    ap.add_argument("--packet-payload-bytes", type=_int_list, default=[32, 64, 128])
    ap.add_argument("--prefetch-overlap-fraction", type=_float_list, default=[0.0, 0.25, 0.5])
    ap.add_argument("--top-k", type=int, default=50)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--out-md", required=True, type=Path)
    args = ap.parse_args()

    payload = build_report(args)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(args.out_md, payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
