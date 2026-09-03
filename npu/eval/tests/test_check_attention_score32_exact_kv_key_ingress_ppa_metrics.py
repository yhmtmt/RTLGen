from __future__ import annotations

import csv
from pathlib import Path

import pytest

from npu.eval.check_attention_score32_exact_kv_key_ingress_ppa_metrics import check


FIELDS = (
    "param_hash",
    "status",
    "critical_path_ns",
    "stdcell_area_um2",
    "total_power_mw",
)


def _write(path: Path, *, blank_area_row: int | None = None) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for index in range(6):
            writer.writerow(
                {
                    "param_hash": f"hash{index}",
                    "status": "ok",
                    "critical_path_ns": "2.5",
                    "stdcell_area_um2": "" if index == blank_area_row else "1234.5",
                    "total_power_mw": "0.75",
                }
            )


def test_checker_accepts_six_complete_rows(tmp_path: Path) -> None:
    metrics = tmp_path / "metrics.csv"
    _write(metrics)
    check(metrics, required_rows=6)


def test_checker_rejects_blank_standard_cell_area(tmp_path: Path) -> None:
    metrics = tmp_path / "metrics.csv"
    _write(metrics, blank_area_row=2)
    with pytest.raises(SystemExit, match="stdcell_area_um2"):
        check(metrics, required_rows=6)


def test_checker_rejects_incomplete_sweep(tmp_path: Path) -> None:
    metrics = tmp_path / "metrics.csv"
    _write(metrics)
    rows = metrics.read_text(encoding="utf-8").splitlines()
    metrics.write_text("\n".join(rows[:-1]) + "\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="expected exactly 6"):
        check(metrics, required_rows=6)
