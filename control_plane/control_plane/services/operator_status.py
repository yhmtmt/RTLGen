"""Operator-oriented live status summary for the control plane."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from control_plane.clock import utcnow
from control_plane.models.enums import LeaseStatus, RunStatus, WorkItemState
from control_plane.models.github_links import GitHubLink
from control_plane.models.run_events import RunEvent
from control_plane.models.runs import Run
from control_plane.models.worker_leases import WorkerLease
from control_plane.models.worker_machines import WorkerMachine
from control_plane.models.work_items import WorkItem
from control_plane.services.completion_retry_service import submission_retry_status
from control_plane.services.operator_submission import assess_submission_eligibility
from control_plane.services.run_index_query import comparative_run_index


def _as_comparable_utc(dt):
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=utcnow().tzinfo)
    return dt


def _submission_finalization_fields(link: GitHubLink) -> dict[str, Any]:
    metadata = dict(link.metadata_ or {})
    finalization_commit = str(metadata.get("finalization_commit") or "").strip() or None
    finalized_proposal_id = str(metadata.get("finalized_proposal_id") or "").strip() or None
    finalization_error = str(metadata.get("finalization_error") or "").strip() or None
    skip_reason = str(metadata.get("finalization_skip_reason") or "").strip() or None
    if finalization_commit:
        status = "finalized"
    elif bool(metadata.get("finalization_skipped")):
        status = "skipped"
    elif finalization_error:
        status = "failed"
    elif link.state.value == "pr_merged":
        status = "pending"
    else:
        status = "not_merged"
    return {
        "finalization_status": status,
        "finalized_proposal_id": finalized_proposal_id,
        "finalization_commit": finalization_commit,
        "finalization_error": finalization_error,
        "finalization_skip_reason": skip_reason,
    }


@dataclass(frozen=True)
class OperatorStatusRequest:
    recent_limit: int = 10
    repo_root: str = "/workspaces/rtlgen-eval-clean"


@dataclass(frozen=True)
class OperatorStatusResult:
    health_summary: dict[str, object]
    state_counts: dict[str, int]
    evaluator_machines: list[dict[str, object]]
    active_runs: list[dict[str, object]]
    stale_leases: list[dict[str, object]]
    pending_submission_items: list[dict[str, object]]
    dispatch_pending_items: list[dict[str, object]]
    recent_failures: list[dict[str, object]]
    recent_submissions: list[dict[str, object]]
    run_index_summary: dict[str, object]
    run_index_families: list[dict[str, object]]
    run_index_best_designs: list[dict[str, object]]
    run_index_family_leaders: list[dict[str, object]]
    run_index_failure_rates: list[dict[str, object]]


def _submission_reason_is_resumable(reason: str | None) -> bool:
    if not reason:
        return False
    normalized = reason.strip().lower()
    blocked_prefixes = (
        'no canonical runs evidence diff',
        'proposal already finalized',
        'missing developer_loop proposal linkage',
        'developer_loop proposal linkage does not resolve',
        'missing canonical runs evidence outputs',
        'unsupported_task_type=',
        'state=',
        'no_runs',
    )
    return not any(normalized.startswith(prefix) for prefix in blocked_prefixes)


def load_operator_status(session: Session, request: OperatorStatusRequest) -> OperatorStatusResult:
    state_counts = {state.value: 0 for state in WorkItemState}
    for work_item in session.query(WorkItem).all():
        state_counts[work_item.state.value] = state_counts.get(work_item.state.value, 0) + 1

    now = utcnow()

    evaluator_machines = []
    for machine in session.query(WorkerMachine).order_by(WorkerMachine.machine_key.asc()).all():
        active_slots = (
            session.query(WorkerLease)
            .filter(WorkerLease.machine_id == machine.id, WorkerLease.status == LeaseStatus.ACTIVE)
            .count()
        )
        assigned_ready = (
            session.query(WorkItem)
            .filter(WorkItem.assigned_machine_key == machine.machine_key, WorkItem.state == WorkItemState.READY)
            .count()
        )
        evaluator_machines.append(
            {
                "machine_key": machine.machine_key,
                "hostname": machine.hostname,
                "role": machine.role,
                "slot_capacity": machine.slot_capacity,
                "active_slots": active_slots,
                "assigned_ready": assigned_ready,
                "active": machine.active,
                "last_seen_at": machine.last_seen_at.isoformat() if machine.last_seen_at else None,
            }
        )

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
        expires_at = _as_comparable_utc(lease.expires_at)
        if expires_at is None or expires_at > now:
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

    pending_submission_items = []
    for work_item in (
        session.query(WorkItem)
        .filter(WorkItem.state == WorkItemState.ARTIFACT_SYNC)
        .order_by(WorkItem.updated_at.desc(), WorkItem.created_at.desc())
        .limit(request.recent_limit)
        .all()
    ):
        latest_run = None
        if work_item.runs:
            latest_run = sorted(work_item.runs, key=lambda row: (row.attempt, row.created_at or utcnow()))[-1]
        eligibility = assess_submission_eligibility(
            session,
            work_item=work_item,
            run=latest_run,
            repo_root=Path(request.repo_root).resolve(),
        )
        retry_status = submission_retry_status(session, work_item=work_item, run=latest_run)
        pending_submission_items.append(
            {
                "item_id": work_item.item_id,
                "task_type": work_item.task_type,
                "platform": work_item.platform,
                "updated_at": work_item.updated_at.isoformat() if work_item.updated_at else None,
                "run_key": latest_run.run_key if latest_run is not None else None,
                "run_status": latest_run.status.value if latest_run is not None else None,
                "eligible": eligibility.eligible,
                "reason": eligibility.reason,
                "resume_requested": retry_status.requested,
                "resumable": (
                    latest_run is not None
                    and latest_run.status == RunStatus.SUCCEEDED
                    and not eligibility.eligible
                    and not retry_status.requested
                    and _submission_reason_is_resumable(eligibility.reason)
                ),
            }
        )

    dispatch_pending_items = []
    for work_item in (
        session.query(WorkItem)
        .filter(WorkItem.state == WorkItemState.DISPATCH_PENDING)
        .order_by(WorkItem.updated_at.desc(), WorkItem.created_at.desc())
        .limit(request.recent_limit)
        .all()
    ):
        latest_run = None
        if work_item.runs:
            latest_run = sorted(work_item.runs, key=lambda row: (row.attempt, row.created_at or utcnow()))[-1]
        dispatch_pending_items.append(
            {
                "item_id": work_item.item_id,
                "task_type": work_item.task_type,
                "platform": work_item.platform,
                "assigned_machine_key": work_item.assigned_machine_key,
                "source_commit": work_item.source_commit,
                "created_at": work_item.created_at.isoformat() if work_item.created_at else None,
                "updated_at": work_item.updated_at.isoformat() if work_item.updated_at else None,
                "run_key": latest_run.run_key if latest_run is not None else None,
                "run_status": latest_run.status.value if latest_run is not None else None,
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

    run_index = comparative_run_index(session, limit=request.recent_limit)

    recent_submissions = []
    for link in (
        session.query(GitHubLink)
        .filter(GitHubLink.pr_number.isnot(None))
        .order_by(GitHubLink.updated_at.desc(), GitHubLink.created_at.desc())
        .limit(request.recent_limit)
        .all()
    ):
        finalization = _submission_finalization_fields(link)
        recent_submissions.append(
            {
                "item_id": link.work_item.item_id,
                "run_key": link.run.run_key if link.run is not None else None,
                "pr_number": link.pr_number,
                "pr_url": link.pr_url,
                "state": link.state.value,
                "branch_name": link.branch_name,
                "updated_at": link.updated_at.isoformat() if link.updated_at else None,
                **finalization,
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
    dispatch_pending_count = state_counts.get(WorkItemState.DISPATCH_PENDING.value, 0)
    if dispatch_pending_count:
        attention_flags.append(f"dispatch_pending={dispatch_pending_count}")
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
        evaluator_machines=evaluator_machines,
        active_runs=active_runs,
        stale_leases=stale_leases,
        pending_submission_items=pending_submission_items,
        dispatch_pending_items=dispatch_pending_items,
        recent_failures=recent_failures,
        recent_submissions=recent_submissions,
        run_index_summary=run_index.summary,
        run_index_families=run_index.families,
        run_index_best_designs=run_index.best_designs,
        run_index_family_leaders=run_index.family_leaders,
        run_index_failure_rates=run_index.failure_rates,
    )
