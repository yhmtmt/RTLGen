"""Tests for the dev-side resolver daemon."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from control_plane.clock import utcnow
from control_plane.db import build_session_factory, create_all
from control_plane.models.enums import ExecutorType, FlowName, LayerName, LeaseStatus, RunStatus, WorkItemState
from control_plane.models.resolver_actions import ResolverAction
from control_plane.models.resolver_cases import ResolverCase
from control_plane.models.resolver_observations import ResolverObservation
from control_plane.models.task_requests import TaskRequest
from control_plane.models.work_items import WorkItem
from control_plane.models.worker_leases import WorkerLease
from control_plane.models.worker_machines import WorkerMachine
from control_plane.models.runs import Run
from control_plane.models.run_events import RunEvent
from control_plane.services.resolver_dev_daemon import ResolverDevDaemonConfig, run_dev_resolver
from control_plane.services.resolver_issue_bridge import ResolverIssueCreateResult


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


def test_dev_resolver_opens_issue_once_for_same_evidence() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)
    _seed_orphaned_running_item(engine)

    session_factory = build_session_factory(engine)
    with patch(
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
    assert open_issue_mock.call_count == 1
    assert comment_mock.call_count == 0
    assert len(cases) == 1
    assert cases[0].issue_number == 175
    assert cases[0].status == "awaiting_remote"


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
    with patch("control_plane.services.resolver_dev_daemon.open_issue_for_case") as open_issue_mock, patch(
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
    assert open_issue_mock.call_count == 0
    assert comment_mock.call_count == 1
    assert case.status == "awaiting_retry"
    assert lease.status == LeaseStatus.EXPIRED
    assert work_item.state == WorkItemState.DISPATCH_PENDING
    assert [action.action_key for action in actions] == ["expire_stale_lease", "comment_issue"]
