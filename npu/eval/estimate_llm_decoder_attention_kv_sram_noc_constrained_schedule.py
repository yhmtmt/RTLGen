#!/usr/bin/env python3
"""Apply practical SRAM-bank and endpoint NoC caps to Llama7B topology-derived schedules."""

from __future__ import annotations

import argparse
import heapq
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from npu.eval import estimate_llm_decoder_attention_kv_clustered_schedule as clustered  # noqa: E402
from npu.eval import estimate_llm_decoder_attention_kv_topology_derived_schedule as topology_derived  # noqa: E402


JsonDict = dict[str, Any]


def _float_list(value: str) -> list[float]:
    items = [float(item.strip()) for item in value.split(",") if item.strip()]
    if not items or any(item <= 0.0 for item in items):
        raise argparse.ArgumentTypeError("expected comma-separated positive floats")
    return items


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


def _optional_str_list(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _profile_list(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _load_json(path: Path) -> JsonDict:
    return json.loads(path.read_text(encoding="utf-8"))


def _ceil_div(numerator: int | float, denominator: int | float) -> int:
    if numerator <= 0:
        return 0
    return int(math.ceil(float(numerator) / max(1.0, float(denominator))))


def _dedupe_rows(payload: JsonDict, *, limit: int) -> list[JsonDict]:
    buckets = [
        [payload.get("best")] if isinstance(payload.get("best"), dict) else [],
        payload.get("top_rows") or [],
        payload.get("best_by_scheduler") or [],
        payload.get("best_by_topology") or [],
        payload.get("best_by_die") or [],
        payload.get("best_by_die_topology") or [],
    ]
    rows: list[JsonDict] = []
    seen: set[tuple[Any, ...]] = set()
    for row in sorted(
        (item for bucket in buckets for item in bucket if isinstance(item, dict)),
        key=lambda item: (
            float(item.get("latency_us", 0.0)),
            str(item.get("topology", "")),
            str(item.get("scheduler_policy", "")),
            int(item.get("cluster_count", 0)),
            int(item.get("link_width_bits", 0)),
        ),
    ):
        key = (
            str(row.get("topology")),
            str(row.get("scheduler_policy")),
            str(row.get("reduction_strategy")),
            str(row.get("bank_placement")),
            int(row.get("cluster_count", 0)),
            int(row.get("bank_count", 0)),
            int(row.get("link_width_bits", 0)),
            int(row.get("virtual_channels", 0)),
            float(row.get("sram_area_fraction", 0.0)),
            float(row.get("compute_logic_area_fraction", 0.0)),
            int(row.get("tile_tokens", 0)),
            int(row.get("command_cycles_per_tile", 0)),
            int(row.get("command_cycles_per_wave", 0)),
            int(row.get("reducer_setup_cycles", 0)),
            float(row.get("reduction_cycle_multiplier", 0.0)),
            int(row.get("compute_replica_count", 0)),
        )
        if key in seen:
            continue
        seen.add(key)
        rows.append(row)
        if len(rows) >= limit:
            break
    if not rows:
        raise RuntimeError("no retained topology-derived schedule rows found")
    return rows


def _sram_profile_caps(payload: JsonDict) -> JsonDict:
    buffers = payload.get("buffers") or []
    widths = [int(item.get("width_bits", 0)) for item in buffers if isinstance(item, dict)]
    return {
        "allocated_sram_bytes": int((payload.get("totals") or {}).get("allocated_sram_bytes", 0)),
        "logical_buffer_bytes": int((payload.get("totals") or {}).get("logical_buffer_bytes", 0)),
        "max_bank_width_bits": max(widths) if widths else 256,
        "sram_metrics_json": payload.get("sram_metrics_json", ""),
        "profile": payload.get("profile", ""),
    }


def _topology_aggregate_bpc(row: JsonDict) -> float:
    return float(
        row.get(
            "topology_aggregate_payload_bytes_per_cycle",
            row.get("aggregate_noc_effective_bytes_per_cycle", 0.0),
        )
    )


def _practical_bank_service(
    *,
    row: JsonDict,
    sram_bank_port_bytes_per_cycle: float,
    sram_read_ports_per_bank: int,
    sram_bank_efficiency: float,
) -> JsonDict:
    bank_count = int(row["bank_count"])
    active_clusters = max(1, int(row["active_clusters"]))
    active_banks = min(bank_count, int(row.get("active_banks", bank_count)))
    aggregate_bank_bpc = active_banks * sram_bank_port_bytes_per_cycle * sram_read_ports_per_bank * sram_bank_efficiency
    shared_bank_bpc_per_cluster = max(1.0, aggregate_bank_bpc / active_clusters)
    if str(row.get("bank_placement")) == "per_cluster_local":
        local_banks_per_cluster = max(1.0, bank_count / active_clusters)
    else:
        local_banks_per_cluster = max(1.0, active_banks * max(float(row["local_sram_fraction"]), 1.0 / active_clusters) / active_clusters)
    local_bank_bpc_per_cluster = max(
        1.0,
        local_banks_per_cluster * sram_bank_port_bytes_per_cycle * sram_read_ports_per_bank * sram_bank_efficiency,
    )
    return {
        "aggregate_bank_bpc": aggregate_bank_bpc,
        "shared_bank_bpc_per_cluster": shared_bank_bpc_per_cluster,
        "local_bank_bpc_per_cluster": local_bank_bpc_per_cluster,
        "local_banks_per_cluster": local_banks_per_cluster,
        "active_banks": active_banks,
    }


def _apply_constraints(
    row: JsonDict,
    *,
    sram_caps: JsonDict,
    local_buffer_multiplier: float,
    sram_bank_port_bytes_per_cycle: float,
    sram_read_ports_per_bank: int,
    sram_bank_efficiency: float,
    endpoint_port_bytes_per_cycle: float,
    endpoint_ports_per_cluster: int,
    endpoint_efficiency: float,
) -> tuple[JsonDict | None, str | None]:
    active_clusters = max(1, int(row["active_clusters"]))
    cluster_count = max(1, int(row["cluster_count"]))
    local_capacity_per_cluster = float(row["local_capacity_mib"]) * 1024.0 * 1024.0 / cluster_count
    required_local_buffer = int(sram_caps["allocated_sram_bytes"] * local_buffer_multiplier)
    if local_capacity_per_cluster < required_local_buffer:
        return None, "local_tile_buffer_capacity"

    bank = _practical_bank_service(
        row=row,
        sram_bank_port_bytes_per_cycle=sram_bank_port_bytes_per_cycle,
        sram_read_ports_per_bank=sram_read_ports_per_bank,
        sram_bank_efficiency=sram_bank_efficiency,
    )
    topology_agg_bpc = _topology_aggregate_bpc(row)
    endpoint_bpc_per_cluster = endpoint_port_bytes_per_cycle * endpoint_ports_per_cluster * endpoint_efficiency
    endpoint_agg_bpc = endpoint_bpc_per_cluster * active_clusters
    practical_aggregate_noc_bpc = max(1.0, min(topology_agg_bpc, endpoint_agg_bpc, bank["aggregate_bank_bpc"]))
    practical_per_cluster_noc_bpc = max(1.0, practical_aggregate_noc_bpc / active_clusters)

    hidden_size = int(row["hidden_size"])
    attention_heads = int(row["attention_heads"])
    kv_heads = int(row["kv_heads"])
    kv_bits = int(row["kv_bits"])
    head_dim = hidden_size // attention_heads
    kv_width = kv_heads * head_dim
    kv_bytes_per_scalar = kv_bits / 8.0
    full_tile_bytes = 2 * int(row["tile_tokens"]) * kv_width * kv_bytes_per_scalar

    tile_local_cycles = _ceil_div(
        full_tile_bytes * float(row["local_byte_share"]),
        bank["local_bank_bpc_per_cluster"],
    )
    tile_shared_bank_cycles = _ceil_div(
        full_tile_bytes * float(row["shared_byte_share"]),
        bank["shared_bank_bpc_per_cluster"],
    )
    tile_noc_cycles = _ceil_div(
        full_tile_bytes * float(row["shared_byte_share"]),
        practical_per_cluster_noc_bpc,
    ) + int(row["noc_hops"]) * 2
    tile_shared_path_cycles = max(tile_shared_bank_cycles, tile_noc_cycles)
    tile_hbm_cycles = int(row["tile_hbm_cycles"])
    tile_memory_cycles = max(tile_local_cycles, tile_shared_path_cycles, tile_hbm_cycles)
    tile_attention_cycles = int(row["tile_attention_cycles"])
    tile_service_cycles = max(tile_attention_cycles, tile_memory_cycles)

    stages, _ = clustered._reduction_factor(str(row["reduction_strategy"]), active_clusters)
    reduction_noc_cycles = _ceil_div(
        int(row["cross_tile_reduction_payload_bytes"]),
        practical_aggregate_noc_bpc,
    ) + stages * int(row["noc_hops"]) * 2
    base_reduction_cycles = int(row["local_reduction_cycles"]) + max(
        reduction_noc_cycles,
        int(row["cross_tile_reduction_vector_cycles"]),
    )
    cross_tile_reduction_cycles = _ceil_div(
        base_reduction_cycles * float(row["reduction_cycle_multiplier"]),
        1,
    ) + int(row["reducer_setup_cycles"])

    kv_write_bytes = 2 * kv_width * kv_bytes_per_scalar
    kv_write_cycles = _ceil_div(kv_write_bytes, min(bank["aggregate_bank_bpc"], practical_aggregate_noc_bpc))
    layer_cycles = (
        int(row["qkv_cycles"])
        + int(row["tile_waves"]) * tile_service_cycles
        + int(row["command_dispatch_cycles"])
        + cross_tile_reduction_cycles
        + kv_write_cycles
    )
    total_cycles = layer_cycles * int(row["layers"])
    clock_ns = float(row["clock_ns"])
    dominant = max(
        {
            "tile_attention": tile_attention_cycles,
            "local_sram": tile_local_cycles,
            "shared_path": tile_shared_path_cycles,
            "hbm": tile_hbm_cycles,
            "cross_tile_reduction": cross_tile_reduction_cycles,
            "command_dispatch": int(row["command_dispatch_cycles"]),
        }.items(),
        key=lambda item: item[1],
    )[0]

    constrained = dict(row)
    constrained.update(
        {
            "unconstrained_latency_us": row["latency_us"],
            "unconstrained_tile_local_sram_cycles": row["tile_local_sram_cycles"],
            "unconstrained_tile_shared_path_cycles": row["tile_shared_path_cycles"],
            "unconstrained_aggregate_noc_effective_bytes_per_cycle": row["aggregate_noc_effective_bytes_per_cycle"],
            "sram_profile_source": sram_caps["profile"],
            "sram_metrics_json": sram_caps["sram_metrics_json"],
            "tile_local_buffer_bytes": sram_caps["allocated_sram_bytes"],
            "local_buffer_multiplier": local_buffer_multiplier,
            "required_local_buffer_bytes_per_cluster": required_local_buffer,
            "local_capacity_bytes_per_cluster": int(local_capacity_per_cluster),
            "sram_bank_port_bytes_per_cycle": sram_bank_port_bytes_per_cycle,
            "sram_read_ports_per_bank": sram_read_ports_per_bank,
            "sram_bank_efficiency": sram_bank_efficiency,
            "practical_active_banks": bank["active_banks"],
            "practical_local_banks_per_cluster": round(bank["local_banks_per_cluster"], 6),
            "practical_aggregate_bank_bytes_per_cycle": round(bank["aggregate_bank_bpc"], 6),
            "practical_local_bank_bytes_per_cycle_per_cluster": round(bank["local_bank_bpc_per_cluster"], 6),
            "practical_shared_bank_bytes_per_cycle_per_cluster": round(bank["shared_bank_bpc_per_cluster"], 6),
            "endpoint_port_bytes_per_cycle": endpoint_port_bytes_per_cycle,
            "endpoint_ports_per_cluster": endpoint_ports_per_cluster,
            "endpoint_efficiency": endpoint_efficiency,
            "endpoint_bytes_per_cycle_per_cluster": round(endpoint_bpc_per_cluster, 6),
            "endpoint_aggregate_bytes_per_cycle": round(endpoint_agg_bpc, 6),
            "practical_aggregate_noc_effective_bytes_per_cycle": round(practical_aggregate_noc_bpc, 6),
            "practical_per_cluster_noc_effective_bytes_per_cycle": round(practical_per_cluster_noc_bpc, 6),
            "practical_noc_cap_source": (
                "topology"
                if practical_aggregate_noc_bpc == topology_agg_bpc
                else "endpoint"
                if practical_aggregate_noc_bpc == endpoint_agg_bpc
                else "sram_bank"
            ),
            "tile_local_sram_cycles": tile_local_cycles,
            "tile_shared_bank_cycles": tile_shared_bank_cycles,
            "tile_noc_cycles": tile_noc_cycles,
            "tile_shared_path_cycles": tile_shared_path_cycles,
            "tile_memory_cycles": tile_memory_cycles,
            "tile_service_cycles": tile_service_cycles,
            "cross_tile_reduction_noc_cycles": reduction_noc_cycles,
            "base_cross_tile_reduction_cycles": base_reduction_cycles,
            "cross_tile_reduction_cycles": cross_tile_reduction_cycles,
            "kv_write_cycles": kv_write_cycles,
            "layer_cycles": layer_cycles,
            "total_cycles": total_cycles,
            "latency_us": round(total_cycles * clock_ns / 1000.0, 6),
            "dominant_tile_resource": dominant,
        }
    )
    constrained["latency_slowdown_vs_topology_derived"] = round(
        float(constrained["latency_us"]) / max(1e-9, float(row["latency_us"])),
        6,
    )
    return constrained, None


def _update_best(target: dict[tuple[Any, ...], JsonDict], keys: tuple[str, ...], row: JsonDict) -> None:
    key = tuple(row.get(item) for item in keys)
    current = target.get(key)
    if current is None or float(row["latency_us"]) < float(current["latency_us"]):
        target[key] = row


def _iter_generated_topology_rows(
    args: argparse.Namespace,
    *,
    repo_root: Path,
    stats: dict[str, Any],
) -> Iterable[JsonDict]:
    topology_payload = _load_json(repo_root / args.topology_pairs_json)
    topology_rows = topology_derived._topology_service_rows(topology_payload, limit=args.topology_row_limit)
    candidates = clustered._load_compute_candidates(
        repo_root=repo_root,
        tag_substring=args.tag_substring,
        compute_source=args.compute_source,
    )
    if args.compute_arch_list:
        allowed = set(args.compute_arch_list)
        candidates = [candidate for candidate in candidates if str(candidate["compute_arch"]) in allowed]
    if not candidates:
        raise RuntimeError("no measured compute candidates matched")
    measured_l1_profiles = clustered._load_measured_l1_profiles(
        repo_root=repo_root,
        costs_path=repo_root / args.measured_l1_costs if args.measured_l1_costs else None,
        profile_names=args.measured_l1_profile,
    )

    stats.update(
        {
            "source_mode": "full_topology_regeneration",
            "source_model": "llm_decoder_attention_kv_topology_derived_schedule_llama7b_v1",
            "topology_pairs_summary": topology_payload.get("summary", {}),
            "topology_service_rows_used": len(topology_rows),
            "topology_generated_row_count": 0,
            "topology_skipped_area_budget_count": 0,
        }
    )
    for service in topology_rows:
        cluster_count = int(service["cluster_count"])
        bank_count = int(service["bank_count"])
        local_sram_fraction = float(service["local_sram_fraction"])
        reduction_strategy = str(service["reduction_strategy"])
        noc_bw = topology_derived._equivalent_raw_noc_bandwidth(service)
        noc_hops = max(1, int(service["worst_hops"]))
        for sequence_length in args.sequence_length_list:
            for die_area_mm2 in args.die_area_mm2_list:
                for sram_area_fraction in args.sram_area_fraction:
                    for logic_area_fraction in args.logic_area_fraction:
                        for usable_sram_fraction in args.usable_sram_fraction:
                            for tile_tokens in args.tile_tokens_list:
                                for command_cycles_per_tile in args.command_cycles_per_tile:
                                    for command_cycles_per_wave in args.command_cycles_per_wave:
                                        for reducer_setup_cycles in args.reducer_setup_cycles:
                                            for reduction_cycle_multiplier in args.reduction_cycle_multiplier:
                                                for measured_l1_profile in measured_l1_profiles:
                                                    for candidate in candidates:
                                                        row = clustered._shape_row(
                                                            candidate=candidate,
                                                            die_area_mm2=die_area_mm2,
                                                            sram_area_fraction=sram_area_fraction,
                                                            logic_area_fraction=logic_area_fraction,
                                                            reserved_area_fraction=args.reserved_area_fraction,
                                                            sequence_length=sequence_length,
                                                            usable_sram_fraction=usable_sram_fraction,
                                                            local_sram_fraction=local_sram_fraction,
                                                            tile_tokens=tile_tokens,
                                                            bank_count=bank_count,
                                                            cluster_count=cluster_count,
                                                            noc_bandwidth_bytes_per_cycle=noc_bw,
                                                            noc_hops=noc_hops,
                                                            reduction_strategy=reduction_strategy,
                                                            vector_ops_per_mac=args.vector_ops_per_mac,
                                                            reduction_scalar_bytes=args.reduction_scalar_bytes,
                                                            command_cycles_per_tile=command_cycles_per_tile,
                                                            command_cycles_per_wave=command_cycles_per_wave,
                                                            reducer_setup_cycles=reducer_setup_cycles,
                                                            reduction_cycle_multiplier=reduction_cycle_multiplier,
                                                            measured_l1_profile=measured_l1_profile,
                                                        )
                                                        if row is None:
                                                            stats["topology_skipped_area_budget_count"] += 1
                                                            continue
                                                        stats["topology_generated_row_count"] += 1
                                                        yield topology_derived._annotate_topology(row, service)


def _source_rows(args: argparse.Namespace, *, repo_root: Path, stats: dict[str, Any]) -> Iterable[JsonDict]:
    if args.topology_pairs_json:
        yield from _iter_generated_topology_rows(args, repo_root=repo_root, stats=stats)
        return
    if not args.topology_derived_json:
        raise RuntimeError("one of --topology-derived-json or --topology-pairs-json is required")
    source_payload = _load_json(repo_root / args.topology_derived_json)
    rows = _dedupe_rows(source_payload, limit=args.frontier_row_limit)
    stats.update(
        {
            "source_mode": "retained_topology_rows",
            "source_model": source_payload.get("model"),
            "retained_source_row_count": len(rows),
        }
    )
    yield from rows


def build_report(args: argparse.Namespace) -> JsonDict:
    repo_root = args.repo_root
    sram_caps = _sram_profile_caps(_load_json(repo_root / args.sram_profile_json))
    source_stats: dict[str, Any] = {}

    best: JsonDict | None = None
    top_heap: list[tuple[float, int, JsonDict]] = []
    heap_counter = 0
    source_rows_used = 0
    generated = 0
    infeasible = Counter()
    dominance = Counter()
    cap_sources = Counter()
    best_by_topology: dict[tuple[Any, ...], JsonDict] = {}
    best_by_endpoint: dict[tuple[Any, ...], JsonDict] = {}
    best_by_die: dict[tuple[Any, ...], JsonDict] = {}

    for row in _source_rows(args, repo_root=repo_root, stats=source_stats):
        source_rows_used += 1
        for local_buffer_multiplier in args.local_buffer_multiplier:
            for sram_bank_efficiency in args.sram_bank_efficiency:
                for endpoint_port_bytes_per_cycle in args.endpoint_port_bytes_per_cycle:
                    for endpoint_ports_per_cluster in args.endpoint_ports_per_cluster:
                        for endpoint_efficiency in args.endpoint_efficiency:
                            constrained, reason = _apply_constraints(
                                row,
                                sram_caps=sram_caps,
                                local_buffer_multiplier=local_buffer_multiplier,
                                sram_bank_port_bytes_per_cycle=args.sram_bank_port_bytes_per_cycle,
                                sram_read_ports_per_bank=args.sram_read_ports_per_bank,
                                sram_bank_efficiency=sram_bank_efficiency,
                                endpoint_port_bytes_per_cycle=endpoint_port_bytes_per_cycle,
                                endpoint_ports_per_cluster=endpoint_ports_per_cluster,
                                endpoint_efficiency=endpoint_efficiency,
                            )
                            if constrained is None:
                                infeasible[reason or "unknown"] += 1
                                continue
                            generated += 1
                            dominance[str(constrained["dominant_tile_resource"])] += 1
                            cap_sources[str(constrained["practical_noc_cap_source"])] += 1
                            if best is None or float(constrained["latency_us"]) < float(best["latency_us"]):
                                best = constrained
                            entry = (-float(constrained["latency_us"]), heap_counter, constrained)
                            heap_counter += 1
                            if len(top_heap) < args.top_k:
                                heapq.heappush(top_heap, entry)
                            elif entry[0] > top_heap[0][0]:
                                heapq.heapreplace(top_heap, entry)
                            _update_best(best_by_topology, ("topology", "scheduler_policy", "reduction_strategy"), constrained)
                            _update_best(
                                best_by_endpoint,
                                (
                                    "endpoint_port_bytes_per_cycle",
                                    "endpoint_ports_per_cluster",
                                    "sram_bank_efficiency",
                                    "local_buffer_multiplier",
                                ),
                                constrained,
                            )
                            _update_best(best_by_die, ("sequence_length", "die_area_mm2"), constrained)
    if best is None:
        raise RuntimeError(f"no feasible practical SRAM/NoC rows; infeasible={dict(infeasible)}")
    top_rows = [entry[2] for entry in sorted(top_heap, key=lambda entry: (entry[2]["latency_us"], entry[1]))]
    return {
        "version": 1,
        "model": "llm_decoder_attention_kv_sram_noc_constrained_schedule_llama7b_v1",
        "topology_derived_json": str(args.topology_derived_json or ""),
        "topology_pairs_json": str(args.topology_pairs_json or ""),
        "sram_profile_json": str(args.sram_profile_json),
        "source_model": source_stats.get("source_model"),
        "inputs": {
            "frontier_row_limit": args.frontier_row_limit,
            "topology_row_limit": args.topology_row_limit,
            "sequence_length_list": args.sequence_length_list,
            "die_area_mm2_list": args.die_area_mm2_list,
            "sram_area_fraction": args.sram_area_fraction,
            "logic_area_fraction": args.logic_area_fraction,
            "reserved_area_fraction": args.reserved_area_fraction,
            "usable_sram_fraction": args.usable_sram_fraction,
            "tile_tokens_list": args.tile_tokens_list,
            "compute_source": args.compute_source,
            "compute_arch_list": args.compute_arch_list,
            "tag_substring": args.tag_substring,
            "measured_l1_costs": str(args.measured_l1_costs),
            "measured_l1_profile": args.measured_l1_profile,
            "sram_bank_port_bytes_per_cycle": args.sram_bank_port_bytes_per_cycle,
            "sram_read_ports_per_bank": args.sram_read_ports_per_bank,
            "sram_bank_efficiency": args.sram_bank_efficiency,
            "endpoint_port_bytes_per_cycle": args.endpoint_port_bytes_per_cycle,
            "endpoint_ports_per_cluster": args.endpoint_ports_per_cluster,
            "endpoint_efficiency": args.endpoint_efficiency,
            "local_buffer_multiplier": args.local_buffer_multiplier,
        },
        "sram_caps": sram_caps,
        "sweep_summary": {
            "source_rows_used": source_rows_used,
            "generated_row_count": generated,
            **source_stats,
            "infeasible_counts": dict(sorted(infeasible.items())),
            "dominant_tile_resource_counts": dict(sorted(dominance.items())),
            "practical_noc_cap_source_counts": dict(sorted(cap_sources.items())),
        },
        "best": best,
        "top_rows": top_rows,
        "best_by_topology": sorted(best_by_topology.values(), key=lambda row: row["latency_us"])[:100],
        "best_by_endpoint": sorted(best_by_endpoint.values(), key=lambda row: row["latency_us"])[:100],
        "best_by_die": sorted(best_by_die.values(), key=lambda row: (row["sequence_length"], row["die_area_mm2"])),
        "assumptions": [
            (
                "Input rows are regenerated from the topology/scheduler pair matrix before practical SRAM/NoC caps are applied."
                if args.topology_pairs_json
                else "Input rows are retained frontier rows from the topology-derived scheduler, not a full re-search of all generated rows."
            ),
            "SRAM bank service is capped by measured 256-bit tile-buffer bank width unless overridden by the CLI.",
            "NoC service is capped by the minimum of topology aggregate payload service, endpoint injection/ejection service, and practical SRAM bank read service.",
            "Local tile-buffer capacity is required per cluster; full KV-cache residency remains the higher-level HBM/SRAM capacity model from the source schedule.",
            "This is still analytic scheduling evidence, not cycle-accurate SRAM arbitration or routed NoC RTL.",
        ],
    }


def write_markdown(path: Path, payload: JsonDict) -> None:
    best = payload["best"]
    lines = [
        "# Llama7B Practical SRAM/NoC Constrained Schedule",
        "",
        f"- source rows used: `{payload['sweep_summary']['source_rows_used']}`",
        f"- generated rows: `{payload['sweep_summary']['generated_row_count']}`",
        f"- infeasible counts: `{payload['sweep_summary']['infeasible_counts']}`",
        f"- NoC cap sources: `{payload['sweep_summary']['practical_noc_cap_source_counts']}`",
        "",
        "## Best",
        "",
        "| topology | scheduler | reduction | clusters | link bits | endpoint B/cyc/cluster | SRAM bank B/cyc/cluster | NoC agg B/cyc | replicas | die | latency us | slowdown | resource | cap |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|",
        "| {topology} | {scheduler_policy} | {reduction_strategy} | {cluster_count} | {link_width_bits} | "
        "{endpoint_bytes_per_cycle_per_cluster} | {practical_shared_bank_bytes_per_cycle_per_cluster} | "
        "{practical_aggregate_noc_effective_bytes_per_cycle} | {compute_replica_count} | {die_area_mm2} | "
        "{latency_us} | {latency_slowdown_vs_topology_derived} | {dominant_tile_resource} | {practical_noc_cap_source} |".format(
            **best
        ),
        "",
        "## Best By Endpoint/SRAM Setting",
        "",
        "| endpoint B/cyc | endpoint ports | bank eff | buffer x | topology | latency us | slowdown | resource |",
        "|---:|---:|---:|---:|---|---:|---:|---|",
    ]
    for row in payload["best_by_endpoint"][:30]:
        lines.append(
            "| {endpoint_port_bytes_per_cycle} | {endpoint_ports_per_cluster} | {sram_bank_efficiency} | "
            "{local_buffer_multiplier} | {topology}/{scheduler_policy} | {latency_us} | "
            "{latency_slowdown_vs_topology_derived} | {dominant_tile_resource} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Best By Topology",
            "",
            "| topology | scheduler | reduction | clusters | link bits | latency us | slowdown | resource | cap |",
            "|---|---|---|---:|---:|---:|---:|---|---|",
        ]
    )
    for row in payload["best_by_topology"][:30]:
        lines.append(
            "| {topology} | {scheduler_policy} | {reduction_strategy} | {cluster_count} | {link_width_bits} | "
            "{latency_us} | {latency_slowdown_vs_topology_derived} | {dominant_tile_resource} | "
            "{practical_noc_cap_source} |".format(**row)
        )
    lines.extend(["", "## Assumptions", ""])
    lines.extend(f"- {item}" for item in payload["assumptions"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-root", type=Path, default=Path("."))
    ap.add_argument("--topology-derived-json", type=Path)
    ap.add_argument("--topology-pairs-json", type=Path)
    ap.add_argument("--sram-profile-json", required=True, type=Path)
    ap.add_argument("--frontier-row-limit", type=int, default=256)
    ap.add_argument("--tag-substring", default="npu_dense_gemm_tile_v2_scale_hier")
    ap.add_argument("--compute-source", choices=["legacy_npu_block", "dense_gemm_tile", "all"], default="dense_gemm_tile")
    ap.add_argument("--compute-arch-list", type=_optional_str_list, default=["dense_gemm_16x8_k1_p1"])
    ap.add_argument("--sequence-length-list", type=_int_list, default=[131072])
    ap.add_argument("--die-area-mm2-list", type=_float_list, default=[800, 1200])
    ap.add_argument("--sram-area-fraction", type=_float_list, default=[0.35, 0.4, 0.5, 0.6])
    ap.add_argument("--logic-area-fraction", type=_float_list, default=[0.3, 0.4, 0.5])
    ap.add_argument("--reserved-area-fraction", type=float, default=0.1)
    ap.add_argument("--usable-sram-fraction", type=_float_list, default=[0.7])
    ap.add_argument("--tile-tokens-list", type=_int_list, default=[512, 1024])
    ap.add_argument("--topology-row-limit", type=int, default=128)
    ap.add_argument("--vector-ops-per-mac", type=float, default=0.125)
    ap.add_argument("--reduction-scalar-bytes", type=int, default=2)
    ap.add_argument("--command-cycles-per-tile", type=_nonnegative_int_list, default=[0, 4, 16])
    ap.add_argument("--command-cycles-per-wave", type=_nonnegative_int_list, default=[0, 16, 64])
    ap.add_argument("--reducer-setup-cycles", type=_nonnegative_int_list, default=[0, 64, 256])
    ap.add_argument("--reduction-cycle-multiplier", type=_float_list, default=[1.0, 2.0, 4.0])
    ap.add_argument("--measured-l1-costs", default="")
    ap.add_argument("--measured-l1-profile", type=_profile_list, default=["hd64_kv8_full_value_p8_ppc2_noc128_softmax_int8_q10"])
    ap.add_argument("--sram-bank-port-bytes-per-cycle", type=float, default=32.0)
    ap.add_argument("--sram-read-ports-per-bank", type=int, default=1)
    ap.add_argument("--sram-bank-efficiency", type=_float_list, default=[0.70, 0.85])
    ap.add_argument("--endpoint-port-bytes-per-cycle", type=_float_list, default=[32.0, 64.0, 128.0])
    ap.add_argument("--endpoint-ports-per-cluster", type=_int_list, default=[1, 2])
    ap.add_argument("--endpoint-efficiency", type=_float_list, default=[0.70, 0.85])
    ap.add_argument("--local-buffer-multiplier", type=_float_list, default=[1.0, 2.0])
    ap.add_argument("--top-k", type=int, default=50)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--out-md", required=True, type=Path)
    args = ap.parse_args()
    if not args.topology_derived_json and not args.topology_pairs_json:
        ap.error("one of --topology-derived-json or --topology-pairs-json is required")

    payload = build_report(args)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(args.out_md, payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
