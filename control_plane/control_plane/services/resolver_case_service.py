"""Resolver case persistence helpers."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any

from sqlalchemy.orm import Session

from control_plane.clock import utcnow
from control_plane.models.resolver_actions import ResolverAction
from control_plane.models.resolver_cases import ResolverCase
from control_plane.models.resolver_observations import ResolverObservation
from control_plane.services.resolver_detection import ResolverDetection

_ACTIVE_CASE_STATUSES = ("open", "diagnosing", "fix_in_progress", "awaiting_remote", "awaiting_retry")


@dataclass(frozen=True)
class CaseUpsertResult:
    case: ResolverCase
    created: bool
    evidence_changed: bool
    evidence_hash: str


def _hash_payload(payload: Any) -> str:
    blob = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def upsert_case_from_detection(session: Session, detection: ResolverDetection) -> CaseUpsertResult:
    evidence_hash = detection.evidence_hash
    case = (
        session.query(ResolverCase)
        .filter(ResolverCase.fingerprint == detection.fingerprint)
        .filter(ResolverCase.status.in_(_ACTIVE_CASE_STATUSES))
        .filter(
            (ResolverCase.latest_item_id == detection.item_id)
            | (ResolverCase.first_item_id == detection.item_id)
        )
        .order_by(ResolverCase.created_at.desc())
        .first()
    )
    if case is None:
        case = ResolverCase(
            fingerprint=detection.fingerprint,
            failure_class=detection.failure_class,
            owner=detection.owner,
            status="open",
            severity=detection.severity,
            first_item_id=detection.item_id,
            latest_item_id=detection.item_id,
            first_run_key=detection.run_key,
            latest_run_key=detection.run_key,
            machine_key=detection.machine_key,
            source_commit=detection.source_commit,
            repo_root=detection.repo_root,
            evidence_json=detection.evidence,
            resolution_json={},
            last_evidence_hash=evidence_hash,
        )
        session.add(case)
        session.flush()
        session.add(
            ResolverObservation(
                case_id=case.id,
                source="db",
                kind="detection",
                summary=detection.summary,
                payload_json=detection.evidence,
            )
        )
        session.commit()
        return CaseUpsertResult(case=case, created=True, evidence_changed=True, evidence_hash=evidence_hash)

    evidence_changed = case.last_evidence_hash != evidence_hash
    case.latest_item_id = detection.item_id
    case.latest_run_key = detection.run_key
    case.machine_key = detection.machine_key
    case.source_commit = detection.source_commit
    case.repo_root = detection.repo_root
    if evidence_changed:
        case.evidence_json = detection.evidence
        case.last_evidence_hash = evidence_hash
        session.add(
            ResolverObservation(
                case_id=case.id,
                source="db",
                kind="evidence_update",
                summary=detection.summary,
                payload_json=detection.evidence,
            )
        )
    session.commit()
    return CaseUpsertResult(case=case, created=False, evidence_changed=evidence_changed, evidence_hash=evidence_hash)


def append_observation(
    session: Session,
    *,
    case: ResolverCase,
    source: str,
    kind: str,
    summary: str,
    payload: dict[str, Any],
) -> ResolverObservation:
    observation = ResolverObservation(
        case_id=case.id,
        source=source,
        kind=kind,
        summary=summary,
        payload_json=payload,
    )
    session.add(observation)
    session.commit()
    return observation


def record_action(
    session: Session,
    *,
    case: ResolverCase,
    actor: str,
    action_type: str,
    action_key: str,
    status: str,
    evidence_hash: str | None,
    failure_hash: str | None,
    request_json: dict[str, Any],
    result_json: dict[str, Any],
    count_attempt: bool = True,
) -> ResolverAction:
    attempt_index = case.attempt_count + 1 if count_attempt else case.attempt_count
    idempotency_key = _hash_payload({
        "case_id": case.id,
        "action_key": action_key,
        "attempt_index": attempt_index,
        "evidence_hash": evidence_hash,
    })
    action = ResolverAction(
        case_id=case.id,
        actor=actor,
        action_type=action_type,
        action_key=action_key,
        status=status,
        attempt_index=attempt_index,
        evidence_hash=evidence_hash,
        failure_hash=failure_hash,
        idempotency_key=idempotency_key,
        request_json=request_json,
        result_json=result_json,
    )
    session.add(action)
    case.last_action_type = action_key
    case.last_action_status = status
    if count_attempt:
        case.attempt_count = attempt_index
        case.last_attempted_evidence_hash = evidence_hash
        case.last_failure_hash = failure_hash
    session.commit()
    return action


def mark_escalated(
    session: Session,
    *,
    case: ResolverCase,
    reason: str,
    resolution: dict[str, Any] | None = None,
) -> ResolverCase:
    case.status = "escalated"
    case.escalation_reason = reason
    case.escalated_at = utcnow()
    case.resolution_json = dict(resolution or {})
    session.commit()
    return case


def mark_resolved(
    session: Session,
    *,
    case: ResolverCase,
    resolution: dict[str, Any] | None = None,
) -> ResolverCase:
    case.status = "resolved"
    case.resolved_at = utcnow()
    case.resolution_json = dict(resolution or {})
    session.commit()
    return case
