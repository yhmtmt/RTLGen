"""Dev-side resolver daemon."""

from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Callable

from sqlalchemy.exc import DBAPIError, OperationalError
from sqlalchemy.orm import Session, sessionmaker

from control_plane.clock import utcnow
from control_plane.models.enums import WorkItemState
from control_plane.models.resolver_actions import ResolverAction
from control_plane.models.resolver_cases import ResolverCase
from control_plane.models.work_items import WorkItem
from control_plane.models.resolver_observations import ResolverObservation
from control_plane.services.completion_retry_service import CompletionRetryError, request_submission_retry
from control_plane.services.lease_service import expire_stale_leases
from control_plane.services.resolver_case_service import (
    append_observation,
    mark_escalated,
    mark_resolved,
    record_action,
    upsert_case_from_detection,
)
from control_plane.services.resolver_detection import (
    ResolverDetection,
    detect_blocked_submission_items,
    detect_orphaned_running_items,
)
from control_plane.services.resolver_issue_bridge import (
    ResolverIssueBridgeCommandError,
    build_issue_comment,
    close_issue_for_case,
    comment_issue_for_case,
    fetch_issue,
    fetch_issue_comments,
    open_issue_for_case,
    parse_resolver_diagnosis_block,
)
from control_plane.services.resolver_policy import retry_allowed


@dataclass(frozen=True)
class ResolverDevDaemonConfig:
    repo: str
    repo_root: str
    poll_seconds: int = 60
    max_polls: int | None = None
    orphaned_stale_grace_seconds: int = 600
    blocked_submission_stale_grace_seconds: int = 120


@dataclass(frozen=True)
class ResolverDevDaemonResult:
    poll_count: int
    detection_count: int
    opened_issue_count: int
    updated_issue_count: int
    escalated_count: int


def _default_log(message: str) -> None:
    print(f"[{utcnow().isoformat().replace('+00:00', 'Z')}] {message}", flush=True)


def _dispose_session_engine(session_factory: sessionmaker, logger: Callable[[str], None]) -> None:
    engine = getattr(session_factory, "kw", {}).get("bind")
    if engine is None:
        return
    try:
        engine.dispose()
    except Exception as exc:  # pragma: no cover - defensive cleanup
        logger(f"resolver-dev engine_dispose_error error={exc}")


def _is_retryable_db_error(exc: Exception) -> bool:
    return isinstance(exc, (OperationalError, DBAPIError, ResolverIssueBridgeCommandError))


def _latest_diagnosis_payload(session: Session, case: ResolverCase) -> dict[str, object] | None:
    observation = (
        session.query(ResolverObservation)
        .filter(ResolverObservation.case_id == case.id)
        .filter(ResolverObservation.source == "github")
        .filter(ResolverObservation.kind == "diagnosis")
        .order_by(ResolverObservation.created_at.desc())
        .first()
    )
    if observation is None:
        return None
    payload = dict(observation.payload_json or {})
    diagnosis = payload.get("diagnosis")
    if not isinstance(diagnosis, dict):
        return None
    return payload


def _sync_issue_diagnosis_comments(session: Session, *, repo: str, case: ResolverCase) -> None:
    if case.issue_number is None:
        return
    comments = fetch_issue_comments(repo, int(case.issue_number))
    seen_comment_ids = {
        int(payload.get("comment_id") or 0)
        for (payload,) in (
            session.query(ResolverObservation.payload_json)
            .filter(ResolverObservation.case_id == case.id)
            .filter(ResolverObservation.source == "github")
            .filter(ResolverObservation.kind == "diagnosis")
            .all()
        )
        if isinstance(payload, dict) and int(payload.get("comment_id") or 0) > 0
    }
    for comment in comments:
        if comment.comment_id in seen_comment_ids:
            continue
        diagnosis = parse_resolver_diagnosis_block(comment.body)
        if not diagnosis:
            continue
        payload = {
            "issue_number": case.issue_number,
            "comment_id": comment.comment_id,
            "comment_author": comment.author,
            "comment_created_at": comment.created_at,
            "comment_updated_at": comment.updated_at,
            "diagnosis_hash": f"issue:{case.issue_number}:comment:{comment.comment_id}",
            "diagnosis": diagnosis,
        }
        append_observation(
            session,
            case=case,
            source="github",
            kind="diagnosis",
            summary=f"issue #{case.issue_number} diagnosis comment {comment.comment_id} synced by dev resolver",
            payload=payload,
        )
        seen_comment_ids.add(comment.comment_id)


def _recommended_action(payload: dict[str, object] | None) -> str | None:
    if not payload:
        return None
    diagnosis = payload.get("diagnosis")
    if not isinstance(diagnosis, dict):
        return None
    raw_value = str(diagnosis.get("recommended_action") or diagnosis.get("recommended_next_action") or "").strip().lower()
    normalized = raw_value.replace("-", "_").replace(" ", "_")
    if normalized in {"expire_stale_lease", "expire_stale_leases"}:
        return "expire_stale_lease"
    if normalized in {"retry_submission", "request_submission_retry", "resume_submission"}:
        return "retry_submission"
    return None


def _diagnosis_force_flag(payload: dict[str, object] | None) -> bool:
    if not payload:
        return False
    diagnosis = payload.get("diagnosis")
    if not isinstance(diagnosis, dict):
        return False
    raw_value = diagnosis.get("force")
    if isinstance(raw_value, bool):
        return raw_value
    return str(raw_value or "").strip().lower() in {"1", "true", "yes", "force"}


def _comment_case_update(repo: str, case: ResolverCase, *, reason: str) -> None:
    if case.issue_number is None:
        return
    comment_issue_for_case(repo, case.issue_number, body=build_issue_comment(case, reason=reason))


def _already_reported_comment_reason(session: Session, *, case: ResolverCase, reason: str, evidence_hash: str | None) -> bool:
    action = (
        session.query(ResolverAction)
        .filter(ResolverAction.case_id == case.id)
        .filter(ResolverAction.action_key == "comment_issue")
        .filter(ResolverAction.status == "applied")
        .filter(ResolverAction.evidence_hash == evidence_hash)
        .order_by(ResolverAction.created_at.desc())
        .first()
    )
    if action is None:
        return False
    result = dict(action.result_json or {})
    return str(result.get("reason") or "") == reason


def _resolve_case_if_item_inactive(session: Session, *, repo: str, case: ResolverCase) -> bool:
    item_id = case.latest_item_id or case.first_item_id or ""
    if not item_id:
        return False
    work_item = session.query(WorkItem).filter(WorkItem.item_id == item_id).first()
    if work_item is None:
        resolution = {"reason": "work_item_missing", "item_id": item_id}
    else:
        state = work_item.state
        if state not in {WorkItemState.SUPERSEDED, WorkItemState.MERGED}:
            return False
        resolution = {"reason": "work_item_inactive", "item_id": item_id, "work_item_state": state.value}
    mark_resolved(session, case=case, resolution=resolution)
    if case.issue_number is not None:
        remote_issue = fetch_issue(repo, int(case.issue_number))
        if str(remote_issue.state or "").lower() == "open":
            close_issue_for_case(repo, int(case.issue_number))
    return True


def _apply_expire_stale_lease(
    session: Session,
    *,
    repo: str,
    case: ResolverCase,
    payload: dict[str, object],
) -> tuple[int, int, bool]:
    updated_issue_count = 0
    escalated_count = 0
    evidence_hash = str(payload.get("diagnosis_hash") or case.last_evidence_hash or "") or None
    decision = retry_allowed(session, case, action_key="expire_stale_lease", evidence_hash=evidence_hash)
    if not decision.allowed:
        mark_escalated(session, case=case, reason=decision.reason)
        _comment_case_update(repo, case, reason=f"escalated:{decision.reason}")
        if case.issue_number is not None:
            updated_issue_count += 1
        escalated_count += 1
        return updated_issue_count, escalated_count, True

    result = expire_stale_leases(session)
    case.status = "awaiting_retry"
    record_action(
        session,
        case=case,
        actor="dev",
        action_type="expire_stale_leases",
        action_key="expire_stale_lease",
        status="applied",
        evidence_hash=evidence_hash,
        failure_hash=None,
        request_json={"repo": repo, "issue_number": case.issue_number},
        result_json={
            "expired_count": result.expired_count,
            "requeued_count": result.requeued_count,
            "cleaned_run_count": result.cleaned_run_count,
        },
    )
    _comment_case_update(repo, case, reason="applied:expire_stale_lease")
    if case.issue_number is not None:
        record_action(
            session,
            case=case,
            actor="dev",
            action_type="comment_issue",
            action_key="comment_issue",
            status="applied",
            evidence_hash=evidence_hash,
            failure_hash=None,
            request_json={"repo": repo, "issue_number": case.issue_number},
            result_json={"reason": "applied:expire_stale_lease"},
            count_attempt=False,
        )
        updated_issue_count += 1
    return updated_issue_count, escalated_count, True


def _apply_retry_submission(
    session: Session,
    *,
    repo: str,
    case: ResolverCase,
    payload: dict[str, object],
) -> tuple[int, int, bool]:
    updated_issue_count = 0
    escalated_count = 0
    evidence_hash = str(payload.get("diagnosis_hash") or case.last_evidence_hash or "") or None
    decision = retry_allowed(session, case, action_key="retry_submission", evidence_hash=evidence_hash)
    if not decision.allowed:
        mark_escalated(session, case=case, reason=decision.reason)
        _comment_case_update(repo, case, reason=f"escalated:{decision.reason}")
        if case.issue_number is not None:
            updated_issue_count += 1
        escalated_count += 1
        return updated_issue_count, escalated_count, True

    item_id = case.latest_item_id or case.first_item_id or ""
    if not item_id:
        mark_escalated(session, case=case, reason="missing_item_id")
        _comment_case_update(repo, case, reason="escalated:missing_item_id")
        if case.issue_number is not None:
            updated_issue_count += 1
        escalated_count += 1
        return updated_issue_count, escalated_count, True

    force = _diagnosis_force_flag(payload)
    try:
        result = request_submission_retry(
            session,
            item_id=item_id,
            actor="resolver_dev_daemon",
            force=force,
        )
    except CompletionRetryError as exc:
        failure_hash = str(exc)
        record_action(
            session,
            case=case,
            actor="dev",
            action_type="retry_submission",
            action_key="retry_submission",
            status="failed",
            evidence_hash=evidence_hash,
            failure_hash=failure_hash,
            request_json={"repo": repo, "issue_number": case.issue_number, "item_id": item_id, "force": force},
            result_json={"error": str(exc)},
        )
        mark_escalated(session, case=case, reason=f"retry_submission_failed:{exc}")
        _comment_case_update(repo, case, reason=f"escalated:retry_submission_failed:{exc}")
        if case.issue_number is not None:
            updated_issue_count += 1
        escalated_count += 1
        return updated_issue_count, escalated_count, True

    case.status = "awaiting_retry"
    action_status = "skipped" if result.already_requested else "applied"
    record_action(
        session,
        case=case,
        actor="dev",
        action_type="retry_submission",
        action_key="retry_submission",
        status=action_status,
        evidence_hash=evidence_hash,
        failure_hash=None,
        request_json={"repo": repo, "issue_number": case.issue_number, "item_id": item_id, "force": force},
        result_json={
            "request_id": result.request_id,
            "target_machine_key": result.target_machine_key,
            "already_requested": result.already_requested,
        },
        count_attempt=not result.already_requested,
    )
    reason = "already_requested:retry_submission" if result.already_requested else "applied:retry_submission"
    _comment_case_update(repo, case, reason=reason)
    if case.issue_number is not None:
        record_action(
            session,
            case=case,
            actor="dev",
            action_type="comment_issue",
            action_key="comment_issue",
            status="applied",
            evidence_hash=evidence_hash,
            failure_hash=None,
            request_json={"repo": repo, "issue_number": case.issue_number},
            result_json={"reason": reason},
            count_attempt=False,
        )
        updated_issue_count += 1
    return updated_issue_count, escalated_count, True


def _maybe_apply_diagnosis_action(
    session: Session,
    *,
    repo: str,
    case: ResolverCase,
) -> tuple[int, int, bool]:
    payload = _latest_diagnosis_payload(session, case)
    action = _recommended_action(payload)
    if action == "expire_stale_lease":
        return _apply_expire_stale_lease(session, repo=repo, case=case, payload=payload or {})
    if action == "retry_submission":
        return _apply_retry_submission(session, repo=repo, case=case, payload=payload or {})
    return 0, 0, False


def _handle_detection(
    session: Session,
    *,
    repo: str,
    detection: ResolverDetection,
) -> tuple[int, int, int]:
    opened_issue_count = 0
    updated_issue_count = 0
    escalated_count = 0

    upsert = upsert_case_from_detection(session, detection)
    case = upsert.case

    if case.issue_number is None:
        decision = retry_allowed(session, case, action_key="open_issue", evidence_hash=upsert.evidence_hash)
        if not decision.allowed:
            mark_escalated(session, case=case, reason=decision.reason)
            escalated_count += 1
            return opened_issue_count, updated_issue_count, escalated_count
        issue = open_issue_for_case(repo, case)
        case.issue_number = issue.issue_number
        case.status = "awaiting_remote"
        session.commit()
        record_action(
            session,
            case=case,
            actor="dev",
            action_type="open_issue",
            action_key="open_issue",
            status="applied",
            evidence_hash=upsert.evidence_hash,
            failure_hash=None,
            request_json={"repo": repo},
            result_json={"issue_number": issue.issue_number, "issue_url": issue.issue_url},
        )
        opened_issue_count += 1
        return opened_issue_count, updated_issue_count, escalated_count

    _sync_issue_diagnosis_comments(session, repo=repo, case=case)
    action_updated, action_escalated, action_applied = _maybe_apply_diagnosis_action(session, repo=repo, case=case)
    updated_issue_count += action_updated
    escalated_count += action_escalated
    if action_applied:
        return opened_issue_count, updated_issue_count, escalated_count

    if upsert.evidence_changed:
        decision = retry_allowed(
            session,
            case,
            action_key="comment_issue",
            evidence_hash=upsert.evidence_hash,
            diagnostic_only=True,
        )
        if decision.allowed:
            reason = "evidence_changed"
            if not _already_reported_comment_reason(session, case=case, reason=reason, evidence_hash=upsert.evidence_hash):
                _comment_case_update(repo, case, reason=reason)
                record_action(
                    session,
                    case=case,
                    actor="dev",
                    action_type="comment_issue",
                    action_key="comment_issue",
                    status="applied",
                    evidence_hash=upsert.evidence_hash,
                    failure_hash=None,
                    request_json={"repo": repo, "issue_number": case.issue_number},
                    result_json={"reason": reason},
                    count_attempt=False,
                )
                updated_issue_count += 1
        else:
            mark_escalated(session, case=case, reason=decision.reason)
            _comment_case_update(repo, case, reason=f"escalated:{decision.reason}")
            escalated_count += 1
    return opened_issue_count, updated_issue_count, escalated_count


def _reconcile_closed_remote_issues(session: Session, *, repo: str) -> None:
    cases = (
        session.query(ResolverCase)
        .filter(ResolverCase.status.in_(("open", "diagnosing", "fix_in_progress", "awaiting_remote", "awaiting_retry")))
        .filter(ResolverCase.issue_number.isnot(None))
        .all()
    )
    for case in cases:
        if _resolve_case_if_item_inactive(session, repo=repo, case=case):
            continue
        remote_issue = fetch_issue(repo, int(case.issue_number))
        if str(remote_issue.state or "").lower() == "open":
            continue
        mark_resolved(
            session,
            case=case,
            resolution={
                "reason": "remote_issue_closed",
                "issue_number": case.issue_number,
                "issue_state": remote_issue.state,
            },
        )


def _collect_detections(
    session: Session,
    *,
    repo_root: str,
    orphaned_stale_grace_seconds: int,
    blocked_submission_stale_grace_seconds: int,
) -> list[ResolverDetection]:
    detections = detect_orphaned_running_items(
        session,
        repo_root=repo_root,
        stale_grace_seconds=orphaned_stale_grace_seconds,
    )
    detections.extend(
        detect_blocked_submission_items(
            session,
            repo_root=repo_root,
            stale_grace_seconds=blocked_submission_stale_grace_seconds,
        )
    )
    return sorted(detections, key=lambda row: (row.failure_class, row.item_id, row.run_key))


def run_dev_resolver(
    session_factory: sessionmaker[Session],
    config: ResolverDevDaemonConfig,
    *,
    log_fn: Callable[[str], None] | None = None,
) -> ResolverDevDaemonResult:
    logger = log_fn or _default_log
    poll_count = 0
    detection_count = 0
    opened_issue_count = 0
    updated_issue_count = 0
    escalated_count = 0

    while True:
        poll_count += 1
        try:
            with session_factory() as session:
                _reconcile_closed_remote_issues(session, repo=config.repo)
                detections = _collect_detections(
                    session,
                    repo_root=config.repo_root,
                    orphaned_stale_grace_seconds=config.orphaned_stale_grace_seconds,
                    blocked_submission_stale_grace_seconds=config.blocked_submission_stale_grace_seconds,
                )
                detection_count += len(detections)
                for detection in detections:
                    opened, updated, escalated = _handle_detection(session, repo=config.repo, detection=detection)
                    opened_issue_count += opened
                    updated_issue_count += updated
                    escalated_count += escalated
        except Exception as exc:
            if _is_retryable_db_error(exc):
                logger(f"resolver-dev db_unavailable poll={poll_count} error={exc}")
                _dispose_session_engine(session_factory, logger)
                if config.max_polls is not None and poll_count >= config.max_polls:
                    break
                time.sleep(config.poll_seconds)
                continue
            raise
        if config.max_polls is not None and poll_count >= config.max_polls:
            break
        time.sleep(config.poll_seconds)

    return ResolverDevDaemonResult(
        poll_count=poll_count,
        detection_count=detection_count,
        opened_issue_count=opened_issue_count,
        updated_issue_count=updated_issue_count,
        escalated_count=escalated_count,
    )
