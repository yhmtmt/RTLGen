#!/usr/bin/env python3
"""Plan the next decoder producer/ranker/memory integration point."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import re
from typing import Any

JsonDict = dict[str, Any]


def _load_json(path: str | Path) -> JsonDict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _ceil_div(a: int, b: int) -> int:
    return (a + b - 1) // b


def _as_float(value: Any, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_int(value: Any, default: int = 0) -> int:
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _producer_mac_lanes(config: JsonDict) -> JsonDict:
    gemm = config.get("compute", {}).get("gemm", {})
    num_modules = _as_int(gemm.get("num_modules"), 1)
    lanes_per_module = _as_int(gemm.get("lanes_per_module", gemm.get("lanes")), 1)
    return {
        "num_modules": num_modules,
        "lanes_per_module": lanes_per_module,
        "mac_lanes_per_cycle": num_modules * lanes_per_module,
        "mac_type": gemm.get("mac_type"),
        "mac_source": gemm.get("mac_source", gemm.get("rtlgen_cpp", {}).get("module_name")),
    }


def _physical_boundary_summary(payload: JsonDict) -> JsonDict:
    diagnosis = payload.get("diagnosis") if isinstance(payload.get("diagnosis"), dict) else {}
    ok_rows = [
        row
        for row in payload.get("probe_rows", [])
        if isinstance(row, dict) and row.get("status") == "ok"
    ]
    row = max(ok_rows, key=lambda item: _as_int(item.get("num_modules")), default={})
    metrics = row.get("metrics_row") if isinstance(row.get("metrics_row"), dict) else {}
    synthesis = row.get("synthesis") if isinstance(row.get("synthesis"), dict) else {}
    log_tail = synthesis.get("log_tail") if isinstance(synthesis.get("log_tail"), list) else []
    placed_cell_area = None
    for line in log_tail:
        match = re.search(r"Placed Cell Area\s+([0-9.]+)", str(line))
        if match:
            placed_cell_area = _as_float(match.group(1))
            break
    return {
        "source_decision": diagnosis.get("decision"),
        "make_target": payload.get("make_target"),
        "boundary_kind": payload.get("boundary_kind"),
        "num_modules": row.get("num_modules"),
        "critical_path_ns": _as_float(metrics.get("critical_path_ns")),
        "die_area_um2": _as_float(metrics.get("die_area")),
        "placed_cell_area_um2": placed_cell_area,
        "total_power_mw": _as_float(metrics.get("total_power_mw")),
        "synthesis_elapsed_seconds": synthesis.get("elapsed_seconds"),
        "result_path": metrics.get("result_path") or metrics.get("work_result_json"),
        "die_area_note": "die_area is the bounded floorplan area; placed_cell_area is preferred for extrapolation when present.",
    }


def _service_rows_by_key(coupling: JsonDict) -> dict[tuple[Any, ...], JsonDict]:
    keyed: dict[tuple[Any, ...], JsonDict] = {}
    for row in coupling.get("producer_service_sweep", []):
        key = (
            row.get("scenario"),
            row.get("hidden_size"),
            row.get("vocab_size"),
            row.get("producer_lanes"),
            row.get("macs_per_cycle"),
            row.get("memory_share"),
            row.get("producer_ii_cycles"),
        )
        keyed[key] = row
    return keyed


def _match_coupled_row(
    coupling: JsonDict,
    *,
    hidden_size: int,
    vocab_size: int,
    producer_choice: JsonDict,
) -> JsonDict | None:
    candidates = []
    for row in coupling.get("coupled_ranker_sweep", []):
        if int(row.get("hidden_size", 0) or 0) != hidden_size:
            continue
        if int(row.get("vocab_size", 0) or 0) != vocab_size:
            continue
        if row.get("producer_lanes") != producer_choice.get("producer_lanes"):
            continue
        if row.get("top_k") != producer_choice.get("top_k"):
            continue
        if row.get("producer_ii_cycles") != producer_choice.get("producer_ii_cycles"):
            continue
        candidates.append(row)
    if not candidates:
        return None
    return min(candidates, key=lambda row: _as_float(row.get("coupled_latency_us_per_token")))


def _projection_with_measured_mac_lanes(
    *,
    service: JsonDict,
    measured_mac_lanes: int,
    physical_clock_ns: float,
) -> JsonDict:
    vocab_size = _as_int(service.get("vocab_size"))
    hidden_size = _as_int(service.get("hidden_size"))
    producer_lanes = _as_int(service.get("producer_lanes"))
    tile_count = _ceil_div(vocab_size, producer_lanes)
    macs_per_tile = producer_lanes * hidden_size
    measured_compute_cycles_per_tile = _ceil_div(macs_per_tile, measured_mac_lanes)
    memory_cycles_per_tile = _as_int(service.get("weight_cycles_per_tile"))
    hidden_load_cycles = _as_int(service.get("hidden_load_cycles"))
    measured_ii_cycles = max(1, measured_compute_cycles_per_tile, memory_cycles_per_tile)
    measured_total_cycles = (
        hidden_load_cycles
        + measured_compute_cycles_per_tile
        + max(0, tile_count - 1) * measured_ii_cycles
    )
    analytical_macs_per_cycle = _as_int(service.get("macs_per_cycle"))
    equivalent_clusters = _ceil_div(analytical_macs_per_cycle, measured_mac_lanes)
    return {
        "measured_mac_lanes_per_cycle": measured_mac_lanes,
        "analytical_macs_per_cycle": analytical_macs_per_cycle,
        "equivalent_nm16_clusters_for_analytical_macs": equivalent_clusters,
        "tile_count": tile_count,
        "macs_per_tile": macs_per_tile,
        "analytical_compute_cycles_per_tile": service.get("compute_cycles_per_tile"),
        "measured_compute_cycles_per_tile": measured_compute_cycles_per_tile,
        "weight_cycles_per_tile": memory_cycles_per_tile,
        "hidden_load_cycles": hidden_load_cycles,
        "measured_ii_cycles": measured_ii_cycles,
        "model_clock_latency_us_per_token": round(measured_total_cycles * 1.0 / 1000.0, 6),
        "physical_clock_latency_us_per_token": round(measured_total_cycles * physical_clock_ns / 1000.0, 6),
    }


def build_report(
    *,
    frontier: JsonDict,
    coupling: JsonDict,
    producer_physical: JsonDict,
    producer_config: JsonDict,
    stream_contract_path: str,
) -> JsonDict:
    mac_summary = _producer_mac_lanes(producer_config)
    physical = _physical_boundary_summary(producer_physical)
    service_by_key = _service_rows_by_key(coupling)
    rows: list[JsonDict] = []
    for focus in frontier.get("focus_summary", []):
        producer_choice = focus.get("producer_choice") if isinstance(focus.get("producer_choice"), dict) else {}
        coupled = _match_coupled_row(
            coupling,
            hidden_size=_as_int(focus.get("hidden_size")),
            vocab_size=_as_int(focus.get("vocab_size")),
            producer_choice=producer_choice,
        )
        if coupled is None:
            continue
        service = service_by_key.get(
            (
                coupled.get("scenario"),
                coupled.get("hidden_size"),
                coupled.get("vocab_size"),
                coupled.get("producer_lanes"),
                coupled.get("macs_per_cycle"),
                coupled.get("memory_share"),
                coupled.get("producer_ii_cycles"),
            )
        )
        if service is None:
            continue
        projection = _projection_with_measured_mac_lanes(
            service=service,
            measured_mac_lanes=mac_summary["mac_lanes_per_cycle"],
            physical_clock_ns=physical["critical_path_ns"] or 1.0,
        )
        ranker_us = _as_float(coupled.get("ranker_latency_us_per_token"))
        model_clock_limiter = (
            "producer_mac_limited"
            if projection["model_clock_latency_us_per_token"] > ranker_us
            else "ranker"
        )
        physical_clock_limiter = (
            "producer_mac_limited"
            if projection["physical_clock_latency_us_per_token"] > ranker_us
            else "ranker"
        )
        rows.append(
            {
                "label": focus.get("label"),
                "sequence_length": focus.get("sequence_length"),
                "hidden_size": focus.get("hidden_size"),
                "vocab_size": focus.get("vocab_size"),
                "frontier_dominant_component": focus.get("dominant_component"),
                "producer_choice": producer_choice,
                "coupled_model": {
                    "scenario": coupled.get("scenario"),
                    "macs_per_cycle": coupled.get("macs_per_cycle"),
                    "memory_share": coupled.get("memory_share"),
                    "producer_latency_us_per_token": coupled.get("producer_latency_us_per_token"),
                    "ranker_latency_us_per_token": coupled.get("ranker_latency_us_per_token"),
                    "coupled_latency_us_per_token": coupled.get("coupled_latency_us_per_token"),
                    "ranker_fifo_capacity_ok": coupled.get("ranker_fifo_capacity_ok"),
                    "ranker_required_fifo_depth_groups": coupled.get("ranker_required_fifo_depth_groups"),
                    "ranker_candidate_memory_bytes": coupled.get("ranker_candidate_memory_bytes"),
                },
                "nm16_mac_projection": projection,
                "bottleneck_if_nm16_model_clock": model_clock_limiter,
                "bottleneck_if_nm16_physical_clock": physical_clock_limiter,
            }
        )

    first_target = rows[0] if rows else {}
    area_basis = physical.get("placed_cell_area_um2") or physical.get("die_area_um2") or 0.0
    clusters = (
        first_target.get("nm16_mac_projection", {}).get("equivalent_nm16_clusters_for_analytical_macs")
        if first_target
        else None
    )
    return {
        "version": 0.1,
        "model": "decoder_producer_ranker_memory_integration_plan_v1",
        "inputs": {
            "frontier_model": frontier.get("model"),
            "coupling_model": coupling.get("model"),
            "stream_contract": stream_contract_path,
        },
        "producer_physical_anchor": physical,
        "producer_config_summary": mac_summary,
        "integration_rows": rows,
        "recommendation": {
            "next_target": {
                "name": "r64_k1_nm16_ready_valid_equivalence",
                "reason": "Use the smallest focus row that already dominates the frontier before attempting larger producer parallelism.",
                "producer_lanes": first_target.get("producer_choice", {}).get("producer_lanes"),
                "top_k": first_target.get("producer_choice", {}).get("top_k"),
                "hidden_size": first_target.get("hidden_size"),
                "vocab_size": first_target.get("vocab_size"),
                "measured_mac_lanes_per_cycle": mac_summary["mac_lanes_per_cycle"],
            },
            "implementation_order": [
                "add producer-to-ranker LogitTileStream/CandidateStream ready-valid equivalence harness",
                "measure a macro-style r64/k1 wrapper with one-entry skid buffers and no exposed scalar logit pins",
                "only then scale producer MAC parallelism or shared-memory/NoC arbitration",
            ],
            "large_array_gap": {
                "analytical_macs_per_cycle": first_target.get("coupled_model", {}).get("macs_per_cycle"),
                "equivalent_nm16_clusters": clusters,
                "area_basis_um2_per_nm16_cluster": area_basis,
                "area_basis_kind": (
                    "placed_cell_area" if physical.get("placed_cell_area_um2") else "floorplan_die_area"
                ),
                "do_not_charge_padded_die_area_blindly": True,
            },
        },
        "assumptions": [
            "Producer num_modules and producer_lanes are different axes: num_modules is measured FP16 MAC parallelism, producer_lanes is logit tile width.",
            "The nm16 physical anchor proves bounded feasibility for the current generated producer wrapper, not an 8192-MAC output-projection array.",
            "Latency rows are recalculated with the same weight-memory model but with measured nm16 MAC lanes to expose the physical/analytical gap.",
            "Ready/valid stream equivalence must be validated before integrated RTL PPA is used in rankings.",
        ],
    }


def _write_markdown(path: Path, payload: JsonDict) -> None:
    rec = payload["recommendation"]
    phys = payload["producer_physical_anchor"]
    cfg = payload["producer_config_summary"]
    lines = [
        "# Decoder Producer/Ranker/Memory Integration Plan",
        "",
        f"- model: `{payload['model']}`",
        f"- measured_mac_lanes_per_cycle: `{cfg['mac_lanes_per_cycle']}`",
        f"- physical_anchor: `nm{phys.get('num_modules')} {phys.get('make_target')} cp={phys.get('critical_path_ns')}ns`",
        f"- next_target: `{rec['next_target']['name']}`",
        "",
        "## Integration Rows",
        "",
        "| shape | W | top_k | model MAC/cyc | ranker_us | nm16_model_us | nm16_physical_us | model limiter | physical limiter | clusters |",
        "|---|---:|---:|---:|---:|---:|---:|---|---|---:|",
    ]
    for row in payload["integration_rows"]:
        prod = row["producer_choice"]
        coupled = row["coupled_model"]
        proj = row["nm16_mac_projection"]
        lines.append(
            "| {label} | {w} | {k} | {macs} | {ranker_us} | {model_us} | {physical_us} | {model_limiter} | {physical_limiter} | {clusters} |".format(
                label=row["label"],
                w=prod.get("producer_lanes"),
                k=prod.get("top_k"),
                macs=coupled.get("macs_per_cycle"),
                ranker_us=coupled.get("ranker_latency_us_per_token"),
                model_us=proj.get("model_clock_latency_us_per_token"),
                physical_us=proj.get("physical_clock_latency_us_per_token"),
                model_limiter=row["bottleneck_if_nm16_model_clock"],
                physical_limiter=row["bottleneck_if_nm16_physical_clock"],
                clusters=proj.get("equivalent_nm16_clusters_for_analytical_macs"),
            )
        )
    lines.extend(
        [
            "",
            "## Recommendation",
            "",
        ]
    )
    for item in rec["implementation_order"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Assumptions", ""])
    for item in payload["assumptions"]:
        lines.append(f"- {item}")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Plan decoder producer/ranker/memory integration")
    ap.add_argument("--frontier-synthesis", required=True)
    ap.add_argument("--producer-ranker-coupled", required=True)
    ap.add_argument("--producer-physical-boundary", required=True)
    ap.add_argument("--producer-config", required=True)
    ap.add_argument("--stream-contract", default="npu/docs/decoder_logit_rank_streaming_hierarchy.md")
    ap.add_argument("--out", required=True)
    ap.add_argument("--out-md", required=True)
    args = ap.parse_args()
    payload = build_report(
        frontier=_load_json(args.frontier_synthesis),
        coupling=_load_json(args.producer_ranker_coupled),
        producer_physical=_load_json(args.producer_physical_boundary),
        producer_config=_load_json(args.producer_config),
        stream_contract_path=args.stream_contract,
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    out_md = Path(args.out_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    _write_markdown(out_md, payload)
    print(json.dumps({"ok": True, "out": str(out), "out_md": str(out_md)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
