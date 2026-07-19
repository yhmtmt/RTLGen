#!/usr/bin/env python3
"""Validate the 8 ns bridge sweep row for decode-score multivalue cluster."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

EXPECTED_CLOCK_PERIOD = 8
EXPECTED_FLOW_VARIANT = "decode_score_multivalue_cluster_v1_8ns_bridge"
EXPECTED_DIE_AREA = "0 0 2500 2500"
EXPECTED_CORE_AREA = "50 50 2450 2450"
EXPECTED_RESULT_PATH_TOKEN = "attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv"


def _parse_params_json(value: str) -> dict[str, object]:
    text = str(value or "").strip()
    if not text:
        raise ValueError("empty params_json")
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        if len(text) >= 2 and text[0] == '"' and text[-1] == '"':
            parsed = json.loads(text[1:-1].replace('""', '"'))
        else:
            raise
    if not isinstance(parsed, dict):
        raise ValueError("params_json did not decode to a JSON object")
    return parsed


def _to_str(value: object) -> str:
    return str(value or "").strip()


def _iter_metrics_rows(metrics_path: Path):
    with metrics_path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        for row in reader:
            if row is None:
                continue
            yield row


def _parse_critical_path(row: dict[str, str]) -> float:
    value = float(row.get("critical_path_ns", "inf"))
    return float(value)


def _row_matches_bridge(row: dict[str, str]) -> bool:
    if _to_str(row.get("status")).lower() != "ok":
        return False

    try:
        params = _parse_params_json(_to_str(row.get("params_json", "")))
    except Exception:
        return False

    if _to_str(params.get("FLOW_VARIANT")) != EXPECTED_FLOW_VARIANT:
        return False

    try:
        clock_period = float(_to_str(params.get("CLOCK_PERIOD", "")))
    except ValueError:
        return False
    if clock_period != float(EXPECTED_CLOCK_PERIOD):
        return False

    if _to_str(params.get("DIE_AREA")) != EXPECTED_DIE_AREA:
        return False
    if _to_str(params.get("CORE_AREA")) != EXPECTED_CORE_AREA:
        return False

    if EXPECTED_RESULT_PATH_TOKEN not in _to_str(row.get("result_path", "")):
        return False

    try:
        return _parse_critical_path(row) <= 8
    except Exception:
        return False


def validate_bridge_metrics(*, metrics_path: Path) -> int:
    if not metrics_path.exists():
        raise ValueError(f"missing metrics.csv: {metrics_path}")

    for row in _iter_metrics_rows(metrics_path):
        if _row_matches_bridge(row):
            return 0

    raise ValueError("missing required 8ns decode-score multivalue-cluster bridge row (status=ok, CLOCK_PERIOD=8, FLOW_VARIANT=decode_score_multivalue_cluster_v1_8ns_bridge, DIE_AREA=0 0 2500 2500, CORE_AREA=50 50 2450 2450, critical_path_ns<=8)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metrics-path", type=Path, required=True)
    args = parser.parse_args()
    validate_bridge_metrics(metrics_path=args.metrics_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
