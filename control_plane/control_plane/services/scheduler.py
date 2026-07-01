"""Scheduler helpers for cp-005."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import case
from sqlalchemy.orm import Session

from control_plane.models.enums import FlowName, LeaseStatus, WorkItemState
from control_plane.models.work_items import WorkItem
from control_plane.models.worker_machines import WorkerMachine
from control_plane.models.worker_leases import WorkerLease


class NoEligibleWorkItem(RuntimeError):
    pass


@dataclass(frozen=True)
class WorkItemAssignmentResult:
    item_id: str
    assigned_machine_key: str | None
    state: str


def assign_work_item(session: Session, *, item_id: str, machine_key: str | None) -> WorkItemAssignmentResult:
    work_item = session.query(WorkItem).filter(WorkItem.item_id == item_id).one_or_none()
    if work_item is None:
        raise NoEligibleWorkItem(f"work item not found: {item_id}")
    if work_item.state in {WorkItemState.MERGED, WorkItemState.SUPERSEDED}:
        raise NoEligibleWorkItem(f"cannot assign item from state={work_item.state.value}")
    if machine_key is not None:
        machine = session.query(WorkerMachine).filter(WorkerMachine.machine_key == machine_key).one_or_none()
        if machine is None:
            raise NoEligibleWorkItem(f"worker machine not found: {machine_key}")
    update_payload = {WorkItem.assigned_machine_key: machine_key}
    if machine_key is None:
        if work_item.state in {WorkItemState.READY, WorkItemState.DISPATCH_PENDING}:
            update_payload[WorkItem.state] = WorkItemState.DISPATCH_PENDING
    else:
        if work_item.state in {WorkItemState.DRAFT, WorkItemState.DISPATCH_PENDING, WorkItemState.READY}:
            update_payload[WorkItem.state] = WorkItemState.READY
    (
        session.query(WorkItem)
        .filter(WorkItem.id == work_item.id)
        .update(update_payload, synchronize_session=False)
    )
    session.commit()
    session.refresh(work_item)
    return WorkItemAssignmentResult(
        item_id=work_item.item_id,
        assigned_machine_key=work_item.assigned_machine_key,
        state=work_item.state.value,
    )


def _effective_filter(machine_capabilities: dict[str, Any], capability_filter: dict[str, Any] | None) -> dict[str, Any]:
    merged = dict(machine_capabilities or {})
    merged.update(capability_filter or {})
    return merged


def _boolish(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def work_item_requires_exclusive_worker(work_item: WorkItem) -> bool:
    """Return whether the item should occupy a worker by itself.

    OpenROAD block sweeps are host-heavy and can freeze evaluator machines when
    several are launched together. The explicit manifest flag lets future jobs
    opt into the same scheduling behavior without relying on command names.
    """

    inputs = dict(work_item.input_manifest or {})
    resources = dict(inputs.get("worker_resources") or {})
    if _boolish(resources.get("exclusive_worker")) or _boolish(resources.get("exclusive")):
        return True
    for command in work_item.command_manifest or []:
        run_text = str((command or {}).get("run") or "")
        if "run_block_sweep.py" in run_text:
            return True
    return False


def machine_has_active_exclusive_work(session: Session, machine_id: str) -> bool:
    active = (
        session.query(WorkItem)
        .join(WorkerLease, WorkerLease.work_item_id == WorkItem.id)
        .filter(WorkerLease.machine_id == machine_id)
        .filter(WorkerLease.status == LeaseStatus.ACTIVE)
        .all()
    )
    return any(work_item_requires_exclusive_worker(item) for item in active)


def machine_active_lease_count(session: Session, machine_id: str) -> int:
    return (
        session.query(WorkerLease)
        .filter(WorkerLease.machine_id == machine_id)
        .filter(WorkerLease.status == LeaseStatus.ACTIVE)
        .count()
    )


def select_next_work_item(
    session: Session,
    *,
    machine_key: str | None = None,
    machine_capabilities: dict[str, Any] | None = None,
    capability_filter: dict[str, Any] | None = None,
) -> WorkItem:
    effective = _effective_filter(machine_capabilities or {}, capability_filter)
    machine = None
    if machine_key:
        machine = session.query(WorkerMachine).filter(WorkerMachine.machine_key == machine_key).one_or_none()
        if machine is not None and machine_has_active_exclusive_work(session, machine.id):
            raise NoEligibleWorkItem("worker already has active exclusive work")

    query = (
        session.query(WorkItem)
        .filter(WorkItem.state == WorkItemState.READY)
        .filter(~WorkItem.leases.any(WorkerLease.status == LeaseStatus.ACTIVE))
    )

    if machine_key:
        query = query.filter(WorkItem.assigned_machine_key == machine_key)
    if effective.get("platform"):
        query = query.filter(WorkItem.platform == effective["platform"])
    if effective.get("flow"):
        query = query.filter(WorkItem.flow == FlowName(effective["flow"]))

    order_cols = []
    if machine_key:
        order_cols.append(case((WorkItem.assigned_machine_key == machine_key, 0), else_=1).asc())
    query = query.order_by(*order_cols, WorkItem.priority.desc(), WorkItem.created_at.asc(), WorkItem.item_id.asc())
    active_count = machine_active_lease_count(session, machine.id) if machine is not None else 0
    for item in query.all():
        if work_item_requires_exclusive_worker(item) and active_count > 0:
            continue
        return item
    raise NoEligibleWorkItem("no eligible work item for the requested capability filter")
