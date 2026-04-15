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
from control_plane.services.scheduler import NoEligibleWorkItem, assign_work_item


@dataclass(frozen=True)
class DispatchReadyRequest:
    max_assignments: int | None = None
    freshness_seconds: int = 120


@dataclass(frozen=True)
class DispatchAssignmentResult:
    item_id: str
    machine_key: str
    priority: int


@dataclass(frozen=True)
class AutoDispatchItemResult:
    item_id: str
    status: str
    machine_key: str | None = None
    reason: str | None = None


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
        .filter(WorkItem.assigned_machine_key.is_(None))
        .filter(WorkItem.state.in_([WorkItemState.DISPATCH_PENDING, WorkItemState.READY]))
        .filter(~WorkItem.leases.any(WorkerLease.status == LeaseStatus.ACTIVE))
        .order_by(WorkItem.priority.desc(), WorkItem.created_at.asc(), WorkItem.item_id.asc())
    )
    for item in query.all():
        if _machine_matches_item(machine, item):
            return item
    return None


def auto_dispatch_item(
    session: Session,
    *,
    item_id: str,
    machine_key: str | None = None,
    freshness_seconds: int = 120,
) -> AutoDispatchItemResult:
    work_item = session.query(WorkItem).filter(WorkItem.item_id == item_id).one_or_none()
    if work_item is None:
        raise NoEligibleWorkItem(f"work item not found: {item_id}")
    if work_item.state in {WorkItemState.MERGED, WorkItemState.SUPERSEDED}:
        return AutoDispatchItemResult(item_id=item_id, status="skipped", reason=f"terminal_state:{work_item.state.value}")
    if work_item.assigned_machine_key:
        return AutoDispatchItemResult(
            item_id=item_id,
            status="skipped",
            machine_key=work_item.assigned_machine_key,
            reason="already_assigned",
        )

    def _assign(target_machine_key: str) -> AutoDispatchItemResult:
        assigned = assign_work_item(session, item_id=item_id, machine_key=target_machine_key)
        return AutoDispatchItemResult(
            item_id=item_id,
            status="assigned",
            machine_key=assigned.assigned_machine_key,
            reason=assigned.state,
        )

    if machine_key is not None:
        machine = session.query(WorkerMachine).filter(WorkerMachine.machine_key == machine_key).one_or_none()
        if machine is None:
            raise NoEligibleWorkItem(f"worker machine not found: {machine_key}")
        if not _is_machine_dispatchable(machine, freshness_seconds=freshness_seconds):
            return AutoDispatchItemResult(item_id=item_id, status="skipped", reason="machine_not_dispatchable")
        if _machine_available_slots(session, machine) <= 0:
            return AutoDispatchItemResult(item_id=item_id, status="skipped", reason="machine_has_no_capacity")
        if not _machine_matches_item(machine, work_item):
            return AutoDispatchItemResult(item_id=item_id, status="skipped", reason="machine_capability_mismatch")
        return _assign(machine.machine_key)

    candidates = [
        machine
        for machine in session.query(WorkerMachine).order_by(WorkerMachine.machine_key.asc()).all()
        if _is_machine_dispatchable(machine, freshness_seconds=freshness_seconds)
        and _machine_available_slots(session, machine) > 0
        and _machine_matches_item(machine, work_item)
    ]
    if not candidates:
        return AutoDispatchItemResult(item_id=item_id, status="skipped", reason="no_eligible_machine")
    if len(candidates) > 1:
        return AutoDispatchItemResult(item_id=item_id, status="skipped", reason="multiple_eligible_machines")
    return _assign(candidates[0].machine_key)


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
