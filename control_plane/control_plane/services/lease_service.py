"""Lease acquisition, heartbeat, and expiry services for cp-005."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from control_plane.clock import utcnow
from control_plane.ids import make_id
from control_plane.models.enums import LeaseStatus, RunStatus, WorkItemState
from control_plane.models.worker_leases import WorkerLease
from control_plane.models.worker_machines import WorkerMachine
from control_plane.services.scheduler import NoEligibleWorkItem, select_next_work_item

_LEASE_CONFLICT_RETRIES = 8


class LeaseServiceError(RuntimeError):
    pass


class LeaseConflict(LeaseServiceError):
    pass


class LeaseNotFound(LeaseServiceError):
    pass


@dataclass(frozen=True)
class LeaseAcquireResult:
    lease_id: str
    lease_token: str
    work_item_id: str
    item_id: str
    machine_id: str
    machine_key: str
    expires_at: str
    status: str


@dataclass(frozen=True)
class LeaseHeartbeatResult:
    lease_id: str
    lease_token: str
    machine_id: str
    expires_at: str
    status: str


@dataclass(frozen=True)
class LeaseExpiryResult:
    expired_count: int
    requeued_count: int


def _as_iso(dt) -> str:
    return dt.isoformat()


def upsert_worker_machine(
    session: Session,
    *,
    machine_key: str,
    hostname: str | None = None,
    executor_kind: str = "docker",
    capabilities: dict[str, Any] | None = None,
) -> WorkerMachine:
    machine = session.query(WorkerMachine).filter(WorkerMachine.machine_key == machine_key).one_or_none()
    now = utcnow()
    if machine is None:
        machine = WorkerMachine(
            machine_key=machine_key,
            hostname=hostname or machine_key,
            executor_kind=executor_kind,
            capabilities=capabilities or {},
            active=True,
            last_seen_at=now,
        )
        session.add(machine)
        session.flush()
        return machine

    machine.hostname = hostname or machine.hostname
    machine.executor_kind = executor_kind or machine.executor_kind
    machine.capabilities = capabilities if capabilities is not None else machine.capabilities
    machine.active = True
    machine.last_seen_at = now
    session.flush()
    return machine


def acquire_next_lease(
    session: Session,
    *,
    machine_key: str,
    hostname: str | None = None,
    executor_kind: str = "docker",
    capabilities: dict[str, Any] | None = None,
    capability_filter: dict[str, Any] | None = None,
    lease_seconds: int = 1800,
) -> LeaseAcquireResult:
    last_error: IntegrityError | None = None
    for _ in range(_LEASE_CONFLICT_RETRIES):
        machine = upsert_worker_machine(
            session,
            machine_key=machine_key,
            hostname=hostname,
            executor_kind=executor_kind,
            capabilities=capabilities,
        )
        try:
            work_item = select_next_work_item(
                session,
                machine_capabilities=machine.capabilities,
                capability_filter=capability_filter,
            )
        except NoEligibleWorkItem:
            session.commit()
            raise

        now = utcnow()
        lease = WorkerLease(
            work_item_id=work_item.id,
            machine_id=machine.id,
            lease_token=make_id("lease"),
            status=LeaseStatus.ACTIVE,
            leased_at=now,
            expires_at=now + timedelta(seconds=lease_seconds),
            last_heartbeat_at=now,
        )
        session.add(lease)
        work_item.state = WorkItemState.LEASED
        try:
            session.commit()
        except IntegrityError as exc:
            session.rollback()
            last_error = exc
            continue

        return LeaseAcquireResult(
            lease_id=lease.id,
            lease_token=lease.lease_token,
            work_item_id=work_item.id,
            item_id=work_item.item_id,
            machine_id=machine.id,
            machine_key=machine.machine_key,
            expires_at=_as_iso(lease.expires_at),
            status=lease.status.value,
        )

    raise LeaseConflict(f"failed to acquire lease due to integrity error: {last_error}") from last_error


def heartbeat_lease(
    session: Session,
    *,
    lease_token: str,
    extend_seconds: int = 1800,
    progress: dict[str, Any] | None = None,
) -> LeaseHeartbeatResult:
    lease = session.query(WorkerLease).filter(WorkerLease.lease_token == lease_token).one_or_none()
    if lease is None:
        raise LeaseNotFound(f"lease not found: {lease_token}")
    if lease.status != LeaseStatus.ACTIVE:
        raise LeaseServiceError(f"lease is not active: {lease_token}")

    now = utcnow()
    lease.last_heartbeat_at = now
    lease.expires_at = now + timedelta(seconds=extend_seconds)
    lease.machine.last_seen_at = now
    if progress is not None:
        lease.machine.capabilities = {**(lease.machine.capabilities or {}), "last_progress": progress}
    session.commit()
    return LeaseHeartbeatResult(
        lease_id=lease.id,
        lease_token=lease.lease_token,
        machine_id=lease.machine_id,
        expires_at=_as_iso(lease.expires_at),
        status=lease.status.value,
    )


def expire_stale_leases(session: Session) -> LeaseExpiryResult:
    now = utcnow()
    leases = (
        session.query(WorkerLease)
        .filter(WorkerLease.status == LeaseStatus.ACTIVE)
        .filter(WorkerLease.expires_at < now)
        .all()
    )
    expired_count = 0
    requeued_count = 0
    for lease in leases:
        lease.status = LeaseStatus.EXPIRED
        expired_count += 1
        work_item = lease.work_item
        latest_run = None
        if work_item.runs:
            latest_run = sorted(work_item.runs, key=lambda run: (run.attempt, run.created_at or now))[-1]
        latest_run_terminal = latest_run is not None and latest_run.status in {
            RunStatus.SUCCEEDED,
            RunStatus.FAILED,
            RunStatus.CANCELED,
            RunStatus.TIMED_OUT,
        }
        if not latest_run_terminal and work_item.state in {WorkItemState.LEASED, WorkItemState.RUNNING}:
            work_item.state = WorkItemState.READY
            requeued_count += 1
    session.commit()
    return LeaseExpiryResult(expired_count=expired_count, requeued_count=requeued_count)
