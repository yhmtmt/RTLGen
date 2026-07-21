#!/usr/bin/env python3
"""Validate exact-state decode-score multivalue-cluster rows for binary-FSM PNR."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

EXPECTED_CLOCK_PERIOD = 8
EXPECTED_TAG_PREFIX = "decode_score_multivalue_cluster_v1_8ns_binary_fsm"
EXPECTED_FLOW_VARIANT = "decode_score_multivalue_cluster_v1_8ns_binary_fsm_v3_proxy_die_2500"
EXPECTED_DIE_AREA = "0 0 2500 2500"
EXPECTED_CORE_AREA = "50 50 2450 2450"
EXPECTED_PLACE_DENSITY = "0.4"
EXPECTED_SYNTH_HIERARCHICAL = "1"
EXPECTED_SYNTH_MEMORY_MAX_BITS = "65536"
EXPECTED_SYNTH_ARGS = "-nofsm"
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
            if row is not None:
                yield row


def _parse_critical_path(row: dict[str, str]) -> float:
    value = float(row.get("critical_path_ns", "inf"))
    return float(value)


def _row_matches_binary_fsm(row: dict[str, str]) -> bool:
    if _to_str(row.get("status")).lower() != "ok":
        return False

    try:
        params = _parse_params_json(_to_str(row.get("params_json", "")))
    except Exception:
        return False

    tag = _to_str(row.get("tag"))
    if not tag.startswith(EXPECTED_TAG_PREFIX):
        return False
    if _to_str(params.get("FLOW_VARIANT")) != EXPECTED_FLOW_VARIANT:
        return False
    if _to_str(params.get("PLACE_DENSITY")) != EXPECTED_PLACE_DENSITY:
        return False
    if _to_str(params.get("SYNTH_HIERARCHICAL")) != EXPECTED_SYNTH_HIERARCHICAL:
        return False
    if _to_str(params.get("SYNTH_MEMORY_MAX_BITS")) != EXPECTED_SYNTH_MEMORY_MAX_BITS:
        return False
    if _to_str(params.get("SYNTH_ARGS")) != EXPECTED_SYNTH_ARGS:
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
    if _to_str(row.get("result_path")).find(EXPECTED_RESULT_PATH_TOKEN) == -1:
        return False

    try:
        return _parse_critical_path(row) <= 8
    except Exception:
        return False


def validate_binary_fsm_metrics(*, metrics_path: Path) -> int:
    if not metrics_path.exists():
        raise ValueError(f"missing metrics.csv: {metrics_path}")

    for row in _iter_metrics_rows(metrics_path):
        if _row_matches_binary_fsm(row):
            return 0

    raise ValueError(
        "missing required 8ns exact-state binary-FSM decode-score multivalue-cluster row "
        "(status=ok, TAG=decode_score_multivalue_cluster_v1_8ns_binary_fsm*, "
        "FLOW_VARIANT=decode_score_multivalue_cluster_v1_8ns_binary_fsm_v3_proxy_die_2500, "
        "DIE_AREA=0 0 2500 2500, CORE_AREA=50 50 2450 2450, SYNTH_ARGS=-nofsm, "
        "PLACE_DENSITY=0.4, SYNTH_HIERARCHICAL=1, SYNTH_MEMORY_MAX_BITS=65536, "
        "critical_path_ns<=8)"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metrics-path", type=Path, required=True)
    args = parser.parse_args()
    validate_binary_fsm_metrics(metrics_path=args.metrics_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
