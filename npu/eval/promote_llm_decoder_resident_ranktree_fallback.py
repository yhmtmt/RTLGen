#!/usr/bin/env python3
"""Promote the resident-weight output-projection rank-tree fallback policy."""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any


JsonDict = dict[str, Any]
R64_LANES = 64
STRATEGY_RE = re.compile(r"^(single|banked)_r64_ranktrees_ranktree_radix(?P<radix>\d+)$")


def _load_json(path: str | Path) -> JsonDict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _maybe_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _placed_cell_area(variant: JsonDict | None) -> float | None:
    if not isinstance(variant, dict):
        return None
    synthesis = variant.get("synthesis") if isinstance(variant.get("synthesis"), dict) else {}
    for line in synthesis.get("log_tail", []):
        match = re.search(r"Placed Cell Area\s+([0-9.]+)", str(line))
        if match:
            return float(match.group(1))
    return None


def _variant_by_radix(rank_tree: JsonDict, radix: int) -> JsonDict | None:
    for variant in rank_tree.get("variants", []):
        if not isinstance(variant, dict):
            continue
        if int(variant.get("radix", -1)) == radix:
            return variant
    return None


def _metrics_summary(variant: JsonDict | None) -> JsonDict | None:
    if not isinstance(variant, dict):
        return None
    metrics = variant.get("metrics_row") if isinstance(variant.get("metrics_row"), dict) else {}
    return {
        "top": variant.get("top"),
        "radix": variant.get("radix"),
        "pipeline_stages": variant.get("pipeline_stages"),
        "critical_path_ns": _maybe_float(metrics.get("critical_path_ns")),
        "die_area_um2": _maybe_float(metrics.get("die_area")),
        "placed_cell_area_um2": _placed_cell_area(variant),
        "total_power_mw": _maybe_float(metrics.get("total_power_mw")),
        "metrics_status": metrics.get("status"),
        "simulation_status": (variant.get("simulation") or {}).get("status")
        if isinstance(variant.get("simulation"), dict)
        else None,
        "design_dir": variant.get("design_dir"),
    }


def _recommended_rows(fallback: JsonDict) -> list[JsonDict]:
    rows: list[JsonDict] = []
    for row in fallback.get("fallback_rows", []):
        if isinstance(row, dict) and isinstance(row.get("recommended"), dict):
            rows.append(row)
    return rows


def _selected_strategy(row: JsonDict) -> str:
    return str((row.get("recommended") or {}).get("strategy", ""))


def _strategy_radix(strategy: str) -> int | None:
    match = STRATEGY_RE.match(strategy)
    if not match:
        return None
    return int(match.group("radix"))


def _producer_mode(row: JsonDict) -> str:
    producer = row.get("producer") if isinstance(row.get("producer"), dict) else {}
    lanes = int(producer.get("producer_lanes", R64_LANES))
    return "single_r64_ranktree" if lanes <= R64_LANES else "banked_r64_ranktrees"


def _mode_summaries(rows: list[JsonDict], *, selected_radix: int, selected_metrics: JsonDict | None) -> list[JsonDict]:
    summaries: list[JsonDict] = []
    power = (selected_metrics or {}).get("total_power_mw")
    area = (selected_metrics or {}).get("placed_cell_area_um2")
    for mode in ("single_r64_ranktree", "banked_r64_ranktrees"):
        mode_rows = [row for row in rows if _producer_mode(row) == mode]
        if not mode_rows:
            continue
        lane_values = sorted(
            {
                int((row.get("producer") or {}).get("producer_lanes", R64_LANES))
                for row in mode_rows
            }
        )
        max_lanes = max(lane_values)
        instances = math.ceil(max_lanes / R64_LANES)
        summaries.append(
            {
                "mode": mode,
                "recommended_strategy_count": len(mode_rows),
                "producer_lanes": lane_values,
                "ranktree_radix": selected_radix,
                "ranker_instances": instances,
                "consumer_ii_cycles": 1,
                "max_required_buffer_r64_tiles": max(
                    int((row.get("recommended") or {}).get("required_buffer_r64_tiles", 0))
                    for row in mode_rows
                ),
                "producer_ii_cycles_min": min(
                    int((row.get("producer") or {}).get("producer_ii_cycles", 0))
                    for row in mode_rows
                ),
                "producer_ii_cycles_max": max(
                    int((row.get("producer") or {}).get("producer_ii_cycles", 0))
                    for row in mode_rows
                ),
                "ranker_total_power_mw": None if power is None else power * instances,
                "ranker_placed_cell_area_um2": None if area is None else area * instances,
            }
        )
    return summaries


def build_report(*, fallback: JsonDict, rank_tree: JsonDict) -> JsonDict:
    rows = _recommended_rows(fallback)
    strategy_counts = Counter(_selected_strategy(row) for row in rows)
    selected_radices = sorted(
        {
            radix
            for radix in (_strategy_radix(strategy) for strategy in strategy_counts)
            if radix is not None
        }
    )
    selected_radix = selected_radices[0] if len(selected_radices) == 1 else None
    selected_variant = _variant_by_radix(rank_tree, selected_radix) if selected_radix is not None else None
    selected_metrics = _metrics_summary(selected_variant)
    all_rank_tree = bool(rows) and all(_strategy_radix(_selected_strategy(row)) is not None for row in rows)
    max_buffer = max(
        (int((row.get("recommended") or {}).get("required_buffer_r64_tiles", 0)) for row in rows),
        default=None,
    )
    fallback_rec = fallback.get("recommendation") if isinstance(fallback.get("recommendation"), dict) else {}
    checks = [
        {
            "name": "fallback_prefers_rank_tree",
            "passed": fallback_rec.get("decision") == "rank_tree_fallback_preferred_for_resident_weight",
            "observed": fallback_rec,
        },
        {
            "name": "all_unsafe_rows_have_rank_tree_strategy",
            "passed": all_rank_tree,
            "observed": dict(strategy_counts),
        },
        {
            "name": "rank_tree_strategy_has_single_radix",
            "passed": selected_radix is not None,
            "observed": selected_radices,
        },
        {
            "name": "selected_rank_tree_variant_has_clean_rtl_sim",
            "passed": isinstance(selected_variant, dict)
            and selected_variant.get("status") == "ok"
            and (selected_variant.get("simulation") or {}).get("status") == "ok",
            "observed": None if selected_variant is None else selected_variant.get("simulation"),
        },
        {
            "name": "selected_rank_tree_variant_has_physical_metrics",
            "passed": isinstance(selected_variant, dict)
            and (selected_variant.get("metrics_row") or {}).get("status") == "ok",
            "observed": selected_metrics,
        },
        {
            "name": "promotion_requires_no_waiting_buffer",
            "passed": max_buffer == 0,
            "observed": max_buffer,
        },
    ]
    passed = all(bool(check["passed"]) for check in checks)
    return {
        "version": 0.1,
        "model": "decoder_resident_ranktree_fallback_promotion_v1",
        "target": {
            "producer_role": "resident_weight_output_projection",
            "producer_lanes_supported": sorted(
                {
                    int((row.get("producer") or {}).get("producer_lanes", R64_LANES))
                    for row in rows
                }
            ),
            "top_k": 1,
            "selected_radix": selected_radix,
            "wrapper_role": "rank_tree_fallback_for_resident_weight_output_projection",
        },
        "coverage": {
            "unsafe_rows": len(rows),
            "strategy_counts": dict(strategy_counts),
            "max_required_buffer_r64_tiles": max_buffer,
        },
        "selected_ranktree_variant": selected_variant,
        "selected_metrics": selected_metrics,
        "producer_modes": (
            []
            if selected_radix is None
            else _mode_summaries(rows, selected_radix=selected_radix, selected_metrics=selected_metrics)
        ),
        "checks": checks,
        "decision": {
            "decision": (
                "resident_weight_ranktree_fallback_promoted"
                if passed
                else "resident_weight_ranktree_fallback_blocked"
            ),
            "next_step": (
                "Implement or instantiate the radix-4 r64 rank-tree fallback in the resident-weight "
                "output-projection producer wrapper: one instance for r64 producer tiles and two "
                "banked instances for r128 producer tiles."
                if passed
                else "Resolve fallback coverage, RTL simulation, or physical metric gaps before promoting the resident-weight rank-tree fallback."
            ),
        },
        "assumptions": [
            "The fallback policy is for resident/cache-backed output-projection rows that outpace the replay-proven serial ranker thresholds.",
            "Single-r64 mode uses one measured r64/k1 rank-tree instance at II=1.",
            "Banked-r64 mode duplicates the measured r64/k1 rank-tree per 64-lane chunk so r128 producer tiles still drain at II=1.",
            "This promotion carries measured rank-tree PPA and RTL simulation status; it does not model FIFO/SRAM overhead because the selected current rows require no waiting buffer.",
        ],
    }


def write_markdown(path: Path, payload: JsonDict) -> None:
    metrics = payload.get("selected_metrics") or {}
    lines = [
        "# Decoder Resident Rank-Tree Fallback Promotion",
        "",
        f"- model: `{payload['model']}`",
        f"- decision: `{payload['decision']['decision']}`",
        f"- selected_radix: `{payload['target']['selected_radix']}`",
        f"- unsafe_rows: `{payload['coverage']['unsafe_rows']}`",
        f"- max_required_buffer_r64_tiles: `{payload['coverage']['max_required_buffer_r64_tiles']}`",
        f"- critical_path_ns: `{metrics.get('critical_path_ns')}`",
        f"- placed_cell_area_um2: `{metrics.get('placed_cell_area_um2')}`",
        f"- total_power_mw: `{metrics.get('total_power_mw')}`",
        f"- next_step: {payload['decision']['next_step']}",
        "",
        "## Producer Modes",
        "",
        "| mode | lanes | instances | II | rows | max buffer r64 | power mW | area um2 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in payload["producer_modes"]:
        lines.append(
            "| {mode} | {lanes} | {instances} | {ii} | {rows} | {buf} | {power} | {area} |".format(
                mode=row["mode"],
                lanes=",".join(str(x) for x in row["producer_lanes"]),
                instances=row["ranker_instances"],
                ii=row["consumer_ii_cycles"],
                rows=row["recommended_strategy_count"],
                buf=row["max_required_buffer_r64_tiles"],
                power=row.get("ranker_total_power_mw"),
                area=row.get("ranker_placed_cell_area_um2"),
            )
        )
    lines.extend(["", "## Checks", "", "| check | passed | observed |", "|---|---|---|"])
    for check in payload["checks"]:
        lines.append(f"| {check['name']} | `{check['passed']}` | `{check.get('observed')}` |")
    lines.extend(["", "## Assumptions", ""])
    for item in payload["assumptions"]:
        lines.append(f"- {item}")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fallback", required=True)
    ap.add_argument("--rank-tree", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--out-md", required=True)
    args = ap.parse_args()

    payload = build_report(fallback=_load_json(args.fallback), rank_tree=_load_json(args.rank_tree))
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
