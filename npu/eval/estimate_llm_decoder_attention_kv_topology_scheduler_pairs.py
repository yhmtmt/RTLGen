#!/usr/bin/env python3
"""Enumerate logically valid NoC topology/scheduler pairs for Llama7B attention."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


JsonDict = dict[str, Any]


def _str_list(value: str) -> list[str]:
    items = [item.strip() for item in value.split(",") if item.strip()]
    if not items:
        raise argparse.ArgumentTypeError("expected comma-separated names")
    return items


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
    return int(math.ceil(float(numerator) / float(denominator)))


def _load_frontier(path: Path | None) -> JsonDict:
    if path is None or not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    best = payload.get("best") or {}
    return best if isinstance(best, dict) else {}


def _mesh_dims(cluster_count: int) -> tuple[int, int]:
    best = (1, cluster_count)
    best_delta = cluster_count - 1
    for rows in range(1, int(math.sqrt(cluster_count)) + 1):
        if cluster_count % rows == 0:
            cols = cluster_count // rows
            delta = abs(cols - rows)
            if delta < best_delta:
                best = (rows, cols)
                best_delta = delta
    return best


def _average_mesh_hops(rows: int, cols: int) -> float:
    nodes = [(r, c) for r in range(rows) for c in range(cols)]
    if len(nodes) <= 1:
        return 0.0
    total = 0
    pairs = 0
    for src_r, src_c in nodes:
        for dst_r, dst_c in nodes:
            if (src_r, src_c) == (dst_r, dst_c):
                continue
            total += abs(src_r - dst_r) + abs(src_c - dst_c)
            pairs += 1
    return total / pairs


def _average_ring_hops(cluster_count: int) -> float:
    if cluster_count <= 1:
        return 0.0
    total = 0
    pairs = 0
    for src in range(cluster_count):
        for dst in range(cluster_count):
            if src == dst:
                continue
            delta = abs(src - dst)
            total += min(delta, cluster_count - delta)
            pairs += 1
    return total / pairs


def _vc_efficiency(virtual_channels: int) -> float:
    return min(1.0, 0.80 + 0.06 * max(0, virtual_channels - 1))


def _topology_service(
    *,
    topology: str,
    cluster_count: int,
    link_width_bits: int,
    virtual_channels: int,
) -> JsonDict:
    link_bytes = link_width_bits / 8.0
    vc_eff = _vc_efficiency(virtual_channels)
    if topology == "local_only":
        return {
            "average_hops": 0.0,
            "worst_hops": 0,
            "active_links": 0,
            "router_radix": 1,
            "aggregate_payload_bytes_per_cycle": 0.0,
            "topology_area_proxy": 0.0,
            "mesh_rows": 1,
            "mesh_cols": cluster_count,
        }
    if topology == "crossbar":
        return {
            "average_hops": 1.0,
            "worst_hops": 1,
            "active_links": cluster_count,
            "router_radix": cluster_count,
            "aggregate_payload_bytes_per_cycle": round(cluster_count * link_bytes * 0.78 * vc_eff, 6),
            "topology_area_proxy": round(cluster_count * cluster_count, 6),
            "mesh_rows": 1,
            "mesh_cols": cluster_count,
        }
    if topology == "ring":
        return {
            "average_hops": round(_average_ring_hops(cluster_count), 6),
            "worst_hops": cluster_count // 2,
            "active_links": cluster_count,
            "router_radix": 2,
            "aggregate_payload_bytes_per_cycle": round(cluster_count * link_bytes * 0.58 * vc_eff, 6),
            "topology_area_proxy": round(cluster_count * 1.4, 6),
            "mesh_rows": 1,
            "mesh_cols": cluster_count,
        }
    if topology == "mesh2d":
        rows, cols = _mesh_dims(cluster_count)
        undirected_links = rows * (cols - 1) + cols * (rows - 1)
        return {
            "average_hops": round(_average_mesh_hops(rows, cols), 6),
            "worst_hops": rows + cols - 2,
            "active_links": undirected_links,
            "router_radix": 4,
            "aggregate_payload_bytes_per_cycle": round(undirected_links * link_bytes * 0.64 * vc_eff, 6),
            "topology_area_proxy": round(cluster_count * 2.2 + undirected_links, 6),
            "mesh_rows": rows,
            "mesh_cols": cols,
        }
    if topology == "cluster_tree":
        depth = int(math.ceil(math.log2(cluster_count))) if cluster_count > 1 else 0
        concurrent_links = max(1, cluster_count // 2)
        return {
            "average_hops": float(depth),
            "worst_hops": depth,
            "active_links": concurrent_links,
            "router_radix": 3,
            "aggregate_payload_bytes_per_cycle": round(concurrent_links * link_bytes * 0.70 * vc_eff, 6),
            "topology_area_proxy": round((cluster_count - 1) * 1.8, 6),
            "mesh_rows": 1,
            "mesh_cols": cluster_count,
        }
    raise ValueError(f"unknown topology: {topology}")


def _invalid_reasons(
    *,
    topology: str,
    scheduler_policy: str,
    reduction_strategy: str,
    bank_placement: str,
    cluster_count: int,
    bank_count: int,
    virtual_channels: int,
    local_sram_fraction: float,
    shared_byte_share: float,
) -> list[str]:
    reasons: list[str] = []
    if topology == "local_only":
        if cluster_count != 1:
            reasons.append("local_only topology cannot route between multiple clusters")
        if shared_byte_share > 0.0:
            reasons.append("local_only topology cannot serve shared-KV traffic")
        if reduction_strategy != "owner_cluster":
            reasons.append("local_only topology requires owner_cluster reduction")
        if bank_placement != "per_cluster_local":
            reasons.append("local_only topology requires per_cluster_local banks")
    if topology == "crossbar":
        if cluster_count > 8:
            reasons.append("crossbar is rejected above 8 clusters because switch cost grows quadratically")
        if reduction_strategy == "cluster_tree":
            reasons.append("crossbar does not expose a physical tree reduction fabric")
        if scheduler_policy == "tree_reduction_aware":
            reasons.append("tree_reduction_aware scheduler requires a tree or mesh spanning tree")
    if topology == "ring":
        if cluster_count < 2:
            reasons.append("ring topology requires at least 2 clusters")
        if cluster_count > 16:
            reasons.append("ring is rejected above 16 clusters because worst-hop latency is unbounded for this target")
        if reduction_strategy == "cluster_tree":
            reasons.append("ring topology should use owner_cluster or centralized reduction, not cluster_tree")
        if scheduler_policy == "tree_reduction_aware":
            reasons.append("tree_reduction_aware scheduler is not compatible with a plain ring")
    if topology == "mesh2d":
        if cluster_count < 4:
            reasons.append("mesh2d topology requires at least 4 clusters")
        if scheduler_policy == "static_wave" and cluster_count > 8:
            reasons.append("static_wave on a large mesh ignores placement and creates avoidable hot spots")
    if topology == "cluster_tree":
        if cluster_count < 2:
            reasons.append("cluster_tree topology requires at least 2 clusters")
        if reduction_strategy == "centralized_tile" and cluster_count > 4:
            reasons.append("centralized_tile bottlenecks a cluster_tree above 4 clusters")
    if reduction_strategy == "centralized_tile" and cluster_count > 4:
        reasons.append("centralized_tile reduction is rejected above 4 clusters")
    if reduction_strategy == "cluster_tree" and topology not in {"cluster_tree", "mesh2d"}:
        reasons.append("cluster_tree reduction requires cluster_tree topology or a mesh spanning tree")
    if scheduler_policy == "bank_aware_prefetch":
        if bank_placement == "per_cluster_local":
            reasons.append("bank_aware_prefetch requires shared or distributed banks")
        if bank_count < cluster_count:
            reasons.append("bank_aware_prefetch requires at least one bank per cluster")
        if virtual_channels < 2:
            reasons.append("bank_aware_prefetch requires at least 2 virtual channels")
    if scheduler_policy == "double_buffered_overlap":
        if local_sram_fraction < 0.05:
            reasons.append("double_buffered_overlap requires local_sram_fraction >= 0.05")
        if virtual_channels < 2:
            reasons.append("double_buffered_overlap requires at least 2 virtual channels")
    if scheduler_policy == "tree_reduction_aware":
        if reduction_strategy != "cluster_tree":
            reasons.append("tree_reduction_aware scheduler requires cluster_tree reduction")
        if topology not in {"cluster_tree", "mesh2d"}:
            reasons.append("tree_reduction_aware scheduler requires cluster_tree topology or mesh2d")
    if scheduler_policy == "locality_aware" and bank_placement == "distributed_shared" and virtual_channels < 2:
        reasons.append("distributed_shared locality scheduling requires at least 2 virtual channels")
    if bank_placement == "grouped_shared" and cluster_count < 4:
        reasons.append("grouped_shared placement is not meaningful below 4 clusters")
    return reasons


def _traffic_quantities(args: argparse.Namespace, frontier_best: JsonDict) -> JsonDict:
    hidden_size = int(frontier_best.get("hidden_size", args.hidden_size))
    attention_heads = int(frontier_best.get("attention_heads", args.attention_heads))
    kv_heads = int(frontier_best.get("kv_heads", args.kv_heads))
    kv_bits = int(frontier_best.get("kv_bits", args.kv_bits))
    tile_tokens = int(frontier_best.get("tile_tokens", args.tile_tokens))
    shared_byte_share = float(frontier_best.get("shared_byte_share", args.shared_byte_share))
    head_dim = hidden_size // attention_heads
    kv_width = kv_heads * head_dim
    full_tile_kv_bytes = int(2 * tile_tokens * kv_width * kv_bits / 8)
    shared_tile_payload_bytes = int(math.ceil(full_tile_kv_bytes * shared_byte_share))
    partial_reduction_payload_bytes = int(
        frontier_best.get(
            "partial_reduction_payload_bytes",
            attention_heads * 2 * args.reduction_scalar_bytes + hidden_size * args.reduction_scalar_bytes,
        )
    )
    previous_noc_bandwidth = float(frontier_best.get("noc_bandwidth_bytes_per_cycle", 0.0))
    previous_noc_hops = int(frontier_best.get("noc_hops", 0))
    return {
        "hidden_size": hidden_size,
        "attention_heads": attention_heads,
        "kv_heads": kv_heads,
        "kv_bits": kv_bits,
        "tile_tokens": tile_tokens,
        "shared_byte_share": round(shared_byte_share, 6),
        "full_tile_kv_bytes": full_tile_kv_bytes,
        "shared_tile_payload_bytes": shared_tile_payload_bytes,
        "partial_reduction_payload_bytes": partial_reduction_payload_bytes,
        "previous_noc_bandwidth_bytes_per_cycle": previous_noc_bandwidth,
        "previous_noc_hops": previous_noc_hops,
    }


def build_pairs(args: argparse.Namespace) -> JsonDict:
    frontier_best = _load_frontier(args.frontier_json)
    traffic = _traffic_quantities(args, frontier_best)
    valid_rows: list[JsonDict] = []
    invalid_rows: list[JsonDict] = []
    invalid_reason_counts: Counter[str] = Counter()

    for cluster_count in args.cluster_count_list:
        for topology in args.topology_list:
            for scheduler_policy in args.scheduler_policy_list:
                for reduction_strategy in args.reduction_strategy_list:
                    for bank_placement in args.bank_placement_list:
                        for bank_count in args.bank_count_list:
                            for link_width_bits in args.link_width_bits_list:
                                for virtual_channels in args.virtual_channel_list:
                                    for local_sram_fraction in args.local_sram_fraction_list:
                                        service = _topology_service(
                                            topology=topology,
                                            cluster_count=cluster_count,
                                            link_width_bits=link_width_bits,
                                            virtual_channels=virtual_channels,
                                        )
                                        reasons = _invalid_reasons(
                                            topology=topology,
                                            scheduler_policy=scheduler_policy,
                                            reduction_strategy=reduction_strategy,
                                            bank_placement=bank_placement,
                                            cluster_count=cluster_count,
                                            bank_count=bank_count,
                                            virtual_channels=virtual_channels,
                                            local_sram_fraction=local_sram_fraction,
                                            shared_byte_share=traffic["shared_byte_share"],
                                        )
                                        base = {
                                            "cluster_count": cluster_count,
                                            "topology": topology,
                                            "scheduler_policy": scheduler_policy,
                                            "reduction_strategy": reduction_strategy,
                                            "bank_placement": bank_placement,
                                            "bank_count": bank_count,
                                            "link_width_bits": link_width_bits,
                                            "virtual_channels": virtual_channels,
                                            "local_sram_fraction": local_sram_fraction,
                                        }
                                        if reasons:
                                            invalid_rows.append({**base, "invalid_reasons": reasons})
                                            invalid_reason_counts.update(reasons)
                                            continue

                                        aggregate_bpc = float(service["aggregate_payload_bytes_per_cycle"])
                                        per_cluster_bpc = aggregate_bpc / max(1, cluster_count)
                                        if aggregate_bpc <= 0.0:
                                            shared_cycles = 0
                                            reduction_cycles = 0
                                            previous_bandwidth_gap = None
                                        else:
                                            shared_cycles = _ceil_div(
                                                traffic["shared_tile_payload_bytes"],
                                                max(1.0, per_cluster_bpc),
                                            )
                                            reduction_cycles = _ceil_div(
                                                cluster_count * traffic["partial_reduction_payload_bytes"],
                                                aggregate_bpc,
                                            )
                                            previous = traffic["previous_noc_bandwidth_bytes_per_cycle"]
                                            previous_bandwidth_gap = round(previous / aggregate_bpc, 6) if previous else None
                                        router_cycles = int(math.ceil(service["worst_hops"] * args.router_latency_cycles_per_hop))
                                        service_cycles = max(shared_cycles, reduction_cycles) + router_cycles
                                        complexity = float(service["topology_area_proxy"])
                                        scheduler_penalty = {
                                            "static_wave": 0.0,
                                            "locality_aware": 0.5,
                                            "bank_aware_prefetch": 1.0,
                                            "tree_reduction_aware": 0.75,
                                            "double_buffered_overlap": 1.25,
                                        }.get(scheduler_policy, 1.0)
                                        proxy_score = service_cycles + complexity * args.area_proxy_cycle_weight + scheduler_penalty
                                        valid_rows.append(
                                            {
                                                **base,
                                                **service,
                                                "aggregate_payload_bytes_per_cycle": aggregate_bpc,
                                                "per_cluster_payload_bytes_per_cycle": round(per_cluster_bpc, 6),
                                                "shared_tile_noc_cycles": shared_cycles,
                                                "cross_tile_reduction_noc_cycles": reduction_cycles,
                                                "router_latency_cycles": router_cycles,
                                                "proxy_service_cycles": service_cycles,
                                                "proxy_score": round(proxy_score, 6),
                                                "previous_bandwidth_gap": previous_bandwidth_gap,
                                                "can_match_previous_one_hop_service": (
                                                    previous_bandwidth_gap is not None
                                                    and previous_bandwidth_gap <= 1.25
                                                    and service["worst_hops"] <= max(1, traffic["previous_noc_hops"])
                                                ),
                                            }
                                        )

    best_rows = sorted(
        valid_rows,
        key=lambda row: (
            row["proxy_score"],
            row["proxy_service_cycles"],
            row["topology_area_proxy"],
            row["link_width_bits"],
        ),
    )[: args.top_k]
    matrix: dict[str, dict[str, int]] = defaultdict(lambda: {"valid": 0, "invalid": 0})
    for row in valid_rows:
        matrix[f"{row['topology']}:{row['scheduler_policy']}"]["valid"] += 1
    for row in invalid_rows:
        matrix[f"{row['topology']}:{row['scheduler_policy']}"]["invalid"] += 1

    return {
        "version": 1,
        "model": "llama7b_proxy",
        "profile": "decoder_attention_kv_dense_tile_topology_scheduler_pairs",
        "frontier_json": str(args.frontier_json) if args.frontier_json else None,
        "traffic_quantities": traffic,
        "parameters": {
            "cluster_count_list": args.cluster_count_list,
            "topology_list": args.topology_list,
            "scheduler_policy_list": args.scheduler_policy_list,
            "reduction_strategy_list": args.reduction_strategy_list,
            "bank_placement_list": args.bank_placement_list,
            "bank_count_list": args.bank_count_list,
            "link_width_bits_list": args.link_width_bits_list,
            "virtual_channel_list": args.virtual_channel_list,
            "local_sram_fraction_list": args.local_sram_fraction_list,
            "router_latency_cycles_per_hop": args.router_latency_cycles_per_hop,
            "area_proxy_cycle_weight": args.area_proxy_cycle_weight,
        },
        "summary": {
            "valid_pair_count": len(valid_rows),
            "invalid_pair_count": len(invalid_rows),
            "top_invalid_reasons": invalid_reason_counts.most_common(12),
            "validity_matrix": dict(sorted(matrix.items())),
        },
        "best_valid_pairs": best_rows,
        "valid_pairs": valid_rows,
        "invalid_pairs": invalid_rows,
        "remaining_abstractions": [
            "This pass validates topology/scheduler/reducer/bank-placement compatibility and derives service envelopes from link widths.",
            "It does not perform cycle-accurate NoC routing, SRAM banking simulation, or RTL physical closure of the chosen fabric.",
            "Valid rows should feed the next clustered schedule run instead of sweeping independent noc_bandwidth/noc_hops/reduction knobs.",
        ],
    }


def write_report(payload: JsonDict, report: Path) -> None:
    lines = [
        "# Llama7B Dense-Tile Topology/Scheduler Pairs",
        "",
        "## Summary",
        "",
        f"- valid pairs: `{payload['summary']['valid_pair_count']}`",
        f"- invalid pairs: `{payload['summary']['invalid_pair_count']}`",
        f"- previous frontier NoC service: `{payload['traffic_quantities']['previous_noc_bandwidth_bytes_per_cycle']}` B/cycle, "
        f"`{payload['traffic_quantities']['previous_noc_hops']}` hop",
        "",
        "## Best Valid Proxy Rows",
        "",
        "| topology | scheduler | reduction | bank placement | clusters | banks | local SRAM | link bits | vc | agg B/cyc | worst hops | shared cyc | red cyc | gap to previous BW |",
        "|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in payload["best_valid_pairs"]:
        gap = row["previous_bandwidth_gap"]
        gap_text = "" if gap is None else str(gap)
        lines.append(
            "| {topology} | {scheduler_policy} | {reduction_strategy} | {bank_placement} | {cluster_count} | "
            "{bank_count} | {local_sram_fraction} | {link_width_bits} | {virtual_channels} | "
            "{aggregate_payload_bytes_per_cycle} | {worst_hops} | {shared_tile_noc_cycles} | "
            "{cross_tile_reduction_noc_cycles} | {gap} |".format(**row, gap=gap_text)
        )
    lines.extend(
        [
            "",
            "## Common Invalid Reasons",
            "",
            "| reason | count |",
            "|---|---:|",
        ]
    )
    for reason, count in payload["summary"]["top_invalid_reasons"]:
        lines.append(f"| {reason} | {count} |")
    lines.extend(
        [
            "",
            "## Validity Matrix",
            "",
            "| topology:scheduler | valid | invalid |",
            "|---|---:|---:|",
        ]
    )
    for key, counts in payload["summary"]["validity_matrix"].items():
        lines.append(f"| {key} | {counts['valid']} | {counts['invalid']} |")
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- The previous 65kB/cycle, one-hop point is treated as a service target, not a proven topology.",
            "- Valid pairs from this report are candidates for the next scheduler/performance sweep.",
        ]
    )
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--frontier-json", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--out-md", required=True, type=Path)
    parser.add_argument("--cluster-count-list", type=_int_list, default=[4, 8, 16])
    parser.add_argument("--topology-list", type=_str_list, default=["cluster_tree", "mesh2d", "ring", "crossbar"])
    parser.add_argument(
        "--scheduler-policy-list",
        type=_str_list,
        default=["static_wave", "locality_aware", "bank_aware_prefetch", "tree_reduction_aware", "double_buffered_overlap"],
    )
    parser.add_argument(
        "--reduction-strategy-list",
        type=_str_list,
        default=["centralized_tile", "owner_cluster", "cluster_tree"],
    )
    parser.add_argument(
        "--bank-placement-list",
        type=_str_list,
        default=["per_cluster_local", "grouped_shared", "distributed_shared"],
    )
    parser.add_argument("--bank-count-list", type=_int_list, default=[16, 64, 128])
    parser.add_argument("--link-width-bits-list", type=_int_list, default=[256, 512, 1024, 2048])
    parser.add_argument("--virtual-channel-list", type=_int_list, default=[1, 2, 4])
    parser.add_argument("--local-sram-fraction-list", type=_float_list, default=[0.05, 0.1, 0.25])
    parser.add_argument("--hidden-size", type=int, default=4096)
    parser.add_argument("--attention-heads", type=int, default=32)
    parser.add_argument("--kv-heads", type=int, default=4)
    parser.add_argument("--kv-bits", type=int, default=8)
    parser.add_argument("--tile-tokens", type=int, default=1024)
    parser.add_argument("--shared-byte-share", type=float, default=0.406435)
    parser.add_argument("--reduction-scalar-bytes", type=int, default=2)
    parser.add_argument("--router-latency-cycles-per-hop", type=int, default=2)
    parser.add_argument("--area-proxy-cycle-weight", type=float, default=0.05)
    parser.add_argument("--top-k", type=int, default=24)
    args = parser.parse_args()

    allowed_topologies = {"local_only", "cluster_tree", "mesh2d", "ring", "crossbar"}
    allowed_schedulers = {
        "static_wave",
        "locality_aware",
        "bank_aware_prefetch",
        "tree_reduction_aware",
        "double_buffered_overlap",
    }
    allowed_reductions = {"centralized_tile", "owner_cluster", "cluster_tree"}
    allowed_bank_placements = {"per_cluster_local", "grouped_shared", "distributed_shared"}
    if unknown := sorted(set(args.topology_list) - allowed_topologies):
        raise SystemExit(f"unknown topology names: {unknown}")
    if unknown := sorted(set(args.scheduler_policy_list) - allowed_schedulers):
        raise SystemExit(f"unknown scheduler policy names: {unknown}")
    if unknown := sorted(set(args.reduction_strategy_list) - allowed_reductions):
        raise SystemExit(f"unknown reduction strategy names: {unknown}")
    if unknown := sorted(set(args.bank_placement_list) - allowed_bank_placements):
        raise SystemExit(f"unknown bank placement names: {unknown}")
    if args.hidden_size % args.attention_heads != 0:
        raise SystemExit("--hidden-size must be divisible by --attention-heads")
    if any(width % 8 != 0 for width in args.link_width_bits_list):
        raise SystemExit("--link-width-bits-list values must be multiples of 8")

    if args.frontier_json and not args.frontier_json.is_absolute():
        args.frontier_json = args.repo_root / args.frontier_json
    payload = build_pairs(args)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_report(payload, args.out_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
