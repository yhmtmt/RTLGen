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


def _write_rows(index_path: Path, rows: list[dict[str, str]]) -> None:
    index_path.parent.mkdir(parents=True, exist_ok=True)
    with index_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=RUNS_INDEX_FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in RUNS_INDEX_FIELDNAMES})


def _rows_from_db(session: Session) -> list[dict[str, str]]:
    rows = (
        session.query(RunIndexRow)
        .order_by(RunIndexRow.index_order.asc(), RunIndexRow.created_at.asc())
        .all()
    )
    return [
        {field: str(getattr(row, field) or "") for field in RUNS_INDEX_FIELDNAMES}
        for row in rows
    ]


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

    rows = _load_rows(index_path)
    session.query(RunIndexRow).delete()
    for index_order, row in enumerate(rows):
        session.add(RunIndexRow(index_order=index_order, **row))
    session.flush()
    _write_rows(index_path, _rows_from_db(session))
    return RunIndexRefreshResult(
        row_count=len(rows),
        index_path=str(index_path),
    )
