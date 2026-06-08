#!/usr/bin/env python3
"""Estimate dense-tile Llama7B schedules from valid topology-derived NoC service rows."""

from __future__ import annotations

import argparse
import heapq
import json
import math
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from npu.eval import estimate_llm_decoder_attention_kv_clustered_schedule as clustered  # noqa: E402


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


def _float_list(value: str) -> list[float]:
    items = [float(item.strip()) for item in value.split(",") if item.strip()]
    if not items or any(item <= 0.0 for item in items):
        raise argparse.ArgumentTypeError("expected comma-separated positive floats")
    return items


def _optional_str_list(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _profile_list(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _load_json(path: Path) -> JsonDict:
    return json.loads(path.read_text(encoding="utf-8"))


def _topology_service_rows(payload: JsonDict, *, limit: int) -> list[JsonDict]:
    raw_rows = list(payload.get("valid_service_envelopes") or payload.get("best_valid_pairs") or [])
    raw_rows.extend(payload.get("best_valid_pairs") or [])
    rows: list[JsonDict] = []
    seen: set[tuple[Any, ...]] = set()
    for row in sorted(
        raw_rows,
        key=lambda item: (
            float(item.get("proxy_score", 0.0)),
            float(item.get("proxy_service_cycles", 0.0)),
            str(item.get("topology", "")),
            str(item.get("scheduler_policy", "")),
            int(item.get("cluster_count", 0)),
        ),
    ):
        aggregate_bpc = float(row["aggregate_payload_bytes_per_cycle"])
        if aggregate_bpc <= 0.0:
            continue
        key = (
            str(row["topology"]),
            str(row["scheduler_policy"]),
            str(row["reduction_strategy"]),
            str(row["bank_placement"]),
            int(row["cluster_count"]),
            int(row["bank_count"]),
            float(row["local_sram_fraction"]),
            int(row["link_width_bits"]),
            int(row["virtual_channels"]),
            int(row["worst_hops"]),
            round(aggregate_bpc, 6),
        )
        if key in seen:
            continue
        seen.add(key)
        rows.append(row)
        if len(rows) >= limit:
            break
    if not rows:
        raise RuntimeError("no usable topology service rows found")
    return rows


def _equivalent_raw_noc_bandwidth(row: JsonDict) -> float:
    """Invert clustered._shape_row's fixed NoC efficiency while preserving hop latency."""
    aggregate_payload_bpc = float(row["aggregate_payload_bytes_per_cycle"])
    worst_hops = max(1, int(row["worst_hops"]))
    return aggregate_payload_bpc * worst_hops / 0.85


def _annotate_topology(row: JsonDict, service: JsonDict) -> JsonDict:
    topology_fields = {
        "topology": service.get("topology"),
        "scheduler_policy": service.get("scheduler_policy"),
        "bank_placement": service.get("bank_placement"),
        "link_width_bits": service.get("link_width_bits"),
        "virtual_channels": service.get("virtual_channels"),
        "topology_average_hops": service.get("average_hops"),
        "topology_worst_hops": service.get("worst_hops"),
        "topology_active_links": service.get("active_links"),
        "topology_router_radix": service.get("router_radix"),
        "topology_area_proxy": service.get("topology_area_proxy"),
        "topology_proxy_score": service.get("proxy_score"),
        "topology_proxy_service_cycles": service.get("proxy_service_cycles"),
        "topology_previous_bandwidth_gap": service.get("previous_bandwidth_gap"),
        "topology_aggregate_payload_bytes_per_cycle": service.get("aggregate_payload_bytes_per_cycle"),
        "topology_per_cluster_payload_bytes_per_cycle": service.get("per_cluster_payload_bytes_per_cycle"),
        "topology_shared_tile_noc_cycles": service.get("shared_tile_noc_cycles"),
        "topology_cross_tile_reduction_noc_cycles": service.get("cross_tile_reduction_noc_cycles"),
        "topology_service_source": "decoder_attention_kv_dense_tile_topology_scheduler_pairs",
    }
    row.update(topology_fields)
    return row


def _update_best(target: dict[tuple[Any, ...], JsonDict], keys: tuple[str, ...], row: JsonDict) -> None:
    key = tuple(row.get(item) for item in keys)
    current = target.get(key)
    if current is None or float(row["latency_us"]) < float(current["latency_us"]):
        target[key] = row


def build_report(args: argparse.Namespace) -> JsonDict:
    repo_root = args.repo_root
    topology_payload = _load_json(repo_root / args.topology_pairs_json)
    topology_rows = _topology_service_rows(topology_payload, limit=args.topology_row_limit)
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

    best: JsonDict | None = None
    generated_row_count = 0
    skipped_area_budget = 0
    dominance: dict[str, int] = {}
    top_heap: list[tuple[float, int, JsonDict]] = []
    heap_counter = 0
    best_by_topology: dict[tuple[Any, ...], JsonDict] = {}
    best_by_scheduler: dict[tuple[Any, ...], JsonDict] = {}
    best_by_die: dict[tuple[Any, ...], JsonDict] = {}
    best_by_die_topology: dict[tuple[Any, ...], JsonDict] = {}

    for service in topology_rows:
        cluster_count = int(service["cluster_count"])
        bank_count = int(service["bank_count"])
        local_sram_fraction = float(service["local_sram_fraction"])
        reduction_strategy = str(service["reduction_strategy"])
        noc_bw = _equivalent_raw_noc_bandwidth(service)
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
                                                            skipped_area_budget += 1
                                                            continue
                                                        generated_row_count += 1
                                                        row = _annotate_topology(row, service)
                                                        resource = str(row["dominant_tile_resource"])
                                                        dominance[resource] = dominance.get(resource, 0) + 1
                                                        if best is None or float(row["latency_us"]) < float(best["latency_us"]):
                                                            best = row
                                                        entry = (-float(row["latency_us"]), heap_counter, row)
                                                        heap_counter += 1
                                                        if len(top_heap) < args.top_k:
                                                            heapq.heappush(top_heap, entry)
                                                        elif entry[0] > top_heap[0][0]:
                                                            heapq.heapreplace(top_heap, entry)
                                                        _update_best(best_by_topology, ("topology", "link_width_bits", "topology_worst_hops"), row)
                                                        _update_best(best_by_scheduler, ("topology", "scheduler_policy", "reduction_strategy"), row)
                                                        _update_best(best_by_die, ("sequence_length", "die_area_mm2"), row)
                                                        _update_best(best_by_die_topology, ("sequence_length", "die_area_mm2", "topology"), row)
    if best is None:
        raise RuntimeError("no topology-derived schedule rows generated")
    top_rows = [entry[2] for entry in sorted(top_heap, key=lambda entry: (entry[2]["latency_us"], entry[1]))]
    return {
        "version": 1,
        "model": "llm_decoder_attention_kv_topology_derived_schedule_llama7b_v1",
        "topology_pairs_json": str(args.topology_pairs_json),
        "topology_pairs_summary": topology_payload.get("summary", {}),
        "inputs": {
            "sequence_length_list": args.sequence_length_list,
            "die_area_mm2_list": args.die_area_mm2_list,
            "sram_area_fraction": args.sram_area_fraction,
            "logic_area_fraction": args.logic_area_fraction,
            "reserved_area_fraction": args.reserved_area_fraction,
            "usable_sram_fraction": args.usable_sram_fraction,
            "tile_tokens_list": args.tile_tokens_list,
            "topology_row_limit": args.topology_row_limit,
            "compute_source": args.compute_source,
            "compute_arch_list": args.compute_arch_list,
            "tag_substring": args.tag_substring,
            "measured_l1_costs": str(args.measured_l1_costs),
            "measured_l1_profile": args.measured_l1_profile,
        },
        "sweep_summary": {
            "topology_service_rows_used": len(topology_rows),
            "generated_row_count": generated_row_count,
            "skipped_area_budget_count": skipped_area_budget,
            "dominant_tile_resource_counts": dict(sorted(dominance.items())),
            "retained_row_count": (
                1
                + len(top_rows)
                + len(best_by_topology)
                + len(best_by_scheduler)
                + len(best_by_die)
                + len(best_by_die_topology)
            ),
        },
        "best": best,
        "top_rows": top_rows,
        "best_by_topology": sorted(best_by_topology.values(), key=lambda row: row["latency_us"])[:200],
        "best_by_scheduler": sorted(best_by_scheduler.values(), key=lambda row: row["latency_us"])[:200],
        "best_by_die": sorted(best_by_die.values(), key=lambda row: (row["sequence_length"], row["die_area_mm2"])),
        "best_by_die_topology": sorted(
            best_by_die_topology.values(),
            key=lambda row: (row["sequence_length"], row["die_area_mm2"], row["latency_us"]),
        )[:200],
        "assumptions": [
            "NoC service rows come from the logically valid topology/scheduler pair matrix.",
            "The clustered scheduler preserves topology worst-hop latency while using the topology-derived aggregate payload service for bandwidth.",
            "This remains analytic schedule evidence; it is not cycle-accurate NoC RTL or SRAM arbitration.",
        ],
    }


def write_markdown(path: Path, payload: JsonDict) -> None:
    best = payload["best"]
    lines = [
        "# Llama7B Topology-Derived Clustered Schedule",
        "",
        f"- topology rows used: `{payload['sweep_summary']['topology_service_rows_used']}`",
        f"- generated rows: `{payload['sweep_summary']['generated_row_count']}`",
        f"- skipped area-budget rows: `{payload['sweep_summary']['skipped_area_budget_count']}`",
        "",
        "## Best",
        "",
        "| topology | scheduler | reduction | clusters | link bits | hops | agg B/cyc | gap | replicas | die | SRAM | logic | latency us | resource |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
        "| {topology} | {scheduler_policy} | {reduction_strategy} | {cluster_count} | {link_width_bits} | "
        "{topology_worst_hops} | {topology_aggregate_payload_bytes_per_cycle} | {topology_previous_bandwidth_gap} | "
        "{compute_replica_count} | {die_area_mm2} | {sram_area_fraction} | {compute_logic_area_fraction} | "
        "{latency_us} | {dominant_tile_resource} |".format(**best),
        "",
        "## Best By Scheduler",
        "",
        "| topology | scheduler | reduction | clusters | link bits | hops | agg B/cyc | latency us | resource |",
        "|---|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in payload["best_by_scheduler"][:30]:
        lines.append(
            "| {topology} | {scheduler_policy} | {reduction_strategy} | {cluster_count} | {link_width_bits} | "
            "{topology_worst_hops} | {topology_aggregate_payload_bytes_per_cycle} | {latency_us} | "
            "{dominant_tile_resource} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Best By Die And Topology",
            "",
            "| die | topology | scheduler | clusters | link bits | replicas | latency us | resource |",
            "|---:|---|---|---:|---:|---:|---:|---|",
        ]
    )
    for row in payload["best_by_die_topology"][:40]:
        lines.append(
            "| {die_area_mm2} | {topology} | {scheduler_policy} | {cluster_count} | {link_width_bits} | "
            "{compute_replica_count} | {latency_us} | {dominant_tile_resource} |".format(**row)
        )
    lines.extend(["", "## Assumptions", ""])
    lines.extend(f"- {item}" for item in payload["assumptions"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-root", type=Path, default=Path("."))
    ap.add_argument("--topology-pairs-json", required=True, type=Path)
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
