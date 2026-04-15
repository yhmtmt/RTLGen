"""Resolver detection rules."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from sqlalchemy.orm import Session

from control_plane.clock import utcnow
from control_plane.models.enums import LeaseStatus, RunStatus, WorkItemState
from control_plane.models.run_events import RunEvent
from control_plane.models.runs import Run
from control_plane.models.work_items import WorkItem
from control_plane.models.worker_leases import WorkerLease
from control_plane.models.worker_machines import WorkerMachine
from control_plane.services.operator_submission import assess_submission_eligibility

_TERMINAL_EVENT_TYPES = {
    "run_abandoned",
    "run_canceled",
    "run_completed",
    "run_failed",
    "run_timed_out",
}


def _latest_run(session: Session, work_item_id: str) -> Run | None:
    return (
        session.query(Run)
        .filter(Run.work_item_id == work_item_id)
        .order_by(Run.attempt.desc(), Run.created_at.desc())
        .first()
    )


def _normalize_reason_slug(reason: str | None) -> str:
    text = str(reason or "").strip().lower()
    if not text:
        return "unknown"
    text = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    return text[:96] or "unknown"


def _artifact_sync_reason_classification(reason: str | None) -> tuple[str, str, str]:
    normalized = str(reason or "").strip().lower()
    if normalized.startswith("missing developer_loop proposal linkage"):
        return "proposal_linkage_missing", "dev", "high"
    if normalized.startswith("developer_loop proposal linkage does not resolve"):
        return "proposal_linkage_unresolved", "dev", "high"
    if normalized.startswith("missing canonical runs evidence outputs"):
        return "missing_canonical_runs_evidence_outputs", "dev", "high"
    if normalized.startswith("no canonical runs evidence diff"):
        return "no_canonical_runs_evidence_diff", "dev", "medium"
    if normalized.startswith("missing ") and normalized.endswith(" review file"):
        return "missing_review_file", "dev", "medium"
    if normalized.startswith("missing ") and normalized.endswith(" artifact"):
        return "missing_review_artifact", "dev", "medium"
    if normalized.startswith("gh pr create failed"):
        return "gh_pr_create_failed", "eval", "medium"
    if normalized.startswith("proposal already finalized"):
        return "proposal_already_finalized", "dev", "low"
    if normalized.startswith("state="):
        return "invalid_submission_state", "dev", "low"
    if normalized.startswith("no_runs"):
        return "no_runs", "dev", "medium"
    if normalized.startswith("unsupported_task_type="):
        return "unsupported_task_type", "dev", "medium"
    return _normalize_reason_slug(normalized), "joint", "medium"


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
    stale_grace_seconds: int = 600,
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
        stale_seconds = None
        if lease.expires_at is not None:
            expires_at = lease.expires_at
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=now.tzinfo)
            stale_seconds = max((now - expires_at).total_seconds(), 0.0)
            if stale_seconds < max(int(stale_grace_seconds), 0):
                continue
        run = _latest_run(session, work_item.id)
        if run is None:
            continue
        if run.status != RunStatus.RUNNING:
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


def detect_blocked_submission_items(
    session: Session,
    *,
    repo_root: str | None = None,
    stale_grace_seconds: int = 120,
) -> list[ResolverDetection]:
    rows = (
        session.query(WorkItem)
        .filter(WorkItem.state == WorkItemState.ARTIFACT_SYNC)
        .order_by(WorkItem.created_at.asc(), WorkItem.item_id.asc())
        .all()
    )
    detections: list[ResolverDetection] = []
    repo_path = Path(repo_root).resolve() if repo_root else None
    now = utcnow()
    for work_item in rows:
        run = _latest_run(session, work_item.id)
        if run is None:
            continue
        submission_failure_reason = None
        latest_event = _latest_event(session, run.id)
        latest_event_time = latest_event.event_time if latest_event is not None else None
        if latest_event_time is not None and latest_event_time.tzinfo is None:
            latest_event_time = latest_event_time.replace(tzinfo=now.tzinfo)
        if latest_event_time is not None and (now - latest_event_time).total_seconds() < stale_grace_seconds:
            submission_failure_reason = assess_submission_eligibility(
                session,
                work_item=work_item,
                run=run,
                repo_root=None,
            ).reason
            if not (submission_failure_reason and str(submission_failure_reason).strip().lower().startswith("gh pr create failed")):
                continue
        eligibility = assess_submission_eligibility(
            session,
            work_item=work_item,
            run=run,
            repo_root=repo_path,
        )
        if eligibility.eligible or not eligibility.reason:
            continue
        reason_key, owner, severity = _artifact_sync_reason_classification(eligibility.reason)
        evidence = {
            "item_id": work_item.item_id,
            "run_key": run.run_key,
            "run_status": run.status.value,
            "machine_key": work_item.assigned_machine_key,
            "eligibility_reason": eligibility.reason,
            "task_type": work_item.task_type,
            "work_item_state": work_item.state.value,
            "repo_root": repo_root,
            "source_commit": work_item.source_commit,
        }
        detections.append(
            ResolverDetection(
                fingerprint=f"artifact_sync_blocked_submission:{reason_key}",
                failure_class="artifact_sync_blocked_submission",
                owner=owner,
                severity=severity,
                summary=f"work item {work_item.item_id} is blocked in ARTIFACT_SYNC: {eligibility.reason}",
                item_id=work_item.item_id,
                run_key=run.run_key,
                machine_key=work_item.assigned_machine_key,
                source_commit=work_item.source_commit,
                repo_root=repo_root,
                evidence=evidence,
            )
        )
    return detections
