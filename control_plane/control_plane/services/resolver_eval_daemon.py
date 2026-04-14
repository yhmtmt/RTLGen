"""Eval-side resolver daemon."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import time
from typing import Callable

from sqlalchemy.exc import DBAPIError, OperationalError
from sqlalchemy.orm import Session, sessionmaker

from control_plane.clock import utcnow
from control_plane.models.resolver_cases import ResolverCase
from control_plane.models.resolver_observations import ResolverObservation
from control_plane.services.resolver_case_service import append_observation
from control_plane.services.resolver_issue_bridge import (
    ResolverIssueBridgeCommandError,
    ResolverIssueComment,
    ResolverRemoteIssue,
    list_open_resolver_issues,
    parse_resolver_diagnosis_block,
)


@dataclass(frozen=True)
class ResolverEvalDaemonConfig:
    repo: str
    machine_key: str | None = None
    poll_seconds: int = 60
    max_polls: int | None = None


@dataclass(frozen=True)
class ResolverEvalDaemonResult:
    poll_count: int
    issue_count: int
    observation_count: int


def _default_log(message: str) -> None:
    print(f"[{utcnow().isoformat().replace('+00:00', 'Z')}] {message}", flush=True)


def _dispose_session_engine(session_factory: sessionmaker, logger: Callable[[str], None]) -> None:
    engine = getattr(session_factory, "kw", {}).get("bind")
    if engine is None:
        return
    try:
        engine.dispose()
    except Exception as exc:  # pragma: no cover - defensive cleanup
        logger(f"resolver-eval engine_dispose_error error={exc}")


def _is_retryable_db_error(exc: Exception) -> bool:
    return isinstance(exc, (OperationalError, DBAPIError, ResolverIssueBridgeCommandError))


def _snapshot_payload(issue: ResolverRemoteIssue) -> dict[str, object]:
    latest_comment = issue.comments[-1] if issue.comments else None
    return {
        "issue_number": issue.issue_number,
        "title": issue.title,
        "state": issue.state,
        "issue_url": issue.issue_url,
        "updated_at": issue.updated_at,
        "case_metadata": dict(issue.case_metadata),
        "comment_count": len(issue.comments),
        "latest_comment_id": latest_comment.comment_id if latest_comment is not None else None,
        "latest_comment_body": latest_comment.body if latest_comment is not None else None,
        "latest_comment_author": latest_comment.author if latest_comment is not None else None,
        "latest_comment_updated_at": latest_comment.updated_at if latest_comment is not None else None,
    }


def _snapshot_hash(payload: dict[str, object]) -> str:
    blob = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def _latest_observation_hash(session: Session, case_id: str, *, kind: str, field_name: str) -> str | None:
    observation = (
        session.query(ResolverObservation)
        .filter(ResolverObservation.case_id == case_id)
        .filter(ResolverObservation.source == "github")
        .filter(ResolverObservation.kind == kind)
        .order_by(ResolverObservation.created_at.desc())
        .first()
    )
    if observation is None:
        return None
    payload = dict(observation.payload_json or {})
    value = str(payload.get(field_name) or "").strip()
    return value or None


def _matches_machine(issue: ResolverRemoteIssue, machine_key: str | None) -> bool:
    if not machine_key:
        return True
    issue_machine = str(issue.case_metadata.get("machine_key") or "").strip()
    return not issue_machine or issue_machine == machine_key


def _lookup_case(session: Session, issue: ResolverRemoteIssue) -> ResolverCase | None:
    case_id = str(issue.case_metadata.get("case_id") or "").strip()
    if not case_id:
        return None
    return session.query(ResolverCase).filter(ResolverCase.id == case_id).first()


def _sync_issue_snapshot(session: Session, issue: ResolverRemoteIssue) -> bool:
    case = _lookup_case(session, issue)
    if case is None:
        return False
    payload = _snapshot_payload(issue)
    payload["snapshot_hash"] = _snapshot_hash(payload)
    if _latest_observation_hash(session, case.id, kind="issue_snapshot", field_name="snapshot_hash") == payload["snapshot_hash"]:
        return False
    append_observation(
        session,
        case=case,
        source="github",
        kind="issue_snapshot",
        summary=f"issue #{issue.issue_number} snapshot synced",
        payload=payload,
    )
    return True


def _latest_diagnosis_comment(issue: ResolverRemoteIssue) -> tuple[ResolverIssueComment, dict[str, str]] | None:
    for comment in reversed(issue.comments):
        diagnosis = parse_resolver_diagnosis_block(comment.body)
        if diagnosis:
            return comment, diagnosis
    return None


def _sync_diagnosis(session: Session, issue: ResolverRemoteIssue) -> bool:
    case = _lookup_case(session, issue)
    if case is None:
        return False
    latest = _latest_diagnosis_comment(issue)
    if latest is None:
        return False
    comment, diagnosis = latest
    payload: dict[str, object] = {
        "issue_number": issue.issue_number,
        "issue_url": issue.issue_url,
        "comment_id": comment.comment_id,
        "comment_author": comment.author,
        "comment_created_at": comment.created_at,
        "comment_updated_at": comment.updated_at,
        "diagnosis": dict(diagnosis),
    }
    payload["diagnosis_hash"] = _snapshot_hash(payload)
    if _latest_observation_hash(session, case.id, kind="diagnosis", field_name="diagnosis_hash") == payload["diagnosis_hash"]:
        return False
    append_observation(
        session,
        case=case,
        source="github",
        kind="diagnosis",
        summary=f"issue #{issue.issue_number} diagnosis synced",
        payload=payload,
    )
    return True


def run_eval_resolver(
    session_factory: sessionmaker[Session],
    config: ResolverEvalDaemonConfig,
    *,
    log_fn: Callable[[str], None] | None = None,
) -> ResolverEvalDaemonResult:
    logger = log_fn or _default_log
    poll_count = 0
    issue_count = 0
    observation_count = 0

    while True:
        poll_count += 1
        try:
            issues = list_open_resolver_issues(config.repo, owner="eval", include_comments=True)
            issue_count += len(issues)
            with session_factory() as session:
                for issue in issues:
                    if not _matches_machine(issue, config.machine_key):
                        continue
                    if _sync_issue_snapshot(session, issue):
                        observation_count += 1
                    if _sync_diagnosis(session, issue):
                        observation_count += 1
        except Exception as exc:
            if _is_retryable_db_error(exc):
                logger(f"resolver-eval db_unavailable poll={poll_count} error={exc}")
                _dispose_session_engine(session_factory, logger)
                if config.max_polls is not None and poll_count >= config.max_polls:
                    break
                time.sleep(config.poll_seconds)
                continue
            raise
        if config.max_polls is not None and poll_count >= config.max_polls:
            break
        time.sleep(config.poll_seconds)

    return ResolverEvalDaemonResult(
        poll_count=poll_count,
        issue_count=issue_count,
        observation_count=observation_count,
    )
