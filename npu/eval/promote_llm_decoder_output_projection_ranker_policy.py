#!/usr/bin/env python3
"""Promote output-projection ranker selection policy across streaming and resident weights."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


JsonDict = dict[str, Any]
R64_LANES = 64


def _load_json(path: str | Path) -> JsonDict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _serial_lpc1_threshold(cadence: JsonDict, serial_wrapper: JsonDict) -> int | None:
    thresholds = cadence.get("ranker_zero_backpressure_thresholds")
    if isinstance(thresholds, dict) and isinstance(thresholds.get("serial_lpc1"), dict):
        value = thresholds["serial_lpc1"].get("min_zero_backpressure_ii_cycles")
        if value is not None:
            return int(value)
    target = serial_wrapper.get("target") if isinstance(serial_wrapper.get("target"), dict) else {}
    value = target.get("producer_ii_cycles")
    return None if value is None else int(value)


def _ranktree_mode_for_lanes(lanes: int) -> str:
    return "single_r64_ranktree" if lanes <= R64_LANES else "banked_r64_ranktrees"


def _ranktree_modes(ranktree_promotion: JsonDict) -> dict[str, JsonDict]:
    modes: dict[str, JsonDict] = {}
    for row in ranktree_promotion.get("producer_modes", []):
        if isinstance(row, dict) and row.get("mode"):
            modes[str(row["mode"])] = row
    return modes


def _policy_row(
    row: JsonDict,
    *,
    serial_threshold: int,
    ranktree_modes: dict[str, JsonDict],
) -> JsonDict:
    producer_lanes = int(row["producer_lanes"])
    producer_ii = int(row["producer_ii_cycles"])
    base = {
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
    }
    if producer_ii >= serial_threshold:
        return {
            "producer": base,
            "selected_path": "serial_lpc1",
            "selection_reason": "producer_ii_meets_serial_lpc1_zero_backpressure_threshold",
            "consumer_ii_cycles": serial_threshold,
            "ranker_instances": 1,
            "coverage_status": "covered",
        }
    mode = _ranktree_mode_for_lanes(producer_lanes)
    promoted = ranktree_modes.get(mode)
    return {
        "producer": base,
        "selected_path": mode,
        "selection_reason": "producer_ii_is_faster_than_serial_lpc1_threshold",
        "consumer_ii_cycles": None if promoted is None else promoted.get("consumer_ii_cycles"),
        "ranker_instances": None if promoted is None else promoted.get("ranker_instances"),
        "ranktree_radix": None if promoted is None else promoted.get("ranktree_radix"),
        "coverage_status": "covered" if promoted is not None else "uncovered_ranktree_mode",
    }


def build_report(
    *,
    serial_wrapper: JsonDict,
    cadence_sensitivity: JsonDict,
    ranktree_promotion: JsonDict,
) -> JsonDict:
    serial_threshold = _serial_lpc1_threshold(cadence_sensitivity, serial_wrapper)
    ranktree_modes = _ranktree_modes(ranktree_promotion)
    rows: list[JsonDict] = []
    if serial_threshold is not None:
        for row in cadence_sensitivity.get("cadence_sweep", []):
            if isinstance(row, dict):
                rows.append(_policy_row(row, serial_threshold=serial_threshold, ranktree_modes=ranktree_modes))
    path_counts = Counter(row["selected_path"] for row in rows)
    uncovered = [row for row in rows if row["coverage_status"] != "covered"]
    serial_decision = (
        serial_wrapper.get("decision", {}).get("decision")
        if isinstance(serial_wrapper.get("decision"), dict)
        else None
    )
    ranktree_decision = (
        ranktree_promotion.get("decision", {}).get("decision")
        if isinstance(ranktree_promotion.get("decision"), dict)
        else None
    )
    checks = [
        {
            "name": "serial_lpc1_wrapper_promoted",
            "passed": serial_decision == "serial_lpc1_producer_coupled_wrapper_promoted",
            "observed": serial_decision,
        },
        {
            "name": "resident_ranktree_fallback_promoted",
            "passed": ranktree_decision == "resident_weight_ranktree_fallback_promoted",
            "observed": ranktree_decision,
        },
        {
            "name": "serial_lpc1_threshold_available",
            "passed": serial_threshold is not None,
            "observed": serial_threshold,
        },
        {
            "name": "all_cadence_rows_covered",
            "passed": bool(rows) and not uncovered,
            "observed": {"total_rows": len(rows), "uncovered_rows": len(uncovered)},
        },
        {
            "name": "ranktree_has_single_and_banked_modes",
            "passed": {"single_r64_ranktree", "banked_r64_ranktrees"}.issubset(ranktree_modes),
            "observed": sorted(ranktree_modes),
        },
    ]
    passed = all(bool(check["passed"]) for check in checks)
    return {
        "version": 0.1,
        "model": "decoder_output_projection_ranker_policy_v1",
        "policy": {
            "serial_lpc1_min_ii_cycles": serial_threshold,
            "rule": (
                "Use serial_lpc1 when producer_ii_cycles is at least the replay-proven "
                "serial_lpc1 zero-backpressure threshold; otherwise use the promoted radix-4 "
                "rank-tree fallback mode selected by producer_lanes."
            ),
            "ranktree_mode_by_lanes": {
                "producer_lanes <= 64": "single_r64_ranktree",
                "producer_lanes > 64": "banked_r64_ranktrees",
            },
        },
        "path_summary": {
            "total_rows": len(rows),
            "path_counts": dict(path_counts),
            "uncovered_rows": len(uncovered),
            "serial_lpc1_rows": path_counts.get("serial_lpc1", 0),
            "ranktree_rows": sum(count for path, count in path_counts.items() if path != "serial_lpc1"),
        },
        "selected_artifacts": {
            "serial_lpc1": {
                "decision": serial_decision,
                "metrics": serial_wrapper.get("selected_metrics"),
                "target": serial_wrapper.get("target"),
            },
            "ranktree_fallback": {
                "decision": ranktree_decision,
                "metrics": ranktree_promotion.get("selected_metrics"),
                "producer_modes": ranktree_promotion.get("producer_modes"),
            },
        },
        "policy_rows": rows,
        "uncovered_rows": uncovered,
        "checks": checks,
        "decision": {
            "decision": (
                "output_projection_ranker_policy_promoted"
                if passed
                else "output_projection_ranker_policy_blocked"
            ),
            "next_step": (
                "Implement the output-projection producer wrapper policy with a serial_lpc1 path for "
                "streaming/slow producer cadences and a radix-4 rank-tree fallback path for faster "
                "resident/cache-backed cadences."
                if passed
                else "Resolve missing serial or rank-tree promotion coverage before implementing the output-projection producer wrapper policy."
            ),
        },
        "assumptions": [
            "The policy is conservative: lpc2/lpc4 rows that were analytically safe are routed to the promoted rank-tree unless lpc1 is also safe.",
            "The rank-tree fallback uses one r64 rank-tree for producer_lanes <= 64 and banked r64 rank-trees for wider producer tiles.",
            "The selection boundary is replay-observed ready-valid backpressure, not only analytical ranker service cycles.",
            "Future measured producer burst traces may add hysteresis or buffering around this fixed-II policy boundary.",
        ],
    }


def write_markdown(path: Path, payload: JsonDict) -> None:
    lines = [
        "# Decoder Output-Projection Ranker Policy",
        "",
        f"- model: `{payload['model']}`",
        f"- decision: `{payload['decision']['decision']}`",
        f"- serial_lpc1_min_ii_cycles: `{payload['policy']['serial_lpc1_min_ii_cycles']}`",
        f"- total_rows: `{payload['path_summary']['total_rows']}`",
        f"- serial_lpc1_rows: `{payload['path_summary']['serial_lpc1_rows']}`",
        f"- ranktree_rows: `{payload['path_summary']['ranktree_rows']}`",
        f"- uncovered_rows: `{payload['path_summary']['uncovered_rows']}`",
        f"- next_step: {payload['decision']['next_step']}",
        "",
        "## Path Counts",
        "",
        "| path | rows |",
        "|---|---:|",
    ]
    for path_name, count in sorted(payload["path_summary"]["path_counts"].items()):
        lines.append(f"| {path_name} | {count} |")
    lines.extend(["", "## Checks", "", "| check | passed | observed |", "|---|---|---|"])
    for check in payload["checks"]:
        lines.append(f"| {check['name']} | `{check['passed']}` | `{check.get('observed')}` |")
    lines.extend(["", "## Assumptions", ""])
    for item in payload["assumptions"]:
        lines.append(f"- {item}")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--serial-wrapper", required=True)
    ap.add_argument("--cadence-sensitivity", required=True)
    ap.add_argument("--ranktree-promotion", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--out-md", required=True)
    args = ap.parse_args()

    payload = build_report(
        serial_wrapper=_load_json(args.serial_wrapper),
        cadence_sensitivity=_load_json(args.cadence_sensitivity),
        ranktree_promotion=_load_json(args.ranktree_promotion),
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
