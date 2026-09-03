#!/usr/bin/env python3
"""Require complete finite PPA rows for an exact K-ingress sweep."""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path
from typing import Sequence


REQUIRED_METRICS = ("critical_path_ns", "stdcell_area_um2", "total_power_mw")


def _positive_finite(row: dict[str, str], key: str) -> bool:
    try:
        value = float(row.get(key, ""))
    except (TypeError, ValueError):
        return False
    return math.isfinite(value) and value > 0.0


def check(metrics_path: Path, *, required_rows: int) -> None:
    if required_rows <= 0:
        raise SystemExit("required_rows must be positive")
    with metrics_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != required_rows:
        raise SystemExit(
            f"expected exactly {required_rows} PPA rows in {metrics_path}, found {len(rows)}"
        )

    param_hashes: set[str] = set()
    failures: list[str] = []
    for index, row in enumerate(rows, start=2):
        param_hash = str(row.get("param_hash") or "").strip()
        if not param_hash:
            failures.append(f"row {index}: missing param_hash")
        elif param_hash in param_hashes:
            failures.append(f"row {index}: duplicate param_hash {param_hash}")
        param_hashes.add(param_hash)
        if str(row.get("status") or "").strip() != "ok":
            failures.append(f"row {index}: status is not ok")
        for key in REQUIRED_METRICS:
            if not _positive_finite(row, key):
                failures.append(f"row {index}: {key} is not finite and positive")
    if failures:
        raise SystemExit("incomplete exact K-ingress PPA metrics: " + "; ".join(failures))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metrics", type=Path, required=True)
    parser.add_argument("--required-rows", type=int, default=6)
    args = parser.parse_args(argv)
    check(args.metrics, required_rows=args.required_rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
