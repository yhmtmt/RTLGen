#!/usr/bin/env python3
"""Audit endpoint/router/SRAM concreteness for the selected Llama7B attention frontier."""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from pathlib import Path
from typing import Any


JsonDict = dict[str, Any]


def _load_json(path: Path) -> JsonDict:
    return json.loads(path.read_text(encoding="utf-8"))


def _ceil_div(numerator: int | float, denominator: int | float) -> int:
    return int(math.ceil(float(numerator) / max(1.0, float(denominator))))


def _parse_width_bits(path_or_design: str) -> int | None:
    match = re.search(r"_w(\d+)(?:_|$)", path_or_design)
    if match:
        return int(match.group(1))
    return None


def _best_metrics(metrics_csv: Path) -> JsonDict | None:
    if not metrics_csv.exists():
        return None
    with metrics_csv.open(newline="", encoding="utf-8") as handle:
        rows = [row for row in csv.DictReader(handle) if row.get("status") == "ok"]
    if not rows:
        return None
    row = min(rows, key=lambda item: (float(item["critical_path_ns"]), float(item["die_area"])))
    return {
        "metrics_csv": str(metrics_csv),
        "design": row.get("design", ""),
        "critical_path_ns": float(row["critical_path_ns"]),
        "area_um2": float(row["die_area"]),
        "power_mw": float(row["total_power_mw"]),
        "param_hash": row.get("param_hash", ""),
        "tag": row.get("tag", ""),
        "width_bits": _parse_width_bits(row.get("design", "") or str(metrics_csv)),
    }


def _sram_capacity_bytes(sram_metrics: JsonDict) -> int:
    total = 0
    for instance in sram_metrics.get("instances", []):
        spec = instance.get("instance", {})
        total += int(spec.get("size_bytes", 0))
    return total


def _build_payload(
    *,
    repo_root: Path,
    endpoint_ready_valid: JsonDict,
    endpoint_onchip: JsonDict,
    sram_summary: JsonDict,
    sram_metrics: JsonDict,
) -> JsonDict:
    best = endpoint_onchip["best"]
    ready_params = endpoint_ready_valid["derived_rtl_parameters"]
    packet_bits = int(ready_params["data_w"])
    packet_payload_bytes = int(ready_params["packet_payload_bytes"])
    link_width_bits = int(best["link_width_bits"])
    router_metrics = _best_metrics(repo_root / best["noc_router_metrics_csv"])
    fifo_metrics = _best_metrics(repo_root / best["noc_fifo_metrics_csv"])
    endpoint_metrics = _best_metrics(repo_root / best["onchip_endpoint_metrics_csv"])

    router_width = int(router_metrics["width_bits"]) if router_metrics and router_metrics.get("width_bits") else 0
    fifo_width = int(fifo_metrics["width_bits"]) if fifo_metrics and fifo_metrics.get("width_bits") else 0
    endpoint_ppa_width = (
        int(endpoint_metrics["width_bits"]) if endpoint_metrics and endpoint_metrics.get("width_bits") else 0
    )
    router_lanes_for_link = _ceil_div(link_width_bits, router_width) if router_width else None
    fifo_lanes_for_link = _ceil_div(link_width_bits, fifo_width) if fifo_width else None
    router_lanes_for_packet = _ceil_div(packet_bits, router_width) if router_width else None
    endpoint_width_ratio = _ceil_div(packet_bits, endpoint_ppa_width) if endpoint_ppa_width else None

    active_clusters = int(best["active_clusters"])
    sram_allocated_bytes = _sram_capacity_bytes(sram_metrics)
    local_capacity_bytes_per_cluster = int(best["local_capacity_bytes_per_cluster"])
    sram_budget_area_um2 = float(best["die_area_mm2"]) * 1_000_000.0 * float(best["sram_area_fraction"])
    tile_sram_area_per_cluster_um2 = float(sram_summary.get("total_area_um2", 0.0))
    tile_sram_total_area_um2 = tile_sram_area_per_cluster_um2 * active_clusters

    scaled_router_area_per_cluster = (
        float(router_metrics["area_um2"]) * router_lanes_for_link if router_metrics and router_lanes_for_link else None
    )
    scaled_fifo_area_per_cluster = (
        float(fifo_metrics["area_um2"]) * fifo_lanes_for_link if fifo_metrics and fifo_lanes_for_link else None
    )
    scaled_endpoint_area_per_cluster = (
        float(endpoint_metrics["area_um2"]) * endpoint_width_ratio if endpoint_metrics and endpoint_width_ratio else None
    )
    scaled_local_service_area_per_cluster = sum(
        value
        for value in [scaled_router_area_per_cluster, scaled_fifo_area_per_cluster, scaled_endpoint_area_per_cluster]
        if value is not None
    )

    closure_flags = {
        "ready_valid_endpoint_passed": endpoint_ready_valid["decision"] == "ready_valid_endpoint_policy_passed",
        "endpoint_ppa_width_matches_ready_valid_width": endpoint_ppa_width == packet_bits,
        "router_ppa_width_matches_link_width": router_width == link_width_bits,
        "fifo_ppa_width_matches_link_width": fifo_width == link_width_bits,
        "tile_sram_profile_fits_sram_area_budget": tile_sram_total_area_um2 <= sram_budget_area_um2,
        "tile_sram_capacity_covers_selected_local_capacity": sram_allocated_bytes >= local_capacity_bytes_per_cluster,
    }
    requires_follow_on = [
        name for name, closed in closure_flags.items() if not closed and name != "tile_sram_capacity_covers_selected_local_capacity"
    ]
    if not closure_flags["tile_sram_capacity_covers_selected_local_capacity"]:
        requires_follow_on.append("full_local_capacity_sram_macro_profile_missing")

    return {
        "model": "llm_decoder_attention_endpoint_router_sram_composition_audit_v1",
        "version": 1,
        "source_items": {
            "endpoint_onchip": "l2_decoder_attention_kv_endpoint_full_onchip_service_schedule_llama7b_v1",
            "endpoint_ready_valid": "l2_decoder_attention_kv_endpoint_ready_valid_service_llama7b_v1",
            "sram_profile": "llama7b_attention_tile_buffers_v1",
        },
        "selected_frontier": {
            "latency_us": best["latency_us"],
            "topology": best["topology"],
            "scheduler_policy": best["scheduler_policy"],
            "reduction_strategy": best["reduction_strategy"],
            "schedule_policy": best["schedule_policy"],
            "bank_arbiter_policy": best["bank_arbiter_policy"],
            "cluster_count": best["cluster_count"],
            "active_clusters": best["active_clusters"],
            "bank_count": best["bank_count"],
            "link_width_bits": link_width_bits,
            "packet_payload_bytes": packet_payload_bytes,
            "local_sram_fraction": best["local_sram_fraction"],
            "sram_area_fraction": best["sram_area_fraction"],
            "compute_logic_area_fraction": best["compute_logic_area_fraction"],
            "dominant_tile_resource": best["dominant_tile_resource"],
        },
        "measured_primitives": {
            "router": router_metrics,
            "fifo": fifo_metrics,
            "endpoint": endpoint_metrics,
            "sram_summary": {
                "total_area_um2": sram_summary.get("total_area_um2"),
                "max_access_time_ns": sram_summary.get("max_access_time_ns"),
                "total_read_energy_pj": sram_summary.get("total_read_energy_pj"),
                "total_write_energy_pj": sram_summary.get("total_write_energy_pj"),
                "allocated_bytes": sram_allocated_bytes,
            },
        },
        "composition_quantities": {
            "packet_bits": packet_bits,
            "packet_payload_bytes": packet_payload_bytes,
            "link_width_bits": link_width_bits,
            "router_lanes_for_packet": router_lanes_for_packet,
            "router_lanes_for_link": router_lanes_for_link,
            "fifo_lanes_for_link": fifo_lanes_for_link,
            "endpoint_width_ratio_vs_measured_ppa": endpoint_width_ratio,
            "local_capacity_bytes_per_cluster": local_capacity_bytes_per_cluster,
            "tile_sram_allocated_bytes_per_cluster": sram_allocated_bytes,
            "tile_sram_capacity_fraction_of_selected_local_capacity": round(
                sram_allocated_bytes / max(1, local_capacity_bytes_per_cluster),
                6,
            ),
            "sram_budget_area_um2": sram_budget_area_um2,
            "tile_sram_total_area_um2_for_active_clusters": tile_sram_total_area_um2,
            "tile_sram_budget_area_fraction": round(tile_sram_total_area_um2 / max(1.0, sram_budget_area_um2), 6),
            "scaled_router_area_per_cluster_um2": scaled_router_area_per_cluster,
            "scaled_fifo_area_per_cluster_um2": scaled_fifo_area_per_cluster,
            "scaled_endpoint_area_per_cluster_um2": scaled_endpoint_area_per_cluster,
            "scaled_local_service_area_per_cluster_um2": scaled_local_service_area_per_cluster,
            "scaled_local_service_area_all_clusters_um2": scaled_local_service_area_per_cluster * active_clusters,
        },
        "closure_flags": closure_flags,
        "decision": (
            "composition_requires_follow_on_ppa"
            if requires_follow_on
            else "endpoint_router_sram_composition_closed_for_selected_policy"
        ),
        "required_follow_on_ppa": requires_follow_on,
        "recommended_next_l1_points": [
            {
                "primitive": "onchip_service_endpoint",
                "reason": "ready/valid probe used DATA_W=1024 but selected PPA currently references w128 endpoint metrics",
                "parameters": {
                    "flit_bits": packet_bits,
                    "banks": int(ready_params["banks"]),
                    "endpoint_depth": int(ready_params["endpoint_queue_depth"]),
                    "bank_queue_depth": int(ready_params["bank_queue_depth"]),
                },
            },
            {
                "primitive": "noc_router",
                "reason": "selected link is 2048 bits but current PPA references w128 router metrics",
                "parameters": {"ports": 4, "flit_bits": link_width_bits},
            },
            {
                "primitive": "noc_fifo",
                "reason": "selected link is 2048 bits but current PPA references w128 FIFO metrics",
                "parameters": {"depth": 16, "flit_bits": link_width_bits},
            },
            {
                "primitive": "local_sram_capacity",
                "reason": "tile-local SRAM buffers are measured, but the selected local-capacity pool is still capacity-estimated",
                "parameters": {
                    "local_capacity_bytes_per_cluster": local_capacity_bytes_per_cluster,
                    "active_clusters": active_clusters,
                },
            },
        ],
        "remaining_abstractions": [
            "Router/FIFO PPA is lane-scaled from narrower measured primitives until wide-link L1 points are measured.",
            "Endpoint ready/valid behavior is verified at 1024 bits, but endpoint PPA is still from the existing w128 wrapper.",
            "Tile-local SRAM buffers have CACTI metrics, but the selected per-cluster local capacity pool is not yet a concrete SRAM macro set.",
            "HBM/DRAM service remains inherited and intentionally outside this audit.",
        ],
    }


def _write_report(payload: JsonDict, report: Path) -> None:
    selected = payload["selected_frontier"]
    quantities = payload["composition_quantities"]
    flags = payload["closure_flags"]
    lines = [
        "# Endpoint Router/SRAM Composition Audit",
        "",
        "## Selected Frontier",
        f"- latency_us: `{selected['latency_us']}`",
        f"- topology: `{selected['topology']}`",
        f"- clusters: `{selected['cluster_count']}`",
        f"- banks: `{selected['bank_count']}`",
        f"- link_width_bits: `{selected['link_width_bits']}`",
        f"- packet_payload_bytes: `{selected['packet_payload_bytes']}`",
        f"- dominant_tile_resource: `{selected['dominant_tile_resource']}`",
        "",
        "## Composition Quantities",
        f"- packet_bits: `{quantities['packet_bits']}`",
        f"- router_lanes_for_packet: `{quantities['router_lanes_for_packet']}`",
        f"- router_lanes_for_link: `{quantities['router_lanes_for_link']}`",
        f"- fifo_lanes_for_link: `{quantities['fifo_lanes_for_link']}`",
        f"- endpoint_width_ratio_vs_measured_ppa: `{quantities['endpoint_width_ratio_vs_measured_ppa']}`",
        f"- tile_sram_capacity_fraction_of_selected_local_capacity: `{quantities['tile_sram_capacity_fraction_of_selected_local_capacity']}`",
        f"- tile_sram_budget_area_fraction: `{quantities['tile_sram_budget_area_fraction']}`",
        "",
        "## Closure Flags",
    ]
    for name, value in flags.items():
        lines.append(f"- {name}: `{value}`")
    lines.extend(
        [
            "",
            "## Decision",
            f"- decision: `{payload['decision']}`",
            f"- required_follow_on_ppa: `{', '.join(payload['required_follow_on_ppa']) or 'none'}`",
            "",
            "## Recommended L1 Points",
        ]
    )
    for item in payload["recommended_next_l1_points"]:
        lines.append(f"- `{item['primitive']}`: {item['reason']}")
    lines.extend(["", "## Remaining Abstractions"])
    for item in payload["remaining_abstractions"]:
        lines.append(f"- {item}")
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--endpoint-ready-valid-json", type=Path, required=True)
    parser.add_argument("--endpoint-onchip-json", type=Path, required=True)
    parser.add_argument("--sram-summary-json", type=Path, required=True)
    parser.add_argument("--sram-metrics-json", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()

    def rooted(path: Path) -> Path:
        return path if path.is_absolute() else repo_root / path

    payload = _build_payload(
        repo_root=repo_root,
        endpoint_ready_valid=_load_json(rooted(args.endpoint_ready_valid_json)),
        endpoint_onchip=_load_json(rooted(args.endpoint_onchip_json)),
        sram_summary=_load_json(rooted(args.sram_summary_json)),
        sram_metrics=_load_json(rooted(args.sram_metrics_json)),
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_report(payload, args.out_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
