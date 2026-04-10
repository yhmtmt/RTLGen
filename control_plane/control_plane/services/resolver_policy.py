"""Resolver attempt budgeting and escalation rules."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from control_plane.models.resolver_actions import ResolverAction
from control_plane.models.resolver_cases import ResolverCase

MAX_TOTAL_ATTEMPTS = 3
ACTION_LIMITS = {
    "open_issue": 1,
    "comment_issue": 10,
    "expire_stale_lease": 1,
    "assign_item": 1,
    "retry_submission": 2,
    "restart_worker": 1,
    "open_fix_pr": 1,
}


@dataclass(frozen=True)
class RetryDecision:
    allowed: bool
    reason: str


def action_limit(action_key: str) -> int:
    return ACTION_LIMITS.get(action_key, 1)


def retry_allowed(
    session: Session,
    case: ResolverCase,
    *,
    action_key: str,
    evidence_hash: str | None,
    failure_hash: str | None = None,
    diagnostic_only: bool = False,
) -> RetryDecision:
    if case.status in {"resolved", "escalated"}:
        return RetryDecision(False, f"case_{case.status}")
    if case.attempt_count >= (case.max_attempts or MAX_TOTAL_ATTEMPTS):
        return RetryDecision(False, "attempt_budget_exhausted")

    action_count = (
        session.query(ResolverAction)
        .filter(ResolverAction.case_id == case.id)
        .filter(ResolverAction.action_key == action_key)
        .filter(ResolverAction.status.in_(("applied", "failed")))
        .count()
    )
    if action_count >= action_limit(action_key):
        return RetryDecision(False, "action_budget_exhausted")

    if not diagnostic_only and evidence_hash is not None and case.last_attempted_evidence_hash == evidence_hash:
        return RetryDecision(False, "same_evidence_repeated")

    if (
        failure_hash is not None
        and case.last_failure_hash == failure_hash
        and case.last_action_type == action_key
        and case.last_action_status == "failed"
    ):
        return RetryDecision(False, "same_fix_failed_repeatedly")

    return RetryDecision(True, "allowed")
