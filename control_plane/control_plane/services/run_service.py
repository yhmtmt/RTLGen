"""Run lifecycle service for cp-004."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from control_plane.clock import utcnow
from control_plane.models.artifacts import Artifact
from control_plane.models.enums import ArtifactStorageMode, ExecutorType, LeaseStatus, RunStatus, WorkItemState
from control_plane.models.run_events import RunEvent
from control_plane.models.runs import Run
from control_plane.models.worker_leases import WorkerLease

_TERMINAL_RUN_STATUSES = {
    RunStatus.SUCCEEDED,
    RunStatus.FAILED,
    RunStatus.CANCELED,
    RunStatus.TIMED_OUT,
}


class RunLifecycleError(RuntimeError):
    pass


class RunConflict(RunLifecycleError):
    pass


class RunNotFound(RunLifecycleError):
    pass


class LeaseNotFound(RunLifecycleError):
    pass


@dataclass(frozen=True)
class RunStartResult:
    run_id: str
    run_key: str
    work_item_id: str
    lease_id: str
    status: str


@dataclass(frozen=True)
class RunEventResult:
    run_id: str
    run_key: str
    event_id: int
    event_type: str


@dataclass(frozen=True)
class RunCompleteResult:
    run_id: str
    run_key: str
    work_item_id: str
    status: str
    artifact_count: int


def _get_active_lease(session: Session, lease_token: str) -> WorkerLease:
    lease = (
        session.query(WorkerLease)
        .filter(WorkerLease.lease_token == lease_token)
        .one_or_none()
    )
    if lease is None:
        raise LeaseNotFound(f"lease not found: {lease_token}")
    if lease.status != LeaseStatus.ACTIVE:
        raise RunLifecycleError(f"lease is not active: {lease_token}")
    return lease


def start_run(
    session: Session,
    *,
    lease_token: str,
    run_key: str,
    attempt: int,
    executor_type: str,
    container_image: str | None = None,
    checkout_commit: str | None = None,
    branch_name: str | None = None,
) -> RunStartResult:
    lease = _get_active_lease(session, lease_token)
    work_item = lease.work_item
    if work_item.state not in {WorkItemState.LEASED, WorkItemState.READY}:
        raise RunLifecycleError(
            f"work item {work_item.item_id} is not ready to start a run from state={work_item.state.value}"
        )

    existing = session.query(Run).filter(Run.run_key == run_key).one_or_none()
    if existing is not None:
        raise RunConflict(f"run_key already exists: {run_key}")

    run = Run(
        run_key=run_key,
        work_item_id=work_item.id,
        lease_id=lease.id,
        attempt=attempt,
        executor_type=ExecutorType(executor_type),
        machine_id=lease.machine_id,
        container_image=container_image,
        checkout_commit=checkout_commit,
        branch_name=branch_name,
        status=RunStatus.RUNNING,
        started_at=utcnow(),
    )
    session.add(run)
    work_item.state = WorkItemState.RUNNING
    session.flush()

    event = RunEvent(
        run_id=run.id,
        event_time=utcnow(),
        event_type="run_started",
        event_payload={
            "lease_token": lease_token,
            "attempt": attempt,
            "executor_type": executor_type,
        },
    )
    session.add(event)

    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise RunConflict(f"failed to start run due to integrity error: {exc}") from exc

    return RunStartResult(
        run_id=run.id,
        run_key=run.run_key,
        work_item_id=work_item.id,
        lease_id=lease.id,
        status=run.status.value,
    )


def append_run_event(
    session: Session,
    *,
    run_key: str,
    event_type: str,
    event_payload: dict[str, Any] | None = None,
) -> RunEventResult:
    run = session.query(Run).filter(Run.run_key == run_key).one_or_none()
    if run is None:
        raise RunNotFound(f"run not found: {run_key}")
    event = RunEvent(
        run_id=run.id,
        event_time=utcnow(),
        event_type=event_type,
        event_payload=event_payload or {},
    )
    session.add(event)
    session.flush()
    session.commit()
    return RunEventResult(
        run_id=run.id,
        run_key=run.run_key,
        event_id=event.id,
        event_type=event.event_type,
    )


def complete_run(
    session: Session,
    *,
    run_key: str,
    status: str,
    result_summary: str,
    result_payload: dict[str, Any] | None = None,
    artifacts: list[dict[str, Any]] | None = None,
) -> RunCompleteResult:
    run = session.query(Run).filter(Run.run_key == run_key).one_or_none()
    if run is None:
        raise RunNotFound(f"run not found: {run_key}")

    run_status = RunStatus(status)
    if run_status not in _TERMINAL_RUN_STATUSES:
        raise RunLifecycleError(f"status is not terminal: {status}")

    run.status = run_status
    run.completed_at = utcnow()
    run.result_summary = result_summary
    run.result_payload = result_payload

    work_item = run.work_item
    if run_status == RunStatus.SUCCEEDED:
        work_item.state = WorkItemState.ARTIFACT_SYNC
    else:
        work_item.state = WorkItemState.FAILED

    if run.lease is not None and run.lease.status == LeaseStatus.ACTIVE:
        run.lease.status = LeaseStatus.RELEASED
        run.lease.last_heartbeat_at = utcnow()

    created_artifacts: list[Artifact] = []
    for item in artifacts or []:
        artifact = Artifact(
            run_id=run.id,
            kind=item["kind"],
            storage_mode=ArtifactStorageMode(item["storage_mode"]),
            path=item["path"],
            sha256=item.get("sha256"),
            metadata_=item.get("metadata", {}),
        )
        session.add(artifact)
        created_artifacts.append(artifact)

    event = RunEvent(
        run_id=run.id,
        event_time=utcnow(),
        event_type="run_completed",
        event_payload={
            "status": run_status.value,
            "artifact_count": len(created_artifacts),
        },
    )
    session.add(event)
    session.commit()
    return RunCompleteResult(
        run_id=run.id,
        run_key=run.run_key,
        work_item_id=work_item.id,
        status=run.status.value,
        artifact_count=len(created_artifacts),
    )
