"""Ready-item dispatcher for multi-evaluator control."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from control_plane.clock import utcnow
from control_plane.models.enums import LeaseStatus, WorkItemState
from control_plane.models.worker_leases import WorkerLease
from control_plane.models.worker_machines import WorkerMachine
from control_plane.models.work_items import WorkItem
from control_plane.services.scheduler import assign_work_item


@dataclass(frozen=True)
class DispatchReadyRequest:
    max_assignments: int | None = None
    freshness_seconds: int = 120


@dataclass(frozen=True)
class DispatchAssignmentResult:
    item_id: str
    machine_key: str
    priority: int


def _as_comparable_utc(dt):
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=utcnow().tzinfo)
    return dt


def _machine_available_slots(session: Session, machine: WorkerMachine) -> int:
    active = (
        session.query(WorkerLease)
        .filter(WorkerLease.machine_id == machine.id, WorkerLease.status == LeaseStatus.ACTIVE)
        .count()
    )
    return max(0, int(machine.slot_capacity or 1) - active)


def _machine_matches_item(machine: WorkerMachine, work_item: WorkItem) -> bool:
    caps = dict(machine.capabilities or {})
    platform = str(caps.get("platform") or "").strip()
    flow = str(caps.get("flow") or "").strip()
    if platform and work_item.platform != platform:
        return False
    if flow and work_item.flow.value != flow:
        return False
    return True


def _is_machine_dispatchable(machine: WorkerMachine, *, freshness_seconds: int) -> bool:
    if not machine.active:
        return False
    if str(machine.role or "evaluator").strip() != "evaluator":
        return False
    if freshness_seconds <= 0:
        return True
    last_seen = _as_comparable_utc(machine.last_seen_at)
    if last_seen is None:
        return False
    age = (utcnow() - last_seen).total_seconds()
    return age <= freshness_seconds


def _next_unassigned_item_for_machine(session: Session, machine: WorkerMachine) -> WorkItem | None:
    query = (
        session.query(WorkItem)
        .filter(WorkItem.state == WorkItemState.READY)
        .filter(WorkItem.assigned_machine_key.is_(None))
        .filter(~WorkItem.leases.any(WorkerLease.status == LeaseStatus.ACTIVE))
        .order_by(WorkItem.priority.desc(), WorkItem.created_at.asc(), WorkItem.item_id.asc())
    )
    for item in query.all():
        if _machine_matches_item(machine, item):
            return item
    return None


def dispatch_ready_items(session: Session, request: DispatchReadyRequest) -> list[DispatchAssignmentResult]:
    results: list[DispatchAssignmentResult] = []
    machines = session.query(WorkerMachine).order_by(WorkerMachine.machine_key.asc()).all()
    remaining = request.max_assignments

    for machine in machines:
        if remaining is not None and remaining <= 0:
            break
        if not _is_machine_dispatchable(machine, freshness_seconds=request.freshness_seconds):
            continue
        available = _machine_available_slots(session, machine)
        while available > 0 and (remaining is None or remaining > 0):
            work_item = _next_unassigned_item_for_machine(session, machine)
            if work_item is None:
                break
            assigned = assign_work_item(session, item_id=work_item.item_id, machine_key=machine.machine_key)
            results.append(
                DispatchAssignmentResult(
                    item_id=assigned.item_id,
                    machine_key=machine.machine_key,
                    priority=work_item.priority,
                )
            )
            available -= 1
            if remaining is not None:
                remaining -= 1
    return results
