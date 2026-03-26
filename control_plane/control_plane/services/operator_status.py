"""Operator-oriented live status summary for the control plane."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from control_plane.clock import utcnow
from control_plane.models.enums import LeaseStatus, RunStatus, WorkItemState
from control_plane.models.github_links import GitHubLink
from control_plane.models.runs import Run
from control_plane.models.worker_leases import WorkerLease
from control_plane.models.work_items import WorkItem


@dataclass(frozen=True)
class OperatorStatusRequest:
    recent_limit: int = 10


@dataclass(frozen=True)
class OperatorStatusResult:
    health_summary: dict[str, object]
    state_counts: dict[str, int]
    active_runs: list[dict[str, object]]
    stale_leases: list[dict[str, object]]
    recent_failures: list[dict[str, object]]
    recent_submissions: list[dict[str, object]]


def load_operator_status(session: Session, request: OperatorStatusRequest) -> OperatorStatusResult:
    state_counts = {state.value: 0 for state in WorkItemState}
    for work_item in session.query(WorkItem).all():
        state_counts[work_item.state.value] = state_counts.get(work_item.state.value, 0) + 1

    now = utcnow()
    active_runs = []
    for run in (
        session.query(Run)
        .filter(Run.status == RunStatus.RUNNING)
        .order_by(Run.started_at.desc().nullslast(), Run.created_at.desc())
        .limit(request.recent_limit)
        .all()
    ):
        lease = run.lease
        active_runs.append(
            {
                "item_id": run.work_item.item_id,
                "run_key": run.run_key,
                "task_type": run.work_item.task_type,
                "worker_host": run.machine.hostname if run.machine is not None else None,
                "machine_key": run.machine.machine_key if run.machine is not None else None,
                "lease_token": lease.lease_token if lease is not None else None,
                "last_heartbeat_at": lease.last_heartbeat_at.isoformat() if lease and lease.last_heartbeat_at else None,
                "started_at": run.started_at.isoformat() if run.started_at else None,
            }
        )

    stale_leases = []
    for lease in (
        session.query(WorkerLease)
        .filter(WorkerLease.status == LeaseStatus.ACTIVE)
        .order_by(WorkerLease.expires_at.asc())
        .all()
    ):
        if lease.expires_at is None or lease.expires_at > now:
            continue
        stale_leases.append(
            {
                "item_id": lease.work_item.item_id,
                "lease_token": lease.lease_token,
                "machine_key": lease.machine.machine_key if lease.machine is not None else None,
                "hostname": lease.machine.hostname if lease.machine is not None else None,
                "expires_at": lease.expires_at.isoformat(),
                "last_heartbeat_at": lease.last_heartbeat_at.isoformat() if lease.last_heartbeat_at else None,
            }
        )

    recent_failures = []
    for run in (
        session.query(Run)
        .filter(Run.status == RunStatus.FAILED)
        .order_by(Run.completed_at.desc().nullslast(), Run.created_at.desc())
        .limit(request.recent_limit)
        .all()
    ):
        payload = dict(run.result_payload or {})
        failure = dict(payload.get("failure_classification") or {})
        failure_issue = dict(payload.get("failure_issue") or {})
        failure_issue_number = failure_issue.get("issue_number")
        if str(failure_issue_number or "").strip():
            failure_issue_status = "reported"
        elif bool(failure_issue.get("skipped")):
            failure_issue_status = f"skipped:{failure_issue.get('reason') or 'unspecified'}"
        else:
            failure_issue_status = "pending"
        recent_failures.append(
            {
                "item_id": run.work_item.item_id,
                "run_key": run.run_key,
                "task_type": run.work_item.task_type,
                "attempt": run.attempt,
                "status": run.status.value,
                "summary": run.result_summary,
                "failure_category": failure.get("category"),
                "failure_issue_status": failure_issue_status,
                "failure_issue_number": failure_issue_number,
                "retry_requeue": (payload.get("retry_decision") or {}).get("requeue"),
                "completed_at": run.completed_at.isoformat() if run.completed_at else None,
                "worker_host": run.machine.hostname if run.machine is not None else None,
            }
        )

    recent_submissions = []
    for link in (
        session.query(GitHubLink)
        .filter(GitHubLink.pr_number.isnot(None))
        .order_by(GitHubLink.updated_at.desc(), GitHubLink.created_at.desc())
        .limit(request.recent_limit)
        .all()
    ):
        recent_submissions.append(
            {
                "item_id": link.work_item.item_id,
                "run_key": link.run.run_key if link.run is not None else None,
                "pr_number": link.pr_number,
                "pr_url": link.pr_url,
                "state": link.state.value,
                "branch_name": link.branch_name,
                "updated_at": link.updated_at.isoformat() if link.updated_at else None,
            }
        )

    attention_flags = []
    if stale_leases:
        attention_flags.append(f"stale_leases={len(stale_leases)}")
    if recent_failures:
        attention_flags.append(f"recent_failures={len(recent_failures)}")
    if active_runs:
        attention_flags.append(f"active_runs={len(active_runs)}")
    pending_submission = state_counts.get(WorkItemState.ARTIFACT_SYNC.value, 0)
    if pending_submission:
        attention_flags.append(f"artifact_sync={pending_submission}")
    awaiting_review = state_counts.get(WorkItemState.AWAITING_REVIEW.value, 0)
    if awaiting_review:
        attention_flags.append(f"awaiting_review={awaiting_review}")
    ready_items = state_counts.get(WorkItemState.READY.value, 0)
    if ready_items:
        attention_flags.append(f"ready={ready_items}")

    if attention_flags:
        health_summary = {
            "status": "attention",
            "message": "attention: " + ", ".join(attention_flags),
        }
    else:
        health_summary = {
            "status": "healthy",
            "message": "healthy: no stale leases, no recent failures, no active runs, no pending submissions, no queued review items",
        }

    return OperatorStatusResult(
        health_summary=health_summary,
        state_counts=state_counts,
        active_runs=active_runs,
        stale_leases=stale_leases,
        recent_failures=recent_failures,
        recent_submissions=recent_submissions,
    )
