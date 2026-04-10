"""Resolver detection rules."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any

from sqlalchemy.orm import Session

from control_plane.clock import utcnow
from control_plane.models.enums import LeaseStatus, RunStatus, WorkItemState
from control_plane.models.run_events import RunEvent
from control_plane.models.runs import Run
from control_plane.models.work_items import WorkItem
from control_plane.models.worker_leases import WorkerLease
from control_plane.models.worker_machines import WorkerMachine

_TERMINAL_EVENT_TYPES = {
    "run_abandoned",
    "run_canceled",
    "run_completed",
    "run_failed",
    "run_timed_out",
}


@dataclass(frozen=True)
class ResolverDetection:
    fingerprint: str
    failure_class: str
    owner: str
    severity: str
    summary: str
    item_id: str
    run_key: str
    machine_key: str | None
    source_commit: str | None
    repo_root: str | None
    evidence: dict[str, Any]

    @property
    def evidence_hash(self) -> str:
        payload = json.dumps(self.evidence, sort_keys=True, default=str).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()


def _latest_event(session: Session, run_id: str) -> RunEvent | None:
    return (
        session.query(RunEvent)
        .filter(RunEvent.run_id == run_id)
        .order_by(RunEvent.event_time.desc(), RunEvent.id.desc())
        .first()
    )


def detect_orphaned_running_items(
    session: Session,
    *,
    repo_root: str | None = None,
) -> list[ResolverDetection]:
    now = utcnow()
    rows = (
        session.query(WorkerLease, WorkItem, WorkerMachine)
        .join(WorkItem, WorkItem.id == WorkerLease.work_item_id)
        .join(WorkerMachine, WorkerMachine.id == WorkerLease.machine_id)
        .filter(WorkerLease.status == LeaseStatus.ACTIVE)
        .filter(WorkerLease.expires_at < now)
        .filter(WorkItem.state == WorkItemState.RUNNING)
        .all()
    )
    detections: list[ResolverDetection] = []
    for lease, work_item, machine in rows:
        run = (
            session.query(Run)
            .filter(Run.work_item_id == work_item.id)
            .filter(Run.status == RunStatus.RUNNING)
            .order_by(Run.attempt.desc(), Run.created_at.desc())
            .first()
        )
        if run is None:
            continue
        latest_event = _latest_event(session, run.id)
        latest_event_type = latest_event.event_type if latest_event is not None else "no_event"
        if latest_event_type in _TERMINAL_EVENT_TYPES:
            continue
        evidence = {
            "item_id": work_item.item_id,
            "run_key": run.run_key,
            "machine_key": machine.machine_key,
            "lease_token": lease.lease_token,
            "lease_expires_at": lease.expires_at.isoformat() if lease.expires_at is not None else None,
            "last_heartbeat_at": lease.last_heartbeat_at.isoformat() if lease.last_heartbeat_at is not None else None,
            "latest_event_type": latest_event_type,
            "latest_event_time": latest_event.event_time.isoformat() if latest_event is not None else None,
            "work_item_state": work_item.state.value,
            "repo_root": repo_root,
            "source_commit": work_item.source_commit,
        }
        detections.append(
            ResolverDetection(
                fingerprint=f"orphaned_running_item:{latest_event_type}",
                failure_class="orphaned_running_item",
                owner="eval",
                severity="high",
                summary=f"work item {work_item.item_id} is still RUNNING after lease {lease.lease_token} expired",
                item_id=work_item.item_id,
                run_key=run.run_key,
                machine_key=machine.machine_key,
                source_commit=work_item.source_commit,
                repo_root=repo_root,
                evidence=evidence,
            )
        )
    return detections
