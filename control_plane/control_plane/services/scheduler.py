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


def select_next_work_item(
    session: Session,
    *,
    machine_key: str | None = None,
    machine_capabilities: dict[str, Any] | None = None,
    capability_filter: dict[str, Any] | None = None,
) -> WorkItem:
    effective = _effective_filter(machine_capabilities or {}, capability_filter)
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
    item = query.first()
    if item is None:
        raise NoEligibleWorkItem("no eligible work item for the requested capability filter")
    return item
