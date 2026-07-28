#!/usr/bin/env python3
"""Pure-Python helpers for the cluster-SRAM-composed full GQA8 hierarchy."""

from __future__ import annotations

import hashlib
import json
from typing import Any

JsonDict = dict[str, Any]
_HEAD_BASES = (0, 8, 16, 24)
_WAVES = 8


def _hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def compare_full_rows(
    expected_rows: list[dict[str, object]],
    observed_rows: list[dict[str, object]],
) -> JsonDict:
    """Compare every structured field; hashes remain summary-only diagnostics."""
    result: JsonDict = {
        "passed": expected_rows == observed_rows,
        "expected_row_count": len(expected_rows),
        "observed_row_count": len(observed_rows),
        "expected_hash": _hash(expected_rows),
        "observed_hash": _hash(observed_rows),
        "first_mismatch": None,
    }
    shared_rows = min(len(expected_rows), len(observed_rows))
    for index in range(shared_rows):
        expected = expected_rows[index]
        observed = observed_rows[index]
        if expected == observed:
            continue
        for field in sorted(set(expected) | set(observed)):
            if expected.get(field) != observed.get(field):
                result["first_mismatch"] = {
                    "row": index,
                    "field": field,
                    "expected": expected.get(field),
                    "observed": observed.get(field),
                }
                return result
    if len(expected_rows) != len(observed_rows):
        result["first_mismatch"] = {
            "row": shared_rows,
            "field": "__row_count__",
            "expected": len(expected_rows),
            "observed": len(observed_rows),
        }
    return result


def compare_compositional_rows(
    *,
    expected_cluster_rows: list[list[dict[str, object]]],
    observed_cluster_rows: list[list[dict[str, object]]],
    expected_root_rows: list[dict[str, object]],
    observed_root_rows: list[dict[str, object]],
) -> JsonDict:
    if len(expected_cluster_rows) != 16 or len(observed_cluster_rows) != 16:
        raise ValueError("compositional audit requires exactly 16 cluster row streams")
    clusters = [
        compare_full_rows(expected_cluster_rows[index], observed_cluster_rows[index])
        for index in range(16)
    ]
    root = compare_full_rows(expected_root_rows, observed_root_rows)
    return {
        "passed": all(bool(result["passed"]) for result in clusters) and bool(root["passed"]),
        "clusters": clusters,
        "root": root,
    }


def expected_schedule_prefix(*, command_count: int) -> tuple[tuple[int, int], ...]:
    resolved = int(command_count)
    if resolved < 0:
        raise ValueError("command_count must be non-negative")
    schedule: list[tuple[int, int]] = []
    for index in range(resolved):
        schedule.append((_HEAD_BASES[(index // _WAVES) % len(_HEAD_BASES)], index % _WAVES))
    return tuple(schedule)


__all__ = [
    "compare_compositional_rows",
    "compare_full_rows",
    "expected_schedule_prefix",
]
