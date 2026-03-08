"""Scheduler helpers for cp-005."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from control_plane.models.enums import FlowName, LeaseStatus, WorkItemState
from control_plane.models.work_items import WorkItem
from control_plane.models.worker_leases import WorkerLease


class NoEligibleWorkItem(RuntimeError):
    pass


def _effective_filter(machine_capabilities: dict[str, Any], capability_filter: dict[str, Any] | None) -> dict[str, Any]:
    merged = dict(machine_capabilities or {})
    merged.update(capability_filter or {})
    return merged


def select_next_work_item(
    session: Session,
    *,
    machine_capabilities: dict[str, Any] | None = None,
    capability_filter: dict[str, Any] | None = None,
) -> WorkItem:
    effective = _effective_filter(machine_capabilities or {}, capability_filter)
    query = (
        session.query(WorkItem)
        .filter(WorkItem.state == WorkItemState.READY)
        .filter(~WorkItem.leases.any(WorkerLease.status == LeaseStatus.ACTIVE))
    )

    if effective.get("platform"):
        query = query.filter(WorkItem.platform == effective["platform"])
    if effective.get("flow"):
        query = query.filter(WorkItem.flow == FlowName(effective["flow"]))

    query = query.order_by(WorkItem.priority.desc(), WorkItem.created_at.asc(), WorkItem.item_id.asc())
    item = query.first()
    if item is None:
        raise NoEligibleWorkItem("no eligible work item for the requested capability filter")
    return item
