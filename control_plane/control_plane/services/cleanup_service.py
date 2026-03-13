"""Operator cleanup and retention helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from datetime import timedelta
from pathlib import Path
import shutil

from sqlalchemy.orm import Session

from control_plane.clock import utcnow
from control_plane.models.artifacts import Artifact
from control_plane.models.enums import ArtifactStorageMode, LeaseStatus
from control_plane.models.worker_leases import WorkerLease


@dataclass(frozen=True)
class CleanupRequest:
    repo_root: str
    runtime_dir: str | None = None
    log_root: str | None = None
    max_age_days: int = 7
    prune_runtime_files: bool = True
    prune_worker_logs: bool = True
    prune_db_leases: bool = True
    prune_db_transient_artifacts: bool = True
    dry_run: bool = True


@dataclass(frozen=True)
class CleanupResult:
    dry_run: bool
    runtime_paths: list[str]
    log_paths: list[str]
    db_expired_leases: int
    db_released_leases: int
    db_transient_artifacts: int


def _remove_path(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path, ignore_errors=True)
    else:
        try:
            path.unlink()
        except FileNotFoundError:
            pass


def _list_runtime_paths(runtime_dir: Path) -> list[Path]:
    if not runtime_dir.exists():
        return []
    names = {
        "worker.pid",
        "worker.log",
        "completions.pid",
        "completions.log",
    }
    return sorted(path for path in runtime_dir.iterdir() if path.name in names)


def _list_log_paths(log_root: Path, *, cutoff) -> list[Path]:
    if not log_root.exists():
        return []
    selected: list[Path] = []
    for path in sorted(log_root.rglob("*")):
        if not path.is_file():
            continue
        modified = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        if modified <= cutoff:
            selected.append(path)
    return selected


def run_cleanup(session: Session, request: CleanupRequest) -> CleanupResult:
    repo_root = Path(request.repo_root).resolve()
    runtime_dir = Path(request.runtime_dir or "/tmp/rtlgen-control-plane").resolve()
    log_root = Path(request.log_root or (repo_root / "control_plane" / "logs")).resolve()
    cutoff = utcnow() - timedelta(days=request.max_age_days)

    runtime_paths = _list_runtime_paths(runtime_dir) if request.prune_runtime_files else []
    log_paths = _list_log_paths(log_root, cutoff=cutoff) if request.prune_worker_logs else []

    expired_leases = []
    released_leases = []
    if request.prune_db_leases:
        expired_leases = (
            session.query(WorkerLease)
            .filter(WorkerLease.status == LeaseStatus.EXPIRED)
            .filter(WorkerLease.expires_at < cutoff)
            .all()
        )
        released_leases = (
            session.query(WorkerLease)
            .filter(WorkerLease.status == LeaseStatus.RELEASED)
            .filter(WorkerLease.expires_at < cutoff)
            .all()
        )

    transient_artifacts = []
    if request.prune_db_transient_artifacts:
        transient_artifacts = (
            session.query(Artifact)
            .filter(Artifact.storage_mode == ArtifactStorageMode.TRANSIENT)
            .filter(Artifact.created_at < cutoff)
            .all()
        )

    if not request.dry_run:
        for path in runtime_paths:
            _remove_path(path)
        for path in log_paths:
            _remove_path(path)
        for row in transient_artifacts:
            session.delete(row)
        for row in expired_leases:
            session.delete(row)
        for row in released_leases:
            session.delete(row)
        session.commit()

    return CleanupResult(
        dry_run=request.dry_run,
        runtime_paths=[str(path) for path in runtime_paths],
        log_paths=[str(path) for path in log_paths],
        db_expired_leases=len(expired_leases),
        db_released_leases=len(released_leases),
        db_transient_artifacts=len(transient_artifacts),
    )
