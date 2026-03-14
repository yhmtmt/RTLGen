"""Tests for control-plane cleanup and retention helpers."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path
import os
import tempfile

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from control_plane.clock import utcnow
from control_plane.db import build_session_factory, create_all
from control_plane.models.artifacts import Artifact
from control_plane.models.enums import (
    ArtifactStorageMode,
    ExecutorType,
    FlowName,
    LayerName,
    LeaseStatus,
    RunStatus,
    WorkItemState,
)
from control_plane.models.runs import Run
from control_plane.models.task_requests import TaskRequest
from control_plane.models.worker_leases import WorkerLease
from control_plane.models.worker_machines import WorkerMachine
from control_plane.models.work_items import WorkItem
from control_plane.services.cleanup_service import CleanupRequest, run_cleanup


def _seed_item(session: Session, *, item_id: str) -> WorkItem:
    task = TaskRequest(
        request_key=f"queue:{item_id}",
        source="test",
        requested_by="tester",
        title=item_id,
        description="cleanup test",
        layer=LayerName.LAYER1,
        flow=FlowName.OPENROAD,
        priority=1,
        request_payload={"item_id": item_id},
    )
    session.add(task)
    session.flush()
    work_item = WorkItem(
        work_item_key=f"queue:{item_id}",
        task_request_id=task.id,
        item_id=item_id,
        layer=LayerName.LAYER1,
        flow=FlowName.OPENROAD,
        platform="nangate45",
        task_type="l1_sweep",
        state=WorkItemState.READY,
        priority=1,
        input_manifest={},
        command_manifest=[],
        expected_outputs=[],
        acceptance_rules=[],
    )
    session.add(work_item)
    session.flush()
    return work_item


def test_cleanup_reports_and_prunes_targets() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        runtime_dir = Path(td) / "runtime"
        runtime_dir.mkdir()
        log_root = repo_root / "control_plane" / "logs"
        log_root.mkdir(parents=True)

        runtime_log = runtime_dir / "worker.log"
        runtime_log.write_text("worker\n", encoding="utf-8")
        worker_log = log_root / "old" / "stderr.log"
        worker_log.parent.mkdir(parents=True)
        worker_log.write_text("stderr\n", encoding="utf-8")

        old_ts = (utcnow() - timedelta(days=10)).timestamp()
        os.utime(runtime_log, (old_ts, old_ts))
        os.utime(worker_log, (old_ts, old_ts))

        db_path = Path(td) / "cp.db"
        engine = create_engine(f"sqlite+pysqlite:///{db_path}", future=True)
        create_all(engine)
        now = utcnow()
        with Session(engine) as session:
            work_item = _seed_item(session, item_id="cleanup_item")
            machine = WorkerMachine(
                machine_key="worker-1",
                hostname="host-1",
                executor_kind="local_process",
                capabilities={},
                last_seen_at=now,
            )
            session.add(machine)
            session.flush()
            lease = WorkerLease(
                work_item_id=work_item.id,
                machine_id=machine.id,
                lease_token="lease-old",
                status=LeaseStatus.EXPIRED,
                leased_at=now - timedelta(days=15),
                expires_at=now - timedelta(days=10),
                last_heartbeat_at=now - timedelta(days=10),
            )
            session.add(lease)
            session.flush()
            run = Run(
                run_key="cleanup_run",
                work_item_id=work_item.id,
                lease_id=lease.id,
                attempt=1,
                executor_type=ExecutorType.INTERNAL_WORKER,
                machine_id=machine.id,
                checkout_commit="deadbeef",
                status=RunStatus.FAILED,
                started_at=now - timedelta(days=12),
                completed_at=now - timedelta(days=10),
                result_summary="cleanup run",
                result_payload={},
            )
            session.add(run)
            session.flush()
            session.add(
                Artifact(
                    run_id=run.id,
                    kind="stderr_log",
                    storage_mode=ArtifactStorageMode.TRANSIENT,
                    path="control_plane/logs/cleanup_item/stderr.log",
                    sha256="deadbeef",
                    metadata_={},
                )
            )
            session.commit()

        session_factory = build_session_factory(engine)
        with session_factory() as session:
            dry_run = run_cleanup(
                session,
                CleanupRequest(
                    repo_root=str(repo_root),
                    runtime_dir=str(runtime_dir),
                    log_root=str(log_root),
                    max_age_days=7,
                    dry_run=True,
                ),
            )

        assert dry_run.dry_run is True
        assert str(runtime_log) in dry_run.runtime_paths
        assert str(worker_log) in dry_run.log_paths
        assert dry_run.db_expired_leases == 1
        assert dry_run.db_released_leases == 0
        assert dry_run.db_transient_artifacts == 1
        assert runtime_log.exists()
        assert worker_log.exists()

        with session_factory() as session:
            applied = run_cleanup(
                session,
                CleanupRequest(
                    repo_root=str(repo_root),
                    runtime_dir=str(runtime_dir),
                    log_root=str(log_root),
                    max_age_days=7,
                    dry_run=False,
                ),
            )

        assert applied.dry_run is False
        assert not runtime_log.exists()
        assert not worker_log.exists()
        with Session(engine) as session:
            assert session.query(WorkerLease).count() == 0
            assert session.query(Artifact).count() == 0


def test_cleanup_uses_independent_retention_windows() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        runtime_dir = Path(td) / "runtime"
        runtime_dir.mkdir()
        log_root = repo_root / "control_plane" / "logs"
        log_root.mkdir(parents=True)

        runtime_log = runtime_dir / "worker.log"
        runtime_log.write_text("worker\n", encoding="utf-8")
        worker_log = log_root / "old" / "stderr.log"
        worker_log.parent.mkdir(parents=True)
        worker_log.write_text("stderr\n", encoding="utf-8")

        old_ts = (utcnow() - timedelta(days=10)).timestamp()
        os.utime(runtime_log, (old_ts, old_ts))
        os.utime(worker_log, (old_ts, old_ts))

        db_path = Path(td) / "cp.db"
        engine = create_engine(f"sqlite+pysqlite:///{db_path}", future=True)
        create_all(engine)
        now = utcnow()
        with Session(engine) as session:
            work_item = _seed_item(session, item_id="cleanup_item_windowed")
            machine = WorkerMachine(
                machine_key="worker-1",
                hostname="host-1",
                executor_kind="local_process",
                capabilities={},
                last_seen_at=now,
            )
            session.add(machine)
            session.flush()
            lease = WorkerLease(
                work_item_id=work_item.id,
                machine_id=machine.id,
                lease_token="lease-old-windowed",
                status=LeaseStatus.EXPIRED,
                leased_at=now - timedelta(days=15),
                expires_at=now - timedelta(days=10),
                last_heartbeat_at=now - timedelta(days=10),
            )
            session.add(lease)
            session.flush()
            run = Run(
                run_key="cleanup_run_windowed",
                work_item_id=work_item.id,
                lease_id=lease.id,
                attempt=1,
                executor_type=ExecutorType.INTERNAL_WORKER,
                machine_id=machine.id,
                checkout_commit="deadbeef",
                status=RunStatus.FAILED,
                started_at=now - timedelta(days=12),
                completed_at=now - timedelta(days=10),
                result_summary="cleanup run",
                result_payload={},
            )
            session.add(run)
            session.flush()
            session.add(
                Artifact(
                    run_id=run.id,
                    kind="stderr_log",
                    storage_mode=ArtifactStorageMode.TRANSIENT,
                    path="control_plane/logs/cleanup_item_windowed/stderr.log",
                    sha256="deadbeef",
                    metadata_={},
                )
            )
            session.commit()

        session_factory = build_session_factory(engine)
        with session_factory() as session:
            dry_run = run_cleanup(
                session,
                CleanupRequest(
                    repo_root=str(repo_root),
                    runtime_dir=str(runtime_dir),
                    log_root=str(log_root),
                    max_age_days=7,
                    runtime_max_age_days=30,
                    log_max_age_days=5,
                    db_max_age_days=30,
                    dry_run=True,
                ),
            )

        assert str(runtime_log) not in dry_run.runtime_paths
        assert str(worker_log) in dry_run.log_paths
        assert dry_run.db_expired_leases == 0
        assert dry_run.db_transient_artifacts == 0
