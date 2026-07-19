#!/usr/bin/env python3
"""Validate macro-placement mode-comparison evidence for folded GQA8 lane2."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


EXPECTED_CLOCK_PERIOD = 10
EXPECTED_DIE_AREA = "0 0 3550 3550"
EXPECTED_CORE_AREA = "50 50 3500 3500"
EXPECTED_DESIGN = "attention_decode_score_multivalue_gqa_group_lanes2_int8_m1x8_iterdiv"
EXPECTED_RESULT_PATH_TOKEN = EXPECTED_DESIGN
EXPECTED_PLACE_DENSITY = 0.4
EXPECTED_SYNTH_MEMORY_MAX_BITS = 65536
EXPECTED_FLOW_VARIANT_PREFIX = "decode_score_multivalue_gqa_lanes2_macro_hier_placement_compare_3550_v1"

EXPECTED_MODES = [
    {
        "name": "flattened_wrapper",
        "hierarchical": 0,
        "flow_variant": f"{EXPECTED_FLOW_VARIANT_PREFIX}_flattened_wrapper",
    },
    {
        "name": "hierarchical_macro",
        "hierarchical": 1,
        "flow_variant": f"{EXPECTED_FLOW_VARIANT_PREFIX}_hierarchical_macro",
    },
]

VALID_STATUSES = {"ok", "flow_failed"}


def _to_str(value: object) -> str:
    return str(value or "").strip()


def _parse_bool(value: object) -> bool | None:
    if isinstance(value, bool):
        return value
    token = _to_str(value).lower()
    if token in {"1", "true", "yes", "on"}:
        return True
    if token in {"0", "false", "no", "off"}:
        return False
    return None


def _parse_int(value: object) -> int:
    if isinstance(value, bool):
        raise ValueError("expected integer value")
    if isinstance(value, int):
        return value
    try:
        parsed = float(value) if isinstance(value, float) else float(_to_str(value))
    except (TypeError, ValueError):
        raise ValueError("expected integer value")
    if not parsed.is_integer():
        raise ValueError("expected integer value")
    return int(parsed)


def _parse_params_json(value: str) -> dict[str, object]:
    text = str(value or "").strip()
    if not text:
        raise ValueError("empty params_json")
    parsed = json.loads(text)
    if not isinstance(parsed, dict):
        raise ValueError("params_json did not decode to an object")
    return parsed


def _iter_metrics_rows(metrics_path: Path):
    with metrics_path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        for row in reader:
            if row is not None:
                yield row


def _row_matches_mode(
    row: dict[str, str],
    *,
    mode_name: str,
    hierarchical: int,
    flow_variant: str,
) -> bool:
    if _to_str(row.get("mode_name")) != mode_name:
        return False
    if _to_str(row.get("status")).lower() not in VALID_STATUSES:
        return False

    if _to_str(row.get("design")) != EXPECTED_DESIGN:
        return False
    if _to_str(row.get("result_path")).find(EXPECTED_RESULT_PATH_TOKEN) == -1:
        return False

    mode_use_macro = _parse_bool(row.get("mode_use_macro"))
    if mode_use_macro is not True:
        return False

    try:
        params = _parse_params_json(_to_str(row.get("params_json", "")))
    except Exception:
        return False

    try:
        clock_period = float(_to_str(params.get("CLOCK_PERIOD")))
    except (TypeError, ValueError):
        return False
    if clock_period != float(EXPECTED_CLOCK_PERIOD):
        return False

    try:
        if _parse_int(params.get("SYNTH_HIERARCHICAL")) != hierarchical:
            return False
        if _parse_int(params.get("SYNTH_MEMORY_MAX_BITS")) != EXPECTED_SYNTH_MEMORY_MAX_BITS:
            return False
        if float(_to_str(params.get("PLACE_DENSITY"))) != EXPECTED_PLACE_DENSITY:
            return False
    except Exception:
        return False

    return (
        _to_str(params.get("FLOW_VARIANT")) == flow_variant
        and _to_str(params.get("DIE_AREA")) == EXPECTED_DIE_AREA
        and _to_str(params.get("CORE_AREA")) == EXPECTED_CORE_AREA
    )


def _collect_mode_rows(
    rows: list[dict[str, str]],
) -> dict[str, list[dict[str, str]]]:
    by_mode: dict[str, list[dict[str, str]]] = {
        mode["name"]: [] for mode in EXPECTED_MODES
    }
    for row in rows:
        for mode in EXPECTED_MODES:
            if _row_matches_mode(
                row,
                mode_name=mode["name"],
                hierarchical=mode["hierarchical"],
                flow_variant=mode["flow_variant"],
            ):
                by_mode[mode["name"]].append(row)
    return by_mode


def _summary_rows(by_mode: dict[str, list[dict[str, str]]]) -> dict[str, object]:
    summaries: list[dict[str, object]] = []
    failures: list[str] = []
    for mode in EXPECTED_MODES:
        name = mode["name"]
        matches = by_mode.get(name, [])
        if not matches:
            failures.append(f"missing required mode: {name}")
            continue

        # Keep the first matching row as the representative, while still reporting all
        # statuses to preserve explicit feasibility/boundary evidence.
        row = matches[0]
        summaries.append(
            {
                "mode": name,
                "status": _to_str(row.get("status")),
                "critical_path_ns": row.get("critical_path_ns") if row.get("critical_path_ns") else None,
                "failure_stage": row.get("failure_stage") if row.get("failure_stage") else None,
                "failure_signature": row.get("failure_signature") if row.get("failure_signature") else None,
                "mode_use_macro": _to_str(row.get("mode_use_macro")),
                "result_path": _to_str(row.get("result_path")),
                "tag": _to_str(row.get("tag")),
            }
        )

    return {
        "status": "ok" if not failures else "invalid",
        "status_mode_rows": summaries,
        "failures": failures,
    }


def validate_mode_compare(*, metrics_path: Path, out_path: Path | None) -> int:
    if not metrics_path.exists():
        raise ValueError(f"missing metrics.csv: {metrics_path}")

    rows = list(_iter_metrics_rows(metrics_path))
    by_mode = _collect_mode_rows(rows)
    summary = _summary_rows(by_mode)

    for mode in EXPECTED_MODES:
        if mode["name"] in [x.get("mode") for x in summary["status_mode_rows"]]:
            continue
        summary["status"] = "invalid"
        missing_msg = f"missing required mode: {mode['name']}"
        if missing_msg not in summary["failures"]:
            summary["failures"].append(missing_msg)

    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if summary["status"] != "ok":
        raise ValueError("required mode-comparison evidence missing or malformed: " + "; ".join(summary["failures"]))

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metrics-path", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    return validate_mode_compare(metrics_path=args.metrics_path, out_path=args.out)


if __name__ == "__main__":
    raise SystemExit(main())
