"""Centralized runs/index.csv refresh and export."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
import subprocess

from sqlalchemy.orm import Session

from control_plane.models.run_index_rows import RunIndexRow

RUNS_INDEX_FIELDNAMES = [
    "circuit_type",
    "design",
    "platform",
    "status",
    "critical_path_ns",
    "die_area",
    "total_power_mw",
    "instance_area_um2",
    "stdcell_area_um2",
    "stdcell_count",
    "core_area_um2",
    "utilization_pct",
    "config_hash",
    "param_hash",
    "tag",
    "result_path",
    "params_json",
    "metrics_path",
    "design_path",
    "sram_area_um2",
    "sram_read_energy_pj",
    "sram_write_energy_pj",
    "sram_max_access_time_ns",
]


class RunIndexExportError(RuntimeError):
    pass


@dataclass(frozen=True)
class RunIndexRefreshResult:
    row_count: int
    index_path: str
    skipped: bool = False
    skip_reason: str | None = None


def _load_rows(index_path: Path) -> list[dict[str, str]]:
    if not index_path.exists():
        return []
    with index_path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows: list[dict[str, str]] = []
        for row in reader:
            rows.append({field: str(row.get(field, "") or "") for field in RUNS_INDEX_FIELDNAMES})
        return rows


def refresh_run_index(session: Session, *, repo_root: str) -> RunIndexRefreshResult:
    repo_path = Path(repo_root).resolve()
    script_path = repo_path / "scripts" / "build_runs_index.py"
    index_path = repo_path / "runs" / "index.csv"
    if not script_path.exists():
        return RunIndexRefreshResult(
            row_count=0,
            index_path=str(index_path),
            skipped=True,
            skip_reason="build_runs_index.py is not present in repo_root",
        )

    try:
        subprocess.run(
            ["python3", str(script_path)],
            cwd=str(repo_path),
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        stdout = (exc.stdout or "").strip()
        detail = stderr or stdout or f"exit status {exc.returncode}"
        raise RunIndexExportError(f"failed to rebuild runs/index.csv: {detail}") from exc

    # Keep the repository-generated CSV as the file of record. The running
    # control-plane daemon can lag the target repo schema, so rewriting this
    # file through RUNS_INDEX_FIELDNAMES would silently strip newer columns.
    rows = _load_rows(index_path)
    session.query(RunIndexRow).delete()
    for index_order, row in enumerate(rows):
        session.add(RunIndexRow(index_order=index_order, **row))
    session.flush()
    return RunIndexRefreshResult(
        row_count=len(rows),
        index_path=str(index_path),
    )
