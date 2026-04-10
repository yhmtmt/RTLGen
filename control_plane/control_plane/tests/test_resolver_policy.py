"""Tests for resolver policy budgets."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from control_plane.db import create_all
from control_plane.models.resolver_actions import ResolverAction
from control_plane.models.resolver_cases import ResolverCase
from control_plane.services.resolver_policy import retry_allowed


def make_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)
    return Session(engine)


def _case() -> ResolverCase:
    return ResolverCase(
        fingerprint="orphaned_running_item:command_progress",
        failure_class="orphaned_running_item",
        owner="eval",
        status="open",
        severity="high",
        evidence_json={},
        resolution_json={},
        attempt_count=0,
        max_attempts=3,
        last_evidence_hash="hash-1",
    )


def test_retry_allowed_blocks_same_evidence_for_non_diagnostic_action() -> None:
    with make_session() as session:
        case = _case()
        case.last_attempted_evidence_hash = "hash-1"
        session.add(case)
        session.commit()

        decision = retry_allowed(session, case, action_key="open_issue", evidence_hash="hash-1")

    assert decision.allowed is False
    assert decision.reason == "same_evidence_repeated"


def test_retry_allowed_allows_diagnostic_comment_on_same_evidence() -> None:
    with make_session() as session:
        case = _case()
        case.last_attempted_evidence_hash = "hash-1"
        session.add(case)
        session.commit()

        decision = retry_allowed(
            session,
            case,
            action_key="comment_issue",
            evidence_hash="hash-1",
            diagnostic_only=True,
        )

    assert decision.allowed is True


def test_retry_allowed_blocks_after_action_budget_exhausted() -> None:
    with make_session() as session:
        case = _case()
        session.add(case)
        session.flush()
        session.add(
            ResolverAction(
                case_id=case.id,
                actor="dev",
                action_type="open_issue",
                action_key="open_issue",
                status="applied",
                attempt_index=1,
                evidence_hash="hash-1",
                failure_hash=None,
                idempotency_key="k1",
                request_json={},
                result_json={},
            )
        )
        session.commit()

        decision = retry_allowed(session, case, action_key="open_issue", evidence_hash="hash-2")

    assert decision.allowed is False
    assert decision.reason == "action_budget_exhausted"
