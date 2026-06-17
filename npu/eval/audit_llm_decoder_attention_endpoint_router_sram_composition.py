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


def _metrics_from_promotion_proposal(proposal: JsonDict) -> JsonDict | None:
    metrics_ref = proposal.get("metrics_ref")
    metric_summary = proposal.get("metric_summary")
    if not isinstance(metrics_ref, dict) or not isinstance(metric_summary, dict):
        return None
    metrics_csv = str(metrics_ref.get("metrics_csv", ""))
    design = str(metrics_ref.get("design") or Path(metrics_csv).parent.name or "")
    return {
        "metrics_csv": metrics_csv,
        "design": design,
        "critical_path_ns": float(metric_summary["critical_path_ns"]),
        "area_um2": float(metric_summary["die_area"]),
        "power_mw": float(metric_summary["total_power_mw"]),
        "param_hash": metrics_ref.get("param_hash", ""),
        "tag": metrics_ref.get("tag", ""),
        "width_bits": _parse_width_bits(design or metrics_csv),
        "source": "l1_promotion",
    }


def _best_promotion_metric(promotion: JsonDict | None, *, design_contains: str) -> JsonDict | None:
    if not promotion:
        return None
    proposals = promotion.get("proposals")
    if not isinstance(proposals, list):
        return None
    matches: list[JsonDict] = []
    for proposal in proposals:
        if not isinstance(proposal, dict):
            continue
        metric = _metrics_from_promotion_proposal(proposal)
        if metric and design_contains in str(metric.get("design", "")):
            matches.append(metric)
    if not matches:
        return None
    return min(matches, key=lambda item: (float(item["critical_path_ns"]), float(item["area_um2"])))


def _best_segmented_router_fifo_metric(
    promotion: JsonDict | None,
    *,
    design_contains: str,
    target_width_bits: int,
    allowed_lane_width_bits: tuple[int, ...] = (128, 256),
) -> JsonDict | None:
    if not promotion:
        return None
    proposals = promotion.get("proposals")
    if not isinstance(proposals, list):
        return None
    candidates: list[JsonDict] = []
    for proposal in proposals:
        if not isinstance(proposal, dict):
            continue
        metric = _metrics_from_promotion_proposal(proposal)
        if not metric:
            continue
        width_bits = metric.get("width_bits")
        if not isinstance(width_bits, int) or width_bits <= 0:
            continue
        if width_bits not in allowed_lane_width_bits:
            continue
        if target_width_bits % width_bits != 0:
            continue
        if design_contains not in str(metric.get("design", "")):
            continue
        lane_count = target_width_bits // width_bits
        metric["lane_count_for_link"] = lane_count
        metric["aggregate_area_um2"] = float(metric["area_um2"]) * lane_count
        metric["aggregate_power_mw"] = float(metric["power_mw"]) * lane_count
        candidates.append(metric)
    if not candidates:
        return None
    return min(
        candidates,
        key=lambda item: (
            float(item["aggregate_area_um2"]),
            float(item["aggregate_power_mw"]),
            float(item["critical_path_ns"]),
        ),
    )


def _promotion_boundary_rows(promotion: JsonDict | None, *, design_contains: str) -> list[JsonDict]:
    if not promotion:
        return []
    boundary = promotion.get("boundary_evidence")
    if not isinstance(boundary, dict):
        return []
    rows = boundary.get("rows")
    if not isinstance(rows, list):
        return []
    return [
        row
        for row in rows
        if isinstance(row, dict) and design_contains in str(row.get("design") or row.get("metrics_csv") or "")
    ]


def _boundary_summary(rows: list[JsonDict], *, target_width_bits: int) -> JsonDict | None:
    if not rows:
        return None
    statuses = sorted({str(row.get("status", "")) for row in rows if row.get("status")})
    param_hashes = [str(row.get("param_hash", "")) for row in rows if row.get("param_hash")]
    metrics_csvs = sorted({str(row.get("metrics_csv", "")) for row in rows if row.get("metrics_csv")})
    core_utilizations: list[int] = []
    for row in rows:
        params_json = row.get("params_json")
        if not isinstance(params_json, str) or not params_json:
            continue
        try:
            params = json.loads(params_json)
        except json.JSONDecodeError:
            continue
        if "CORE_UTILIZATION" in params:
            core_utilizations.append(int(params["CORE_UTILIZATION"]))
    return {
        "status": "failed" if statuses == ["failed"] else "mixed",
        "row_count": len(rows),
        "target_width_bits": target_width_bits,
        "observed_width_bits": _parse_width_bits(str(rows[0].get("design") or rows[0].get("metrics_csv") or "")),
        "statuses": statuses,
        "core_utilizations": sorted(set(core_utilizations)),
        "param_hashes": param_hashes,
        "metrics_csvs": metrics_csvs,
    }


def _sram_capacity_bytes(sram_metrics: JsonDict) -> int:
    total = 0
    for instance in sram_metrics.get("instances", []):
        spec = instance.get("instance", {})
        total += int(spec.get("size_bytes", 0))
    return total


def _local_sram_capacity_evidence_summary(
    local_sram_capacity: JsonDict | None,
) -> tuple[JsonDict | None, JsonDict | None]:
    if not isinstance(local_sram_capacity, dict):
        return None, None
    budget_check = local_sram_capacity.get("budget_check")
    chunking = local_sram_capacity.get("chunking")
    if not isinstance(budget_check, dict):
        budget_check = None
    if not isinstance(chunking, dict):
        chunking = None
    return budget_check, chunking


def _local_sram_capacity_diagnosis(local_sram_budget: JsonDict | None) -> str:
    if local_sram_budget is None:
        return "full_local_capacity_sram_macro_profile_missing"
    fits_budget = local_sram_budget.get("fits_sram_budget")
    if isinstance(fits_budget, bool):
        return "local_capacity_budget_passed" if fits_budget else "local_capacity_budget_failed"
    return "local_capacity_budget_check_missing"


def _build_payload(
    *,
    repo_root: Path,
    endpoint_ready_valid: JsonDict,
    endpoint_onchip: JsonDict,
    sram_summary: JsonDict,
    sram_metrics: JsonDict,
    wide_l1_promotion: JsonDict | None = None,
    segmented_l1_promotion: JsonDict | None = None,
    local_sram_capacity: JsonDict | None = None,
) -> JsonDict:
    best = endpoint_onchip["best"]
    ready_params = endpoint_ready_valid["derived_rtl_parameters"]
    packet_bits = int(ready_params["data_w"])
    packet_payload_bytes = int(ready_params["packet_payload_bytes"])
    link_width_bits = int(best["link_width_bits"])
    router_metrics = _best_metrics(repo_root / best["noc_router_metrics_csv"])
    fifo_metrics = _best_metrics(repo_root / best["noc_fifo_metrics_csv"])
    router_segmented_metrics = _best_segmented_router_fifo_metric(
        segmented_l1_promotion,
        design_contains="noc_router",
        target_width_bits=link_width_bits,
    )
    fifo_segmented_metrics = _best_segmented_router_fifo_metric(
        segmented_l1_promotion,
        design_contains="noc_fifo",
        target_width_bits=link_width_bits,
    )
    if router_segmented_metrics and (
        not router_metrics
        or not router_metrics.get("width_bits")
        or int(router_metrics["width_bits"]) != link_width_bits
    ):
        router_segmented_metrics["source"] = "segmented_l1_promotion"
        router_metrics = router_segmented_metrics
    if fifo_segmented_metrics and (
        not fifo_metrics
        or not fifo_metrics.get("width_bits")
        or int(fifo_metrics["width_bits"]) != link_width_bits
    ):
        fifo_segmented_metrics["source"] = "segmented_l1_promotion"
        fifo_metrics = fifo_segmented_metrics
    endpoint_metrics = (
        _best_promotion_metric(wide_l1_promotion, design_contains="onchip_endpoint")
        or _best_metrics(repo_root / best["onchip_endpoint_metrics_csv"])
    )
    router_boundary = _boundary_summary(
        _promotion_boundary_rows(wide_l1_promotion, design_contains="noc_router"),
        target_width_bits=link_width_bits,
    )
    fifo_boundary = _boundary_summary(
        _promotion_boundary_rows(wide_l1_promotion, design_contains="noc_fifo"),
        target_width_bits=link_width_bits,
    )

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
    local_sram_budget, local_sram_chunking = _local_sram_capacity_evidence_summary(local_sram_capacity)
    local_sram_capacity_present = isinstance(local_sram_capacity, dict)
    local_capacity_diagnosis = _local_sram_capacity_diagnosis(local_sram_budget)
    local_capacity_fits_budget = (
        local_sram_budget.get("fits_sram_budget") if isinstance(local_sram_budget, dict) else None
    )

    router_uses_segmented = router_metrics.get("source") == "segmented_l1_promotion" if router_metrics else False
    fifo_uses_segmented = fifo_metrics.get("source") == "segmented_l1_promotion" if fifo_metrics else False
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
        requires_follow_on.append(
            "capacity_rebalance_or_smaller_local_sram_required"
            if local_sram_capacity_present
            else "full_local_capacity_sram_macro_profile_missing"
        )
    if (
        "router_ppa_width_matches_link_width" in requires_follow_on
        and not closure_flags["router_ppa_width_matches_link_width"]
    ):
        requires_follow_on.remove("router_ppa_width_matches_link_width")
        if not router_uses_segmented:
            if router_boundary:
                requires_follow_on.append("segmented_or_narrower_router_ppa_required")
            else:
                requires_follow_on.append("router_ppa_width_matches_link_width")
    if (
        "fifo_ppa_width_matches_link_width" in requires_follow_on
        and not closure_flags["fifo_ppa_width_matches_link_width"]
    ):
        requires_follow_on.remove("fifo_ppa_width_matches_link_width")
        if not fifo_uses_segmented:
            if fifo_boundary:
                requires_follow_on.append("segmented_or_narrower_fifo_ppa_required")
            else:
                requires_follow_on.append("fifo_ppa_width_matches_link_width")

    router_measured_at_link_width = closure_flags["router_ppa_width_matches_link_width"] and link_width_bits == 2048
    fifo_measured_at_link_width = closure_flags["fifo_ppa_width_matches_link_width"] and link_width_bits == 2048

    closure_diagnosis = {
        "endpoint": (
            "measured_at_ready_valid_width"
            if closure_flags["endpoint_ppa_width_matches_ready_valid_width"]
            else "ppa_width_mismatch_or_missing"
        ),
        "router": (
            "measured_at_link_width"
            if router_measured_at_link_width
            else (
                "lane_composed_segmented_evidence_available_while_flat_2048_failed"
                if router_boundary and router_uses_segmented
                else (
                    "ppa_width_matches_non_2048_link_width"
                    if closure_flags["router_ppa_width_matches_link_width"]
                    else (
                        "flat_link_width_boundary_failed"
                        if router_boundary and router_boundary.get("status") == "failed"
                        else "ppa_width_mismatch_or_missing"
                    )
                )
            )
        ),
        "fifo": (
            "measured_at_link_width"
            if fifo_measured_at_link_width
            else (
                "lane_composed_segmented_evidence_available_while_flat_2048_failed"
                if fifo_boundary and fifo_uses_segmented
                else (
                    "ppa_width_matches_non_2048_link_width"
                    if closure_flags["fifo_ppa_width_matches_link_width"]
                    else (
                        "flat_link_width_boundary_failed"
                        if fifo_boundary and fifo_boundary.get("status") == "failed"
                        else "ppa_width_mismatch_or_missing"
                    )
                )
            )
        ),
        "local_sram_capacity": (
            "covered_by_measured_tile_profile"
            if closure_flags["tile_sram_capacity_covers_selected_local_capacity"]
            else local_capacity_diagnosis
        ),
    }

    recommended_next_l1_points = []
    if not closure_flags["endpoint_ppa_width_matches_ready_valid_width"]:
        recommended_next_l1_points.append(
            {
                "primitive": "onchip_service_endpoint",
                "reason": "ready/valid probe width still lacks matching endpoint PPA",
                "parameters": {
                    "flit_bits": packet_bits,
                    "banks": int(ready_params["banks"]),
                    "endpoint_depth": int(ready_params["endpoint_queue_depth"]),
                    "bank_queue_depth": int(ready_params["bank_queue_depth"]),
                },
            }
        )
    if not closure_flags["router_ppa_width_matches_link_width"]:
        if not router_uses_segmented:
            recommended_next_l1_points.append(
                {
                    "primitive": "segmented_noc_router",
                    "reason": (
                        "flat 2048-bit router failed physical boundary runs; measure lane-composed or narrower-link "
                        "router/scheduler pairs instead of retrying the same flat primitive"
                    )
                    if router_boundary
                    else "selected link width lacks matching router PPA",
                    "parameters": {
                        "ports": 4,
                        "aggregate_flit_bits": link_width_bits,
                        "candidate_lane_bits": [128, 256],
                    },
                }
            )
    if not closure_flags["fifo_ppa_width_matches_link_width"]:
        if not fifo_uses_segmented:
            recommended_next_l1_points.append(
                {
                    "primitive": "segmented_noc_fifo",
                    "reason": (
                        "flat 2048-bit FIFO failed physical boundary runs; measure lane-composed or narrower-link "
                        "FIFO/scheduler pairs instead of retrying the same flat primitive"
                    )
                    if fifo_boundary
                    else "selected link width lacks matching FIFO PPA",
                    "parameters": {
                        "depth": 16,
                        "aggregate_flit_bits": link_width_bits,
                        "candidate_lane_bits": [128, 256],
                    },
                }
            )
    if not closure_flags["tile_sram_capacity_covers_selected_local_capacity"]:
        if local_sram_capacity_present:
            local_capacity_reason = (
                "tile-local SRAM buffers are measured, and local-capacity CACTI evidence is available; "
                "re-balance or reduce the selected local-capacity pool to resolve a local SRAM budget failure."
                if local_capacity_fits_budget is False
                else (
                    "tile-local SRAM buffers are measured, and local-capacity CACTI evidence is available; "
                    "consume measured local-capacity profiles in the next rebalance step."
                )
            )
        else:
            local_capacity_reason = (
                "tile-local SRAM buffers are measured, but the selected local-capacity pool is still capacity-estimated"
            )
        recommended_next_l1_points.append(
            {
                "primitive": "local_sram_capacity",
                "reason": local_capacity_reason,
                "parameters": {
                    "local_capacity_bytes_per_cluster": local_capacity_bytes_per_cluster,
                    "active_clusters": active_clusters,
                },
            }
        )
    remaining_abstractions = []
    if not closure_flags["endpoint_ppa_width_matches_ready_valid_width"]:
        remaining_abstractions.append(
            "Endpoint ready/valid behavior is verified at the selected width, but matching endpoint PPA is not yet available."
        )
    if not closure_flags["router_ppa_width_matches_link_width"] or not closure_flags["fifo_ppa_width_matches_link_width"]:
        router_or_fifo_segmented = router_uses_segmented or fifo_uses_segmented
        if router_or_fifo_segmented:
            if router_boundary or fifo_boundary:
                remaining_abstractions.append(
                    "Lane-composed/segmented NoC PPA metrics are available for router/FIFO while flat 2048-bit boundary evidence failed."
                )
            else:
                remaining_abstractions.append(
                    "Lane-composed/segmented NoC PPA metrics are available for router/FIFO."
                )
        elif router_boundary or fifo_boundary:
            remaining_abstractions.append(
                "Router/FIFO PPA cannot use the failed flat 2048-bit primitive; lane-composed or narrower-link NoC PPA remains open."
            )
        else:
            remaining_abstractions.append(
                "Router/FIFO PPA is lane-scaled from narrower measured primitives until matching link-width or segmented L1 points are measured."
            )
    if not closure_flags["tile_sram_capacity_covers_selected_local_capacity"]:
        if local_sram_capacity_present:
            if local_capacity_fits_budget is False:
                remaining_abstractions.append(
                    "Tile-local SRAM buffers are measured, but measured local-capacity evidence already shows the selected per-cluster "
                    "local SRAM pool exceeds the available shared SRAM budget."
                )
            else:
                remaining_abstractions.append(
                    "Tile-local SRAM buffers are measured, and concrete local-capacity evidence is available for the selected pool."
                )
        else:
            remaining_abstractions.append(
                "Tile-local SRAM buffers have CACTI metrics, but the selected per-cluster local capacity pool is not yet a concrete SRAM macro set."
            )
    remaining_abstractions.append("HBM/DRAM service remains inherited and intentionally outside this audit.")

    return {
        "model": "llm_decoder_attention_endpoint_router_sram_composition_audit_v1",
        "version": 1,
        "source_items": {
            "endpoint_onchip": "l2_decoder_attention_kv_endpoint_full_onchip_service_schedule_llama7b_v1",
            "endpoint_ready_valid": "l2_decoder_attention_kv_endpoint_ready_valid_service_llama7b_v1",
            "sram_profile": "llama7b_attention_tile_buffers_v1",
            "wide_l1_promotion": wide_l1_promotion.get("item_id") if wide_l1_promotion else None,
            "segmented_l1_promotion": segmented_l1_promotion.get("item_id") if segmented_l1_promotion else None,
            "local_sram_capacity": local_sram_capacity.get("source_item") if isinstance(local_sram_capacity, dict) else None,
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
            "local_sram_capacity": {
                "budget_check": local_sram_budget,
                "chunking": local_sram_chunking,
            } if local_sram_capacity_present else None,
        },
        "boundary_evidence": {
            "router": router_boundary,
            "fifo": fifo_boundary,
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
        "closure_diagnosis": closure_diagnosis,
        "decision": (
            "composition_requires_follow_on_ppa"
            if requires_follow_on
            else "endpoint_router_sram_composition_closed_for_selected_policy"
        ),
        "required_follow_on_ppa": requires_follow_on,
        "recommended_next_l1_points": recommended_next_l1_points,
        "remaining_abstractions": remaining_abstractions,
    }


def _write_report(payload: JsonDict, report: Path) -> None:
    selected = payload["selected_frontier"]
    quantities = payload["composition_quantities"]
    flags = payload["closure_flags"]
    diagnosis = payload["closure_diagnosis"]
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
    lines.extend(["", "## Closure Diagnosis"])
    for name, value in diagnosis.items():
        lines.append(f"- {name}: `{value}`")
    local_sram_evidence = payload.get("measured_primitives", {}).get("local_sram_capacity", {})
    local_sram_budget = local_sram_evidence.get("budget_check") if isinstance(local_sram_evidence, dict) else None
    if isinstance(local_sram_budget, dict):
        lines.extend(
            [
                "",
                "## Local SRAM Capacity Budget",
                f"- fits_sram_budget: `{local_sram_budget.get('fits_sram_budget')}`",
                f"- total_area_um2: `{local_sram_budget.get('total_area_um2')}`",
                f"- sram_budget_area_um2: `{local_sram_budget.get('sram_budget_area_um2')}`",
                f"- area_fraction_of_sram_budget: `{local_sram_budget.get('area_fraction_of_sram_budget')}`",
            ]
        )
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
    parser.add_argument("--wide-l1-promotion-json", type=Path)
    parser.add_argument("--segmented-l1-promotion-json", type=Path)
    parser.add_argument("--local-sram-capacity-json", type=Path)
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
        wide_l1_promotion=_load_json(rooted(args.wide_l1_promotion_json)) if args.wide_l1_promotion_json else None,
        segmented_l1_promotion=_load_json(rooted(args.segmented_l1_promotion_json))
        if args.segmented_l1_promotion_json
        else None,
        local_sram_capacity=_load_json(rooted(args.local_sram_capacity_json)) if args.local_sram_capacity_json else None,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_report(payload, args.out_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
