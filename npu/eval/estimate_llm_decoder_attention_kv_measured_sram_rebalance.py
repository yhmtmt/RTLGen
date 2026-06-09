#!/usr/bin/env python3
"""Rebalance Llama7B attention schedules with measured SRAM capacity.

This pass takes the current endpoint/on-chip service frontier and replaces the
abstract SRAM capacity fields with CACTI-derived tile-local SRAM area plus a
packed shared-SRAM capacity under the selected die SRAM budget.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from npu.eval import estimate_llm_decoder_attention_kv_onchip_service_schedule as onchip  # noqa: E402

JsonDict = dict[str, Any]


def _load_json(path: Path) -> JsonDict:
    return json.loads(path.read_text(encoding="utf-8"))


def _ceil_div(numerator: int | float, denominator: int | float) -> int:
    if numerator <= 0:
        return 0
    return int(math.ceil(float(numerator) / max(1.0, float(denominator))))


def _macro_library(capacity_payload: JsonDict) -> list[JsonDict]:
    metrics_json = capacity_payload.get("sram_metrics_json")
    if not metrics_json:
        raise ValueError("capacity payload is missing sram_metrics_json")
    metrics_path = Path(str(metrics_json))
    if not metrics_path.is_absolute():
        metrics_path = _REPO_ROOT / metrics_path
    metrics = _load_json(metrics_path)
    instances = metrics.get("instances")
    if not isinstance(instances, list) or not instances:
        raise ValueError(f"no SRAM macro instances in {metrics_path}")
    macros: list[JsonDict] = []
    for entry in instances:
        instance = entry.get("instance") if isinstance(entry, dict) else None
        metric = entry.get("metrics") if isinstance(entry, dict) else None
        if not isinstance(instance, dict) or not isinstance(metric, dict):
            continue
        size_bytes = int(instance.get("size_bytes", 0))
        area_um2 = float(metric.get("area_um2", 0.0))
        if size_bytes <= 0 or area_um2 <= 0.0:
            continue
        macros.append(
            {
                "name": str(instance.get("name", f"sram_{size_bytes}")),
                "size_bytes": size_bytes,
                "area_um2": area_um2,
                "access_time_ns": float(metric.get("access_time_ns", 0.0)),
                "read_energy_pj": float(metric.get("read_energy_pj", 0.0)),
                "write_energy_pj": float(metric.get("write_energy_pj", 0.0)),
                "bytes_per_um2": size_bytes / area_um2,
            }
        )
    if not macros:
        raise ValueError(f"no usable SRAM macros in {metrics_path}")
    return sorted(macros, key=lambda item: (item["bytes_per_um2"], item["size_bytes"]), reverse=True)


def _pack_capacity(*, area_budget_um2: float, macros: list[JsonDict]) -> JsonDict:
    remaining = max(0.0, float(area_budget_um2))
    selected: list[JsonDict] = []
    total_bytes = 0
    total_area = 0.0
    total_read = 0.0
    total_write = 0.0
    max_access = 0.0
    for macro in macros:
        count = int(math.floor((remaining + 1e-6) / float(macro["area_um2"])))
        if count <= 0:
            continue
        area = count * float(macro["area_um2"])
        size = count * int(macro["size_bytes"])
        selected.append(
            {
                "name": macro["name"],
                "count": count,
                "size_bytes_each": int(macro["size_bytes"]),
                "area_um2_each": float(macro["area_um2"]),
                "size_bytes_total": size,
                "area_um2_total": area,
            }
        )
        total_bytes += size
        total_area += area
        total_read += count * float(macro["read_energy_pj"])
        total_write += count * float(macro["write_energy_pj"])
        max_access = max(max_access, float(macro["access_time_ns"]))
        remaining -= area
    return {
        "area_budget_um2": round(area_budget_um2, 6),
        "used_area_um2": round(total_area, 6),
        "unused_area_um2": round(max(0.0, remaining), 6),
        "capacity_bytes": total_bytes,
        "capacity_mib": round(total_bytes / (1024 * 1024), 6),
        "read_energy_pj": round(total_read, 6),
        "write_energy_pj": round(total_write, 6),
        "max_access_time_ns": round(max_access, 6),
        "selected_macros": selected,
    }


def _row_shared_budget_um2(row: JsonDict, composition: JsonDict) -> tuple[float, float, int]:
    active_clusters = max(1, int(row.get("active_clusters", row.get("cluster_count", 1))))
    sram_budget = float(row["die_area_mm2"]) * 1_000_000.0 * float(row["sram_area_fraction"])
    quantities = composition.get("composition_quantities")
    if not isinstance(quantities, dict):
        raise ValueError("composition payload missing composition_quantities")
    tile_area_per_cluster = float(quantities["tile_sram_total_area_um2_for_active_clusters"]) / max(
        1, int(composition["selected_frontier"]["active_clusters"])
    )
    tile_area = tile_area_per_cluster * active_clusters
    return max(0.0, sram_budget - tile_area), tile_area, active_clusters


def _rebalance_row(
    row: JsonDict,
    *,
    composition: JsonDict,
    capacity_payload: JsonDict,
    macros: list[JsonDict],
) -> JsonDict:
    shared_budget_um2, tile_area_um2, active_clusters = _row_shared_budget_um2(row, composition)
    shared_pack = _pack_capacity(area_budget_um2=shared_budget_um2, macros=macros)
    quantities = composition["composition_quantities"]
    tile_local_bytes_per_cluster = int(quantities["tile_sram_allocated_bytes_per_cluster"])
    kv_cache_bytes = int(round(float(row["kv_cache_mib"]) * 1024.0 * 1024.0))
    shared_resident_bytes = min(kv_cache_bytes, int(shared_pack["capacity_bytes"]))
    shared_byte_share = shared_resident_bytes / kv_cache_bytes if kv_cache_bytes else 0.0
    local_byte_share = float(row.get("local_byte_share", 0.0))
    hbm_byte_share = max(0.0, 1.0 - shared_byte_share)

    full_tile_bytes = onchip._full_tile_bytes(row)
    per_cluster_hbm_bpc = float(row.get("per_cluster_hbm_bytes_per_cycle", row.get("effective_hbm_bytes_per_cycle", 1.0)))
    tile_hbm_cycles = _ceil_div(full_tile_bytes * hbm_byte_share, per_cluster_hbm_bpc)

    out = dict(row)
    out.update(
        {
            "measured_sram_rebalance_model": "cacti_tile_local_shared_capacity_v1",
            "abstract_local_capacity_bytes_per_cluster_replaced": int(row.get("local_capacity_bytes_per_cluster", 0)),
            "local_capacity_bytes_per_cluster": tile_local_bytes_per_cluster,
            "local_capacity_mib": round(tile_local_bytes_per_cluster * active_clusters / (1024 * 1024), 6),
            "measured_tile_local_sram_area_um2": round(tile_area_um2, 6),
            "measured_shared_sram_budget_um2": round(shared_budget_um2, 6),
            "measured_shared_sram_used_area_um2": shared_pack["used_area_um2"],
            "measured_shared_sram_capacity_bytes": shared_pack["capacity_bytes"],
            "measured_shared_sram_capacity_mib": shared_pack["capacity_mib"],
            "measured_shared_sram_pack": shared_pack,
            "shared_capacity_mib": shared_pack["capacity_mib"],
            "shared_byte_share": round(shared_byte_share, 9),
            "hbm_byte_share": round(hbm_byte_share, 9),
            "local_byte_share": round(local_byte_share, 9),
            "tile_hbm_cycles": tile_hbm_cycles,
            "measured_sram_capacity_source": capacity_payload.get("source_item"),
            "measured_sram_budget_fits": True,
        }
    )
    return out


def build_report(args: argparse.Namespace) -> JsonDict:
    repo_root = args.repo_root
    source_payload = _load_json(repo_root / args.endpoint_schedule_json)
    composition = _load_json(repo_root / args.composition_json)
    capacity_payload = _load_json(repo_root / args.local_sram_capacity_json)
    macros = _macro_library(capacity_payload)

    source_rows = list(source_payload.get("top_rows") or [])
    if not source_rows:
        best = source_payload.get("best")
        if isinstance(best, dict):
            source_rows = [best]
    source_rows = source_rows[: args.frontier_row_limit]
    if not source_rows:
        raise RuntimeError("no source schedule rows found")

    rows: list[JsonDict] = []
    for row in source_rows:
        rebased = _rebalance_row(row, composition=composition, capacity_payload=capacity_payload, macros=macros)
        rows.append(
            onchip._annotate_service(
                rebased,
                schedule_policy=str(rebased["schedule_policy"]),
                bank_arbiter_policy=str(rebased["bank_arbiter_policy"]),
                endpoint_queue_depth_bytes=int(rebased["endpoint_queue_depth_bytes"]),
                bank_queue_depth_bytes=int(rebased["bank_queue_depth_bytes"]),
                router_latency_cycles_per_hop=int(rebased["router_latency_cycles_per_hop"]),
                packet_payload_bytes=int(rebased["packet_payload_bytes"]),
                prefetch_overlap_fraction=float(rebased["prefetch_overlap_fraction"]),
            )
        )

    rows_sorted = sorted(rows, key=lambda item: float(item["latency_us"]))
    best = rows_sorted[0]
    return {
        "version": 1,
        "model": "llm_decoder_attention_kv_measured_sram_rebalance_llama7b_v1",
        "endpoint_schedule_json": str(args.endpoint_schedule_json),
        "composition_json": str(args.composition_json),
        "local_sram_capacity_json": str(args.local_sram_capacity_json),
        "sweep_summary": {
            "source_rows_used": len(source_rows),
            "generated_row_count": len(rows),
            "best_latency_us": best["latency_us"],
            "best_hbm_byte_share": best["hbm_byte_share"],
            "best_shared_capacity_mib": best["measured_shared_sram_capacity_mib"],
            "best_replaced_local_capacity_bytes_per_cluster": best["abstract_local_capacity_bytes_per_cluster_replaced"],
            "best_tile_local_capacity_bytes_per_cluster": best["local_capacity_bytes_per_cluster"],
        },
        "best": best,
        "top_rows": rows_sorted[: args.top_k],
        "sram_macro_library": macros,
        "assumptions": [
            "Tile-local SRAM area is taken from the endpoint/router/SRAM composition audit.",
            "The remaining SRAM area budget is packed into shared SRAM using the CACTI macro chunks from the local-capacity profile.",
            "The abstract per-cluster local-capacity pool is replaced by measured tile-local buffer capacity.",
            "HBM/DRAM bandwidth and compute PPA remain inherited from the source schedule.",
            "Shared SRAM packing is a macro-level CACTI estimate, not a placed memory compiler floorplan.",
        ],
    }


def write_markdown(path: Path, payload: JsonDict) -> None:
    best = payload["best"]
    lines = [
        "# Llama7B Measured-SRAM Rebalanced Endpoint Schedule",
        "",
        f"- source rows used: `{payload['sweep_summary']['source_rows_used']}`",
        f"- generated rows: `{payload['sweep_summary']['generated_row_count']}`",
        "",
        "## Best",
        "",
        "| topology | schedule | clusters | link bits | latency us | hbm share | shared MiB | tile local B/cluster | replaced local B/cluster | resource |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---|",
        "| {topology} | {schedule_policy} | {cluster_count} | {link_width_bits} | {latency_us} | "
        "{hbm_byte_share} | {measured_shared_sram_capacity_mib} | {local_capacity_bytes_per_cluster} | "
        "{abstract_local_capacity_bytes_per_cluster_replaced} | {dominant_tile_resource} |".format(**best),
        "",
        "## Top Rows",
        "",
        "| rank | topology | schedule | bank policy | latency us | hbm share | shared MiB | resource |",
        "|---:|---|---|---|---:|---:|---:|---|",
    ]
    for idx, row in enumerate(payload["top_rows"][:30], start=1):
        lines.append(
            "| {rank} | {topology} | {schedule_policy} | {bank_arbiter_policy} | {latency_us} | "
            "{hbm_byte_share} | {measured_shared_sram_capacity_mib} | {dominant_tile_resource} |".format(
                rank=idx,
                **row,
            )
        )
    lines.extend(["", "## Assumptions", ""])
    lines.extend(f"- {item}" for item in payload["assumptions"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--endpoint-schedule-json", type=Path, required=True)
    parser.add_argument("--composition-json", type=Path, required=True)
    parser.add_argument("--local-sram-capacity-json", type=Path, required=True)
    parser.add_argument("--frontier-row-limit", type=int, default=64)
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
