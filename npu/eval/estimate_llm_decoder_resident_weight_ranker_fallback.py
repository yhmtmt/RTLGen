#!/usr/bin/env python3
"""Compare buffering and rank-tree fallbacks for fast resident-weight producers."""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any

JsonDict = dict[str, Any]
R64_LANES = 64


def _load_json(path: str | Path) -> JsonDict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _maybe_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _ceil_div(a: int, b: int) -> int:
    return (a + b - 1) // b


def _placed_cell_area(variant: JsonDict) -> float | None:
    synthesis = variant.get("synthesis") if isinstance(variant.get("synthesis"), dict) else {}
    for line in synthesis.get("log_tail", []):
        match = re.search(r"Placed Cell Area\s+([0-9.]+)", str(line))
        if match:
            return float(match.group(1))
    return None


def _serial_thresholds(cadence: JsonDict) -> dict[str, JsonDict]:
    return {
        str(key): value
        for key, value in cadence.get("ranker_zero_backpressure_thresholds", {}).items()
        if isinstance(value, dict)
    }


def _serial_costs(cadence: JsonDict) -> dict[str, JsonDict]:
    return {
        str(key): value
        for key, value in cadence.get("ranker_costs", {}).items()
        if isinstance(value, dict)
    }


def _rank_tree_costs(rank_tree: JsonDict) -> list[JsonDict]:
    rows: list[JsonDict] = []
    for variant in rank_tree.get("variants", []):
        if not isinstance(variant, dict) or variant.get("status") != "ok":
            continue
        metrics = variant.get("metrics_row") if isinstance(variant.get("metrics_row"), dict) else {}
        rows.append(
            {
                "ranker": f"ranktree_radix{int(variant.get('radix'))}",
                "radix": int(variant.get("radix")),
                "pipeline_stages": int(variant.get("pipeline_stages", 0)),
                "ranker_service_cycles": 1,
                "critical_path_ns": _maybe_float(metrics.get("critical_path_ns")),
                "total_power_mw": _maybe_float(metrics.get("total_power_mw")),
                "die_area_um2": _maybe_float(metrics.get("die_area")),
                "placed_cell_area_um2": _placed_cell_area(variant),
            }
        )
    return rows


def _required_waiting_buffer_tiles(
    *,
    producer_tile_count: int,
    chunks_per_producer_tile: int,
    producer_ii_cycles: int,
    consumer_ii_cycles: int,
) -> int:
    queue = 0
    max_queue = 0
    next_done: int | None = None
    for tile in range(producer_tile_count):
        arrival = tile * producer_ii_cycles
        while next_done is not None and next_done <= arrival:
            if queue > 0:
                queue -= 1
                next_done += consumer_ii_cycles
            else:
                next_done = None
                break
        queue += chunks_per_producer_tile
        if next_done is None and queue > 0:
            queue -= 1
            next_done = arrival + consumer_ii_cycles
        max_queue = max(max_queue, queue)
    return max_queue


def _buffer_option(
    *,
    row: JsonDict,
    ranker: str,
    threshold: JsonDict,
    cost: JsonDict,
    logit_bits: int,
) -> JsonDict:
    producer_lanes = int(row["producer_lanes"])
    chunks = _ceil_div(producer_lanes, R64_LANES)
    depth_tiles = _required_waiting_buffer_tiles(
        producer_tile_count=int(row["tile_count"]),
        chunks_per_producer_tile=chunks,
        producer_ii_cycles=int(row["producer_ii_cycles"]),
        consumer_ii_cycles=int(threshold["min_zero_backpressure_ii_cycles"]),
    )
    return {
        "strategy": f"buffered_{ranker}",
        "ranker": ranker,
        "chunks_per_producer_tile": chunks,
        "consumer_ii_cycles": int(threshold["min_zero_backpressure_ii_cycles"]),
        "required_buffer_r64_tiles": depth_tiles,
        "required_buffer_bytes": depth_tiles * R64_LANES * math.ceil(logit_bits / 8),
        "ranker_total_power_mw": cost.get("total_power_mw"),
        "ranker_critical_path_ns": cost.get("critical_path_ns"),
        "ranker_service_cycles": cost.get("ranker_service_cycles"),
        "decision": "buffer_feasible",
    }


def _rank_tree_option(
    *,
    row: JsonDict,
    tree: JsonDict,
    integration: str,
    logit_bits: int,
) -> JsonDict:
    producer_lanes = int(row["producer_lanes"])
    chunks = _ceil_div(producer_lanes, R64_LANES)
    banked = integration == "banked_r64_ranktrees"
    instances = chunks if banked else 1
    consumer_ii = 1 if banked else chunks
    offered_units = 1 if banked else chunks
    queued_units = _required_waiting_buffer_tiles(
        producer_tile_count=int(row["tile_count"]),
        chunks_per_producer_tile=offered_units,
        producer_ii_cycles=int(row["producer_ii_cycles"]),
        consumer_ii_cycles=consumer_ii,
    )
    depth_tiles = queued_units * chunks if banked else queued_units
    power = tree.get("total_power_mw")
    area = tree.get("placed_cell_area_um2")
    return {
        "strategy": f"{integration}_{tree['ranker']}",
        "ranker": tree["ranker"],
        "integration": integration,
        "ranker_instances": instances,
        "consumer_ii_cycles": consumer_ii,
        "required_buffer_r64_tiles": depth_tiles,
        "required_buffer_bytes": depth_tiles * R64_LANES * math.ceil(logit_bits / 8),
        "ranker_total_power_mw": None if power is None else power * instances,
        "ranker_placed_cell_area_um2": None if area is None else area * instances,
        "ranker_critical_path_ns": tree.get("critical_path_ns"),
        "ranker_service_cycles": consumer_ii,
        "decision": "rank_tree_feasible" if depth_tiles == 0 else "rank_tree_with_buffer",
    }


def _choose_option(options: list[JsonDict], *, small_buffer_tiles: int) -> JsonDict:
    small_buffers = [
        row
        for row in options
        if row["strategy"].startswith("buffered_serial_lpc4")
        and row["required_buffer_r64_tiles"] <= small_buffer_tiles
    ]
    if small_buffers:
        return min(small_buffers, key=lambda row: row["required_buffer_r64_tiles"])
    no_buffer_trees = [
        row for row in options if row["strategy"].startswith("single_r64_ranktrees") and row["required_buffer_r64_tiles"] == 0
    ]
    if no_buffer_trees:
        return min(
            no_buffer_trees,
            key=lambda row: (
                row.get("ranker_total_power_mw") is None,
                row.get("ranker_total_power_mw") if row.get("ranker_total_power_mw") is not None else math.inf,
            ),
        )
    return min(
        options,
        key=lambda row: (
            row["required_buffer_r64_tiles"],
            row.get("ranker_total_power_mw") is None,
            row.get("ranker_total_power_mw") if row.get("ranker_total_power_mw") is not None else math.inf,
        ),
    )


def build_report(
    *,
    cadence_sensitivity: JsonDict,
    rank_tree: JsonDict,
    logit_bits: int,
    small_buffer_tiles: int,
) -> JsonDict:
    thresholds = _serial_thresholds(cadence_sensitivity)
    serial_costs = _serial_costs(cadence_sensitivity)
    trees = _rank_tree_costs(rank_tree)
    unsafe_rows = [
        row
        for row in cadence_sensitivity.get("cadence_sweep", [])
        if isinstance(row, dict)
        and (row.get("selected_ranker") or {}).get("decision") != "serial_ranker_safe"
    ]
    fallback_rows: list[JsonDict] = []
    for row in unsafe_rows:
        options: list[JsonDict] = []
        for ranker in ("serial_lpc1", "serial_lpc2", "serial_lpc4"):
            if ranker in thresholds:
                options.append(
                    _buffer_option(
                        row=row,
                        ranker=ranker,
                        threshold=thresholds[ranker],
                        cost=serial_costs.get(ranker, {}),
                        logit_bits=logit_bits,
                    )
                )
        for tree in trees:
            options.append(
                _rank_tree_option(
                    row=row,
                    tree=tree,
                    integration="single_r64_ranktrees",
                    logit_bits=logit_bits,
                )
            )
            if int(row["producer_lanes"]) > R64_LANES:
                options.append(
                    _rank_tree_option(
                        row=row,
                        tree=tree,
                        integration="banked_r64_ranktrees",
                        logit_bits=logit_bits,
                    )
                )
        fallback_rows.append(
            {
                "producer": {
                    key: row[key]
                    for key in (
                        "vocab_size",
                        "hidden_size",
                        "producer_lanes",
                        "tile_count",
                        "macs_per_cycle",
                        "memory_bandwidth_bytes_per_cycle",
                        "weight_cache_hit_rate",
                        "producer_ii_cycles",
                        "service_limiter",
                    )
                },
                "options": options,
                "recommended": _choose_option(options, small_buffer_tiles=small_buffer_tiles),
            }
        )

    rank_tree_count = sum(
        1 for row in fallback_rows if "ranktree" in str(row["recommended"].get("strategy", ""))
    )
    buffered_count = len(fallback_rows) - rank_tree_count
    return {
        "version": 0.1,
        "model": "decoder_resident_weight_ranker_fallback_v1",
        "inputs": {
            "logit_bits": logit_bits,
            "small_buffer_tiles": small_buffer_tiles,
        },
        "assumptions": [
            "Unsafe rows are producer cadence rows where prior serial replay has no zero-backpressure ranker.",
            "Buffer depth is simulated as r64 logit-tile chunks waiting in front of the ranker, excluding the tile in service.",
            "Rank-tree fallback reuses measured r64/k1 rank-tree variants; single_r64 handles wider producer tiles sequentially, banked_r64 duplicates r64 rankers.",
            "The model ignores SRAM/FIFO implementation overhead beyond raw logit storage bytes.",
        ],
        "fallback_rows": fallback_rows,
        "recommendation": {
            "decision": (
                "rank_tree_fallback_preferred_for_resident_weight"
                if rank_tree_count >= buffered_count
                else "small_buffered_serial_fallback_preferred"
            ),
            "unsafe_rows": len(fallback_rows),
            "rank_tree_recommended_rows": rank_tree_count,
            "buffered_serial_recommended_rows": buffered_count,
            "next_step": (
                "Promote a rank-tree fallback wrapper for resident-weight producer rows, while keeping buffered serial_lpc4 only for near-threshold cadence cases."
                if rank_tree_count >= buffered_count
                else "Evaluate a small input FIFO in front of serial_lpc4 for near-threshold resident/cache-backed producer rows."
            ),
        },
    }


def write_markdown(path: Path, payload: JsonDict) -> None:
    rec = payload["recommendation"]
    lines = [
        "# Decoder Resident-Weight Ranker Fallback",
        "",
        f"- model: `{payload['model']}`",
        f"- decision: `{rec['decision']}`",
        f"- unsafe_rows: `{rec['unsafe_rows']}`",
        f"- rank_tree_recommended_rows: `{rec['rank_tree_recommended_rows']}`",
        f"- buffered_serial_recommended_rows: `{rec['buffered_serial_recommended_rows']}`",
        f"- next_step: {rec['next_step']}",
        "",
        "## Fallback Rows",
        "",
        "| vocab | hidden | W | prod II | hit | recommended | buffer r64 tiles | buffer bytes | power mW |",
        "|---:|---:|---:|---:|---:|---|---:|---:|---:|",
    ]
    for row in payload["fallback_rows"][:96]:
        producer = row["producer"]
        selected = row["recommended"]
        lines.append(
            "| {vocab} | {hidden} | {lanes} | {ii} | {hit} | {strategy} | {depth} | {bytes} | {power} |".format(
                vocab=producer["vocab_size"],
                hidden=producer["hidden_size"],
                lanes=producer["producer_lanes"],
                ii=producer["producer_ii_cycles"],
                hit=producer["weight_cache_hit_rate"],
                strategy=selected["strategy"],
                depth=selected["required_buffer_r64_tiles"],
                bytes=selected["required_buffer_bytes"],
                power=selected.get("ranker_total_power_mw"),
            )
        )
    lines.extend(["", "## Assumptions", ""])
    for item in payload["assumptions"]:
        lines.append(f"- {item}")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cadence-sensitivity", required=True)
    ap.add_argument("--rank-tree", required=True)
    ap.add_argument("--logit-bits", type=int, default=16)
    ap.add_argument("--small-buffer-tiles", type=int, default=32)
    ap.add_argument("--out", required=True)
    ap.add_argument("--out-md", required=True)
    args = ap.parse_args()

    payload = build_report(
        cadence_sensitivity=_load_json(args.cadence_sensitivity),
        rank_tree=_load_json(args.rank_tree),
        logit_bits=args.logit_bits,
        small_buffer_tiles=args.small_buffer_tiles,
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    out_md = Path(args.out_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    write_markdown(out_md, payload)
    print(json.dumps({"ok": True, "out": str(out), "out_md": str(out_md)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
