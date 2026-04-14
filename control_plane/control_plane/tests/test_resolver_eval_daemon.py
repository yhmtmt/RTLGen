"""Tests for the eval-side resolver daemon."""

from __future__ import annotations

from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from control_plane.db import build_session_factory, create_all
from control_plane.models.resolver_cases import ResolverCase
from control_plane.models.resolver_observations import ResolverObservation
from control_plane.services.resolver_eval_daemon import ResolverEvalDaemonConfig, run_eval_resolver
from control_plane.services.resolver_issue_bridge import ResolverIssueComment, ResolverRemoteIssue


def test_eval_resolver_records_issue_snapshot_and_diagnosis_once_for_same_issue_state() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)
    with Session(engine) as session:
        session.add(
            ResolverCase(
                id="case-1",
                fingerprint="orphaned_running_item:command_progress",
                failure_class="orphaned_running_item",
                owner="eval",
                status="awaiting_remote",
                severity="high",
                issue_number=175,
                first_item_id="item-1",
                latest_item_id="item-1",
                first_run_key="run-1",
                latest_run_key="run-1",
                machine_key="eval-1",
                evidence_json={"item_id": "item-1"},
                resolution_json={},
            )
        )
        session.commit()

    issue = ResolverRemoteIssue(
        issue_number=175,
        title="Resolver: orphaned_running_item [item-1]",
        body="""<!-- resolver-case
case_id: case-1
owner: eval
machine_key: eval-1
-->""",
        state="open",
        issue_url="https://github.com/yhmtmt/RTLGen/issues/175",
        updated_at="2026-04-10T12:00:00Z",
        case_metadata={"case_id": "case-1", "owner": "eval", "machine_key": "eval-1"},
        comments=(
            ResolverIssueComment(
                comment_id=10,
                body="""<!-- resolver-diagnosis
verdict: worker died during finalize
failure_point: complete_run
recommended_action: expire_stale_leases
-->""",
                author="eval-bot",
                created_at="2026-04-10T12:05:00Z",
                updated_at="2026-04-10T12:05:00Z",
            ),
        ),
    )

    session_factory = build_session_factory(engine)
    with patch(
        "control_plane.services.resolver_eval_daemon.list_open_resolver_issues",
        return_value=(issue,),
    ), patch("control_plane.services.resolver_eval_daemon.time.sleep"):
        result = run_eval_resolver(
            session_factory,
            ResolverEvalDaemonConfig(
                repo="yhmtmt/RTLGen",
                machine_key="eval-1",
                poll_seconds=0,
                max_polls=2,
            ),
        )

    with Session(engine) as session:
        observations = session.query(ResolverObservation).order_by(ResolverObservation.kind.asc()).all()

    assert result.poll_count == 2
    assert result.issue_count == 2
    assert result.observation_count == 2
    assert len(observations) == 2
    assert {observation.kind for observation in observations} == {"diagnosis", "issue_snapshot"}


def test_eval_resolver_continues_after_retryable_db_error() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)
    with Session(engine) as session:
        session.add(
            ResolverCase(
                id="case-1",
                fingerprint="orphaned_running_item:command_progress",
                failure_class="orphaned_running_item",
                owner="eval",
                status="awaiting_remote",
                severity="high",
                issue_number=175,
                first_item_id="item-1",
                latest_item_id="item-1",
                first_run_key="run-1",
                latest_run_key="run-1",
                machine_key="eval-1",
                evidence_json={"item_id": "item-1"},
                resolution_json={},
            )
        )
        session.commit()

    issue = ResolverRemoteIssue(
        issue_number=175,
        title="Resolver: orphaned_running_item [item-1]",
        body="""<!-- resolver-case
case_id: case-1
owner: eval
machine_key: eval-1
-->""",
        state="open",
        issue_url="https://github.com/yhmtmt/RTLGen/issues/175",
        updated_at="2026-04-10T12:00:00Z",
        case_metadata={"case_id": "case-1", "owner": "eval", "machine_key": "eval-1"},
        comments=(),
    )

    session_factory = build_session_factory(engine)
    log_messages: list[str] = []
    with patch(
        "control_plane.services.resolver_eval_daemon.list_open_resolver_issues",
        return_value=(issue,),
    ), patch(
        "control_plane.services.resolver_eval_daemon._sync_issue_snapshot",
        side_effect=[OperationalError("select 1", {}, Exception("db down")), False],
    ) as snapshot_mock, patch(
        "control_plane.services.resolver_eval_daemon.time.sleep"
    ), patch.object(engine, "dispose") as dispose_mock:
        result = run_eval_resolver(
            session_factory,
            ResolverEvalDaemonConfig(repo="yhmtmt/RTLGen", machine_key="eval-1", poll_seconds=0, max_polls=2),
            log_fn=log_messages.append,
        )

    assert result.poll_count == 2
    assert result.issue_count == 2
    assert result.observation_count == 0
    assert snapshot_mock.call_count == 2
    assert dispose_mock.call_count == 1
    assert any("resolver-eval db_unavailable" in message for message in log_messages)
