"""Tests for the dev-side resolver daemon."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError

from control_plane.services.resolver_issue_bridge import ResolverIssueBridgeCommandError, ResolverIssueCreateResult
from sqlalchemy.orm import Session

from control_plane.clock import utcnow
from control_plane.db import build_session_factory, create_all
from control_plane.models.enums import ExecutorType, FlowName, LayerName, LeaseStatus, RunStatus, WorkItemState
from control_plane.models.resolver_actions import ResolverAction
from control_plane.models.resolver_cases import ResolverCase
from control_plane.models.resolver_observations import ResolverObservation
from control_plane.models.run_events import RunEvent
from control_plane.models.runs import Run
from control_plane.models.task_requests import TaskRequest
from control_plane.models.work_items import WorkItem
from control_plane.models.worker_leases import WorkerLease
from control_plane.models.worker_machines import WorkerMachine
from control_plane.services.resolver_dev_daemon import ResolverDevDaemonConfig, run_dev_resolver


def _seed_orphaned_running_item(engine) -> None:
    now = utcnow()
    with Session(engine) as session:
        task = TaskRequest(
            request_key="queue:test-orphan",
            source="test",
            requested_by="tester",
            title="test orphan",
            description="detect stuck run",
            layer=LayerName.LAYER1,
            flow=FlowName.OPENROAD,
            priority=1,
            request_payload={"item_id": "orphan-item"},
        )
        session.add(task)
        session.flush()
        work_item = WorkItem(
            work_item_key="queue:test-orphan",
            task_request_id=task.id,
            item_id="orphan-item",
            layer=LayerName.LAYER1,
            flow=FlowName.OPENROAD,
            platform="nangate45",
            task_type="l1_sweep",
            state=WorkItemState.RUNNING,
            priority=1,
            input_manifest={},
            command_manifest=[],
            expected_outputs=[],
            acceptance_rules=[],
            source_commit="deadbeef",
        )
        session.add(work_item)
        machine = WorkerMachine(
            machine_key="eval-1",
            hostname="eval-host",
            executor_kind="local_process",
            capabilities={},
        )
        session.add(machine)
        session.flush()
        lease = WorkerLease(
            work_item_id=work_item.id,
            machine_id=machine.id,
            lease_token="lease-1",
            status=LeaseStatus.ACTIVE,
            leased_at=now - timedelta(hours=1),
            expires_at=now - timedelta(minutes=30),
            last_heartbeat_at=now - timedelta(minutes=35),
        )
        session.add(lease)
        session.flush()
        run = Run(
            run_key="run-1",
            work_item_id=work_item.id,
            lease_id=lease.id,
            attempt=1,
            executor_type=ExecutorType.INTERNAL_WORKER,
            machine_id=machine.id,
            status=RunStatus.RUNNING,
            started_at=now - timedelta(hours=1),
            result_payload={},
        )
        session.add(run)
        session.flush()
        session.add(
            RunEvent(
                run_id=run.id,
                event_time=now - timedelta(minutes=31),
                event_type="command_progress",
                event_payload={"command": "run_sweep"},
            )
        )
        session.commit()


def _seed_blocked_submission_item(engine, *, submission_failed_reason: str | None = None) -> None:
    now = utcnow()
    with Session(engine) as session:
        task = TaskRequest(
            request_key="queue:test-blocked",
            source="test",
            requested_by="tester",
            title="test blocked",
            description="detect blocked submission",
            layer=LayerName.LAYER1,
            flow=FlowName.OPENROAD,
            priority=1,
            request_payload={
                "item_id": "blocked-item",
                "developer_loop": {"proposal_id": "prop_missing_seedvariance_v1"},
            },
        )
        session.add(task)
        session.flush()
        work_item = WorkItem(
            work_item_key="queue:test-blocked",
            task_request_id=task.id,
            item_id="blocked-item",
            layer=LayerName.LAYER1,
            flow=FlowName.OPENROAD,
            platform="nangate45",
            task_type="l1_sweep",
            state=WorkItemState.ARTIFACT_SYNC,
            priority=1,
            input_manifest={},
            command_manifest=[],
            expected_outputs=[],
            acceptance_rules=[],
            source_commit="cafefeed",
            assigned_machine_key="eval-1",
        )
        session.add(work_item)
        session.flush()
        run = Run(
            run_key="run-blocked",
            work_item_id=work_item.id,
            attempt=1,
            executor_type=ExecutorType.INTERNAL_WORKER,
            status=RunStatus.SUCCEEDED,
            started_at=now - timedelta(hours=1),
            completed_at=now - timedelta(minutes=30),
            result_payload={},
        )
        session.add(run)
        session.flush()
        if submission_failed_reason:
            session.add(
                RunEvent(
                    run_id=run.id,
                    event_time=now - timedelta(minutes=10),
                    event_type="submission_failed",
                    event_payload={"error": submission_failed_reason},
                )
            )
        session.commit()


def test_dev_resolver_opens_issue_once_for_same_evidence() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)
    _seed_orphaned_running_item(engine)

    session_factory = build_session_factory(engine)
    with patch(
        "control_plane.services.resolver_dev_daemon.fetch_issue",
        return_value=type("Issue", (), {"state": "open"})(),
    ) as fetch_issue_mock, patch(
        "control_plane.services.resolver_dev_daemon.open_issue_for_case",
        return_value=ResolverIssueCreateResult(issue_number=175, issue_url="https://github.com/yhmtmt/RTLGen/issues/175"),
    ) as open_issue_mock, patch(
        "control_plane.services.resolver_dev_daemon.comment_issue_for_case"
    ) as comment_mock, patch(
        "control_plane.services.resolver_dev_daemon.time.sleep"
    ):
        result = run_dev_resolver(
            session_factory,
            ResolverDevDaemonConfig(
                repo="yhmtmt/RTLGen",
                repo_root="/repo",
                poll_seconds=0,
                max_polls=2,
            ),
        )

    with Session(engine) as session:
        cases = session.query(ResolverCase).all()

    assert result.poll_count == 2
    assert result.detection_count == 2
    assert result.opened_issue_count == 1
    assert result.updated_issue_count == 0
    assert fetch_issue_mock.call_count >= 1
    assert open_issue_mock.call_count == 1
    assert comment_mock.call_count == 0
    assert len(cases) == 1
    assert cases[0].issue_number == 175
    assert cases[0].status == "awaiting_remote"


def test_dev_resolver_does_not_open_issue_within_orphaned_stale_grace() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)
    _seed_orphaned_running_item(engine)

    with Session(engine) as session:
        lease = session.query(WorkerLease).one()
        lease.expires_at = utcnow() - timedelta(seconds=30)
        lease.last_heartbeat_at = utcnow() - timedelta(minutes=2)
        event = session.query(RunEvent).one()
        event.event_type = "command_started"
        event.event_time = utcnow() - timedelta(minutes=1)
        session.commit()

    session_factory = build_session_factory(engine)
    with patch(
        "control_plane.services.resolver_dev_daemon.open_issue_for_case",
        return_value=ResolverIssueCreateResult(issue_number=999, issue_url="https://github.com/yhmtmt/RTLGen/issues/999"),
    ) as open_issue_mock, patch(
        "control_plane.services.resolver_dev_daemon.time.sleep"
    ):
        result = run_dev_resolver(
            session_factory,
            ResolverDevDaemonConfig(
                repo="yhmtmt/RTLGen",
                repo_root="/repo",
                poll_seconds=0,
                max_polls=1,
                orphaned_stale_grace_seconds=600,
            ),
        )

    with Session(engine) as session:
        cases = session.query(ResolverCase).all()

    assert result.detection_count == 0
    assert result.opened_issue_count == 0
    assert open_issue_mock.call_count == 0
    assert cases == []


def test_dev_resolver_opens_new_issue_when_existing_linked_issue_is_closed() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)
    _seed_orphaned_running_item(engine)

    with Session(engine) as session:
        case = ResolverCase(
            id="case-closed",
            fingerprint="orphaned_running_item:command_progress",
            failure_class="orphaned_running_item",
            owner="eval",
            status="awaiting_remote",
            severity="high",
            issue_number=184,
            first_item_id="old-item",
            latest_item_id="old-item",
            first_run_key="old-run",
            latest_run_key="old-run",
            machine_key="eval-1",
            source_commit="deadbeef",
            repo_root="/repo",
            evidence_json={"item_id": "old-item", "latest_event_type": "command_progress"},
            resolution_json={},
            last_evidence_hash="oldhash",
        )
        session.add(case)
        session.commit()

    session_factory = build_session_factory(engine)
    with patch(
        "control_plane.services.resolver_dev_daemon.fetch_issue",
        return_value=type("Issue", (), {"state": "closed"})(),
    ) as fetch_issue_mock, patch(
        "control_plane.services.resolver_dev_daemon.open_issue_for_case",
        return_value=ResolverIssueCreateResult(issue_number=186, issue_url="https://github.com/yhmtmt/RTLGen/issues/186"),
    ) as open_issue_mock, patch(
        "control_plane.services.resolver_dev_daemon.comment_issue_for_case"
    ) as comment_mock, patch(
        "control_plane.services.resolver_dev_daemon.time.sleep"
    ):
        result = run_dev_resolver(
            session_factory,
            ResolverDevDaemonConfig(
                repo="yhmtmt/RTLGen",
                repo_root="/repo",
                poll_seconds=0,
                max_polls=1,
                orphaned_stale_grace_seconds=0,
            ),
        )

    with Session(engine) as session:
        cases = session.query(ResolverCase).order_by(ResolverCase.created_at.asc()).all()

    assert result.opened_issue_count == 1
    assert fetch_issue_mock.call_count == 1
    assert open_issue_mock.call_count == 1
    assert comment_mock.call_count == 0
    assert len(cases) == 2
    assert cases[0].status == "resolved"
    assert cases[1].issue_number == 186
    assert cases[1].latest_item_id == "orphan-item"


def test_dev_resolver_opens_issue_for_blocked_submission() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)
    _seed_blocked_submission_item(engine)

    session_factory = build_session_factory(engine)
    with patch(
        "control_plane.services.resolver_dev_daemon.open_issue_for_case",
        return_value=ResolverIssueCreateResult(issue_number=176, issue_url="https://github.com/yhmtmt/RTLGen/issues/176"),
    ) as open_issue_mock, patch(
        "control_plane.services.resolver_dev_daemon.comment_issue_for_case"
    ) as comment_mock, patch(
        "control_plane.services.resolver_dev_daemon.time.sleep"
    ):
        result = run_dev_resolver(
            session_factory,
            ResolverDevDaemonConfig(
                repo="yhmtmt/RTLGen",
                repo_root="/repo",
                poll_seconds=0,
                max_polls=1,
            ),
        )

    with Session(engine) as session:
        case = session.query(ResolverCase).one()

    assert result.detection_count == 1
    assert result.opened_issue_count == 1
    assert result.updated_issue_count == 0
    assert open_issue_mock.call_count == 1
    assert comment_mock.call_count == 0
    assert case.failure_class == "artifact_sync_blocked_submission"
    assert case.owner == "dev"
    assert case.fingerprint == "artifact_sync_blocked_submission:proposal_linkage_unresolved"
    assert case.issue_number == 176
    assert case.status == "awaiting_remote"


def test_dev_resolver_applies_expire_stale_lease_from_diagnosis() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)
    _seed_orphaned_running_item(engine)

    with Session(engine) as session:
        case = ResolverCase(
            id="case-1",
            fingerprint="orphaned_running_item:command_progress",
            failure_class="orphaned_running_item",
            owner="eval",
            status="awaiting_remote",
            severity="high",
            issue_number=175,
            first_item_id="orphan-item",
            latest_item_id="orphan-item",
            first_run_key="run-1",
            latest_run_key="run-1",
            machine_key="eval-1",
            source_commit="deadbeef",
            repo_root="/repo",
            evidence_json={"item_id": "orphan-item", "latest_event_type": "command_progress"},
            resolution_json={},
        )
        session.add(case)
        session.flush()
        session.add(
            ResolverObservation(
                case_id=case.id,
                source="github",
                kind="diagnosis",
                summary="issue #175 diagnosis synced",
                payload_json={
                    "issue_number": 175,
                    "comment_id": 10,
                    "diagnosis_hash": "diag-1",
                    "diagnosis": {
                        "verdict": "worker died during finalize",
                        "failure_point": "complete_run",
                        "recommended_action": "expire_stale_leases",
                    },
                },
            )
        )
        session.commit()

    session_factory = build_session_factory(engine)
    with patch(
        "control_plane.services.resolver_dev_daemon.fetch_issue",
        return_value=type("Issue", (), {"state": "open"})(),
    ) as fetch_issue_mock, patch("control_plane.services.resolver_dev_daemon.open_issue_for_case") as open_issue_mock, patch(
        "control_plane.services.resolver_dev_daemon.comment_issue_for_case"
    ) as comment_mock, patch("control_plane.services.resolver_dev_daemon.time.sleep"):
        result = run_dev_resolver(
            session_factory,
            ResolverDevDaemonConfig(
                repo="yhmtmt/RTLGen",
                repo_root="/repo",
                poll_seconds=0,
                max_polls=1,
            ),
        )

    with Session(engine) as session:
        case = session.query(ResolverCase).filter(ResolverCase.id == "case-1").one()
        lease = session.query(WorkerLease).filter(WorkerLease.lease_token == "lease-1").one()
        actions = session.query(ResolverAction).order_by(ResolverAction.created_at.asc()).all()
        work_item = session.query(WorkItem).filter(WorkItem.item_id == "orphan-item").one()

    assert result.poll_count == 1
    assert result.detection_count == 1
    assert result.opened_issue_count == 0
    assert result.updated_issue_count == 1
    assert fetch_issue_mock.call_count == 1
    assert fetch_issue_mock.call_count == 1
    assert open_issue_mock.call_count == 0
    assert comment_mock.call_count == 1
    assert case.status == "awaiting_retry"
    assert lease.status == LeaseStatus.EXPIRED
    assert work_item.state == WorkItemState.DISPATCH_PENDING
    assert [action.action_key for action in actions] == ["expire_stale_lease", "comment_issue"]


def test_dev_resolver_applies_retry_submission_from_diagnosis() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)
    _seed_blocked_submission_item(engine, submission_failed_reason="gh pr create failed: exit code 4")

    with Session(engine) as session:
        case = ResolverCase(
            id="case-2",
            fingerprint="artifact_sync_blocked_submission:gh_pr_create_failed",
            failure_class="artifact_sync_blocked_submission",
            owner="eval",
            status="awaiting_remote",
            severity="medium",
            issue_number=178,
            first_item_id="blocked-item",
            latest_item_id="blocked-item",
            first_run_key="run-blocked",
            latest_run_key="run-blocked",
            machine_key="eval-1",
            source_commit="cafefeed",
            repo_root="/repo",
            evidence_json={"item_id": "blocked-item", "eligibility_reason": "gh pr create failed: exit code 4"},
            resolution_json={},
        )
        session.add(case)
        session.flush()
        session.add(
            ResolverObservation(
                case_id=case.id,
                source="github",
                kind="diagnosis",
                summary="issue #178 diagnosis synced",
                payload_json={
                    "issue_number": 178,
                    "comment_id": 20,
                    "diagnosis_hash": "diag-2",
                    "diagnosis": {
                        "verdict": "gh auth was missing and is now restored",
                        "failure_point": "gh_pr_create",
                        "recommended_action": "retry_submission",
                    },
                },
            )
        )
        session.commit()

    session_factory = build_session_factory(engine)
    with patch(
        "control_plane.services.resolver_dev_daemon.fetch_issue",
        return_value=type("Issue", (), {"state": "open"})(),
    ) as fetch_issue_mock, patch("control_plane.services.resolver_dev_daemon.open_issue_for_case") as open_issue_mock, patch(
        "control_plane.services.resolver_dev_daemon.comment_issue_for_case"
    ) as comment_mock, patch("control_plane.services.resolver_dev_daemon.time.sleep"):
        result = run_dev_resolver(
            session_factory,
            ResolverDevDaemonConfig(
                repo="yhmtmt/RTLGen",
                repo_root="/repo",
                poll_seconds=0,
                max_polls=1,
            ),
        )

    with Session(engine) as session:
        case = session.query(ResolverCase).filter(ResolverCase.id == "case-2").one()
        actions = session.query(ResolverAction).filter(ResolverAction.case_id == case.id).order_by(ResolverAction.created_at.asc()).all()
        run = session.query(Run).filter(Run.run_key == "run-blocked").one()
        retry_events = (
            session.query(RunEvent)
            .filter(RunEvent.run_id == run.id, RunEvent.event_type == "submission_retry_requested")
            .order_by(RunEvent.event_time.asc())
            .all()
        )

    assert result.poll_count == 1
    assert result.detection_count == 1
    assert result.opened_issue_count == 0
    assert result.updated_issue_count == 1
    assert open_issue_mock.call_count == 0
    assert comment_mock.call_count == 1
    assert case.status == "awaiting_retry"
    assert len(retry_events) == 1
    assert retry_events[0].event_payload["actor"] == "resolver_dev_daemon"
    assert [action.action_key for action in actions] == ["retry_submission", "comment_issue"]


def test_dev_resolver_continues_after_retryable_db_error() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)
    session_factory = build_session_factory(engine)
    log_messages: list[str] = []

    with patch(
        "control_plane.services.resolver_dev_daemon._collect_detections",
        side_effect=[
            OperationalError("select 1", {}, Exception("db down")),
            [],
        ],
    ) as collect_mock, patch(
        "control_plane.services.resolver_dev_daemon._reconcile_closed_remote_issues"
    ), patch(
        "control_plane.services.resolver_dev_daemon.time.sleep"
    ), patch.object(engine, "dispose") as dispose_mock:
        result = run_dev_resolver(
            session_factory,
            ResolverDevDaemonConfig(repo="yhmtmt/RTLGen", repo_root="/repo", poll_seconds=0, max_polls=2),
            log_fn=log_messages.append,
        )

    assert result.poll_count == 2
    assert result.detection_count == 0
    assert collect_mock.call_count == 2
    assert dispose_mock.call_count == 1
    assert any("resolver-dev db_unavailable" in message for message in log_messages)


def test_dev_resolver_continues_after_retryable_github_error() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)
    _seed_orphaned_running_item(engine)
    session_factory = build_session_factory(engine)
    log_messages: list[str] = []

    with patch(
        "control_plane.services.resolver_dev_daemon.fetch_issue",
        side_effect=[ResolverIssueBridgeCommandError("gh api failed"), type("Issue", (), {"state": "open"})()],
    ) as fetch_mock, patch(
        "control_plane.services.resolver_dev_daemon.time.sleep"
    ), patch.object(engine, "dispose") as dispose_mock:
        result = run_dev_resolver(
            session_factory,
            ResolverDevDaemonConfig(repo="yhmtmt/RTLGen", repo_root="/repo", poll_seconds=0, max_polls=2),
            log_fn=log_messages.append,
        )

    assert result.poll_count == 2
    assert fetch_mock.call_count >= 1
    assert dispose_mock.call_count == 1
    assert any("resolver-dev db_unavailable" in message for message in log_messages)
