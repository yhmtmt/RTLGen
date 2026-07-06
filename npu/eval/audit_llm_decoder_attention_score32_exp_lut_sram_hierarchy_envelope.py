#!/usr/bin/env python3
"""Audit SRAM hierarchy placement envelope for the score32 exp-LUT Llama7B row."""

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

JsonDict = dict[str, Any]


def _load_json(path: Path) -> JsonDict:
    return json.loads(path.read_text(encoding="utf-8"))


def _as_dict(value: Any) -> JsonDict:
    return dict(value) if isinstance(value, dict) else {}


def _ceil_div(numerator: int | float, denominator: int | float) -> int:
    if numerator <= 0:
        return 0
    return int(math.ceil(float(numerator) / max(1.0, float(denominator))))


def _float_list(text: str) -> list[float]:
    values: list[float] = []
    for piece in text.split(","):
        piece = piece.strip()
        if not piece:
            continue
        value = float(piece)
        if value <= 0.0 or value > 1.0:
            raise argparse.ArgumentTypeError("efficiency values must be in (0, 1]")
        values.append(value)
    if not values:
        raise argparse.ArgumentTypeError("at least one efficiency value is required")
    return values


def _macro_library(capacity_payload: JsonDict) -> list[JsonDict]:
    metrics_json = capacity_payload.get("sram_metrics_json")
    if not metrics_json:
        raise ValueError("local SRAM capacity payload is missing sram_metrics_json")
    metrics_path = Path(str(metrics_json))
    if not metrics_path.is_absolute():
        metrics_path = _REPO_ROOT / metrics_path
    metrics = _load_json(metrics_path)
    macros: list[JsonDict] = []
    for entry in metrics.get("instances", []):
        if not isinstance(entry, dict):
            continue
        instance = _as_dict(entry.get("instance"))
        metric = _as_dict(entry.get("metrics"))
        size_bytes = int(instance.get("size_bytes", 0) or 0)
        area_um2 = float(metric.get("area_um2", 0.0) or 0.0)
        if size_bytes <= 0 or area_um2 <= 0.0:
            continue
        macros.append(
            {
                "name": str(instance.get("name") or f"sram_{size_bytes}"),
                "size_bytes": size_bytes,
                "area_um2": area_um2,
                "read_energy_pj": float(metric.get("read_energy_pj", 0.0) or 0.0),
                "write_energy_pj": float(metric.get("write_energy_pj", 0.0) or 0.0),
                "access_time_ns": float(metric.get("access_time_ns", 0.0) or 0.0),
                "bytes_per_um2": size_bytes / area_um2,
            }
        )
    if not macros:
        raise ValueError(f"no usable SRAM macro metrics found in {metrics_path}")
    return sorted(macros, key=lambda item: (float(item["bytes_per_um2"]), int(item["size_bytes"])), reverse=True)


def _pack_capacity(*, macro_area_budget_um2: float, macros: list[JsonDict]) -> JsonDict:
    remaining = max(0.0, float(macro_area_budget_um2))
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
                "area_um2_each": round(float(macro["area_um2"]), 6),
                "size_bytes_total": size,
                "macro_area_um2_total": round(area, 6),
            }
        )
        total_bytes += size
        total_area += area
        total_read += count * float(macro["read_energy_pj"])
        total_write += count * float(macro["write_energy_pj"])
        max_access = max(max_access, float(macro["access_time_ns"]))
        remaining -= area
    return {
        "capacity_bytes": total_bytes,
        "capacity_mib": round(total_bytes / (1024 * 1024), 6),
        "macro_area_um2": round(total_area, 6),
        "unused_macro_area_budget_um2": round(max(0.0, remaining), 6),
        "read_energy_pj": round(total_read, 6),
        "write_energy_pj": round(total_write, 6),
        "max_access_time_ns": round(max_access, 6),
        "selected_macros": selected,
    }


def _score32_row(service_closure: JsonDict) -> JsonDict:
    return _as_dict(service_closure.get("selected_score32_row"))


def _best_measured_sram_row(measured_sram: JsonDict) -> JsonDict:
    return _as_dict(measured_sram.get("best"))


def _build_row(
    *,
    efficiency: float,
    placement_overhead_fraction: float,
    score32_row: JsonDict,
    measured_sram_row: JsonDict,
    composition_quantities: JsonDict,
    local_capacity_payload: JsonDict,
    macros: list[JsonDict],
) -> JsonDict:
    sram_budget_um2 = float(composition_quantities["sram_budget_area_um2"])
    tile_area_um2 = float(composition_quantities["tile_sram_total_area_um2_for_active_clusters"])
    service_area_um2 = float(composition_quantities.get("scaled_local_service_area_all_clusters_um2", 0.0) or 0.0)
    shared_envelope_budget_um2 = max(0.0, sram_budget_um2 - tile_area_um2 - service_area_um2)
    macro_area_budget_um2 = shared_envelope_budget_um2 * efficiency * (1.0 - placement_overhead_fraction)
    pack = _pack_capacity(macro_area_budget_um2=macro_area_budget_um2, macros=macros)
    kv_cache_bytes = int(round(float(measured_sram_row["kv_cache_mib"]) * 1024.0 * 1024.0))
    shared_byte_share = min(kv_cache_bytes, int(pack["capacity_bytes"])) / kv_cache_bytes if kv_cache_bytes else 0.0
    hbm_byte_share = max(0.0, 1.0 - shared_byte_share)
    source_hbm_share = float(measured_sram_row.get("hbm_byte_share", score32_row.get("hbm_byte_share", 1.0)))
    hbm_share_scale = hbm_byte_share / max(1e-12, source_hbm_share)
    source_latency_us = float(score32_row.get("replica_recost_latency_us") or score32_row.get("adjusted_latency_us_if_feasible") or 0.0)
    source_hbm_cycles = int(score32_row.get("tile_hbm_cycles") or score32_row.get("controller_service_cycles") or 0)
    projected_hbm_cycles = int(math.ceil(source_hbm_cycles * hbm_share_scale)) if source_hbm_cycles else None
    projected_latency_us = source_latency_us * max(1.0, hbm_share_scale)
    return {
        "placement_efficiency": round(efficiency, 6),
        "placement_overhead_fraction": round(placement_overhead_fraction, 6),
        "sram_budget_area_um2": round(sram_budget_um2, 6),
        "tile_local_sram_area_um2": round(tile_area_um2, 6),
        "endpoint_router_fifo_area_um2": round(service_area_um2, 6),
        "shared_sram_envelope_budget_um2": round(shared_envelope_budget_um2, 6),
        "shared_sram_macro_area_budget_um2": round(macro_area_budget_um2, 6),
        "shared_sram_capacity_mib": pack["capacity_mib"],
        "shared_sram_macro_area_um2": pack["macro_area_um2"],
        "shared_sram_envelope_area_um2": round(pack["macro_area_um2"] / efficiency if efficiency else 0.0, 6),
        "shared_sram_pack": pack,
        "shared_byte_share": round(shared_byte_share, 9),
        "hbm_byte_share": round(hbm_byte_share, 9),
        "hbm_share_scale_vs_measured_sram": round(hbm_share_scale, 9),
        "source_score32_latency_us": round(source_latency_us, 6),
        "projected_latency_us_hbm_share_scaled": round(projected_latency_us, 6),
        "source_tile_hbm_cycles": source_hbm_cycles,
        "projected_tile_hbm_cycles": projected_hbm_cycles,
        "tile_local_capacity_bytes_per_cluster": int(composition_quantities["tile_sram_allocated_bytes_per_cluster"]),
        "replaced_abstract_local_capacity_bytes_per_cluster": int(
            measured_sram_row.get("abstract_local_capacity_bytes_per_cluster_replaced", 0)
            or _as_dict(local_capacity_payload.get("selected_frontier")).get("local_capacity_bytes_per_cluster", 0)
        ),
        "fits_sram_area_budget": (pack["macro_area_um2"] / efficiency if efficiency else 0.0)
        + tile_area_um2
        + service_area_um2
        <= sram_budget_um2 + 1e-6,
    }


def build_report(args: argparse.Namespace) -> JsonDict:
    service_closure = _load_json(args.service_closure_json)
    measured_sram = _load_json(args.measured_sram_rebalance_json)
    local_capacity = _load_json(args.local_sram_capacity_json)
    composition = _load_json(args.endpoint_router_sram_composition_json)
    score32_row = _score32_row(service_closure)
    measured_sram_row = _best_measured_sram_row(measured_sram)
    quantities = _as_dict(composition.get("composition_quantities"))
    macros = _macro_library(local_capacity)

    rows = [
        _build_row(
            efficiency=efficiency,
            placement_overhead_fraction=args.placement_overhead_fraction,
            score32_row=score32_row,
            measured_sram_row=measured_sram_row,
            composition_quantities=quantities,
            local_capacity_payload=local_capacity,
            macros=macros,
        )
        for efficiency in args.placement_efficiency
    ]
    rows_sorted = sorted(rows, key=lambda item: float(item["placement_efficiency"]), reverse=True)
    conservative = min(rows_sorted, key=lambda item: float(item["placement_efficiency"]))
    nominal = min(rows_sorted, key=lambda item: abs(float(item["placement_efficiency"]) - args.nominal_efficiency))
    hbm_share_delta = float(conservative["hbm_byte_share"]) - float(measured_sram_row["hbm_byte_share"])
    decision = (
        "score32_exp_lut_sram_hierarchy_envelope_stable"
        if hbm_share_delta <= args.max_hbm_share_delta_for_stable
        else "score32_exp_lut_sram_hierarchy_envelope_changes_frontier"
    )
    return {
        "version": 1,
        "model": "llm_decoder_attention_score32_exp_lut_sram_hierarchy_envelope_v1",
        "decision": decision,
        "inputs": {
            "service_closure_json": str(args.service_closure_json),
            "measured_sram_rebalance_json": str(args.measured_sram_rebalance_json),
            "local_sram_capacity_json": str(args.local_sram_capacity_json),
            "endpoint_router_sram_composition_json": str(args.endpoint_router_sram_composition_json),
        },
        "diagnosis": {
            "score32_supported": _as_dict(service_closure.get("diagnosis")).get("score32_supported"),
            "selected_semantic_profile": _as_dict(service_closure.get("diagnosis")).get("selected_semantic_profile"),
            "source_score32_latency_us": score32_row.get("replica_recost_latency_us")
            or score32_row.get("adjusted_latency_us_if_feasible"),
            "source_hbm_byte_share": measured_sram_row.get("hbm_byte_share"),
            "nominal_efficiency": nominal["placement_efficiency"],
            "nominal_shared_sram_capacity_mib": nominal["shared_sram_capacity_mib"],
            "nominal_hbm_byte_share": nominal["hbm_byte_share"],
            "conservative_efficiency": conservative["placement_efficiency"],
            "conservative_shared_sram_capacity_mib": conservative["shared_sram_capacity_mib"],
            "conservative_hbm_byte_share": conservative["hbm_byte_share"],
            "conservative_hbm_share_delta": round(hbm_share_delta, 9),
            "conservative_projected_latency_us_hbm_share_scaled": conservative[
                "projected_latency_us_hbm_share_scaled"
            ],
            "sram_hierarchy_status": "placement_envelope_not_full_sram_pnr",
            "remaining_abstractions": ["hbm_dram_service", "sram_macro_floorplan_pnr"],
        },
        "rows": rows_sorted,
        "sram_macro_library": macros,
        "next_step": {
            "recommended_next_step": (
                "Prioritize HBM/DRAM service closure if the conservative SRAM placement envelope "
                "does not materially change hbm_byte_share; otherwise revisit SRAM hierarchy capacity."
            ),
            "requires_hbm_dram_closure": True,
            "requires_full_sram_macro_floorplan": True,
        },
        "assumptions": [
            "SRAM macro placement efficiency is modeled as macro_area/envelope_area and swept explicitly.",
            "Tile-local SRAM area and endpoint/router/FIFO area are reserved before packing shared SRAM.",
            "Shared SRAM capacity uses the existing CACTI macro library; this is a placement envelope, not a placed memory compiler floorplan.",
            "Latency sensitivity scales the score32 baseline by HBM byte-share change only; HBM/DRAM service remains inherited.",
        ],
    }


def write_markdown(path: Path, payload: JsonDict) -> None:
    diagnosis = payload["diagnosis"]
    lines = [
        "# Score32 exp-LUT SRAM Hierarchy Envelope",
        "",
        f"- decision: `{payload['decision']}`",
        f"- source score32 latency us: `{diagnosis.get('source_score32_latency_us')}`",
        f"- source hbm share: `{diagnosis.get('source_hbm_byte_share')}`",
        f"- nominal efficiency: `{diagnosis.get('nominal_efficiency')}`",
        f"- nominal shared MiB: `{diagnosis.get('nominal_shared_sram_capacity_mib')}`",
        f"- nominal hbm share: `{diagnosis.get('nominal_hbm_byte_share')}`",
        f"- conservative efficiency: `{diagnosis.get('conservative_efficiency')}`",
        f"- conservative shared MiB: `{diagnosis.get('conservative_shared_sram_capacity_mib')}`",
        f"- conservative hbm share delta: `{diagnosis.get('conservative_hbm_share_delta')}`",
        "",
        "## Sweep",
        "",
        "| efficiency | shared MiB | hbm share | projected latency us | shared envelope um2 | fits |",
        "|---:|---:|---:|---:|---:|---|",
    ]
    for row in payload["rows"]:
        lines.append(
            "| {placement_efficiency} | {shared_sram_capacity_mib} | {hbm_byte_share} | "
            "{projected_latency_us_hbm_share_scaled} | {shared_sram_envelope_area_um2} | "
            "{fits_sram_area_budget} |".format(**row)
        )
    lines.extend(["", "## Assumptions", ""])
    lines.extend(f"- {item}" for item in payload["assumptions"])
    lines.extend(["", "## Next Step", "", f"- {payload['next_step']['recommended_next_step']}"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--service-closure-json", type=Path, required=True)
    parser.add_argument("--measured-sram-rebalance-json", type=Path, required=True)
    parser.add_argument("--local-sram-capacity-json", type=Path, required=True)
    parser.add_argument("--endpoint-router-sram-composition-json", type=Path, required=True)
    parser.add_argument("--placement-efficiency", type=_float_list, default=[1.0, 0.85, 0.75, 0.65, 0.55])
    parser.add_argument("--nominal-efficiency", type=float, default=0.75)
    parser.add_argument("--placement-overhead-fraction", type=float, default=0.05)
    parser.add_argument("--max-hbm-share-delta-for-stable", type=float, default=0.01)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    args = parser.parse_args()
    if args.placement_overhead_fraction < 0.0 or args.placement_overhead_fraction >= 1.0:
        raise SystemExit("--placement-overhead-fraction must be in [0, 1)")
    payload = build_report(args)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(args.out_md, payload)
    print(json.dumps({"ok": True, "decision": payload["decision"], "out": str(args.out)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
