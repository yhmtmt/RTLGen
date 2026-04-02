"""Tests for the operator-facing live status summary."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path
import tempfile
from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from control_plane.clock import utcnow
from control_plane.db import build_session_factory, create_all
from control_plane.models.artifacts import Artifact
from control_plane.models.enums import (
    ArtifactStorageMode,
    ExecutorType,
    FlowName,
    GitHubLinkState,
    LayerName,
    LeaseStatus,
    RunStatus,
    WorkItemState,
)
from control_plane.models.github_links import GitHubLink
from control_plane.models.runs import Run
from control_plane.models.task_requests import TaskRequest
from control_plane.models.worker_leases import WorkerLease
from control_plane.models.worker_machines import WorkerMachine
from control_plane.models.run_events import RunEvent
from control_plane.models.work_items import WorkItem
from control_plane.services.operator_status import OperatorStatusRequest, load_operator_status


def _seed_item(
    session: Session,
    *,
    item_id: str,
    state: WorkItemState,
    task_type: str = "l1_sweep",
) -> WorkItem:
    task = TaskRequest(
        request_key=f"queue:{item_id}",
        source="test",
        requested_by="tester",
        title=item_id,
        description="status test",
        layer=LayerName.LAYER1,
        flow=FlowName.OPENROAD,
        priority=1,
        request_payload={"item_id": item_id},
    )
    session.add(task)
    session.flush()
    work_item = WorkItem(
        work_item_key=f"queue:{item_id}",
        task_request_id=task.id,
        item_id=item_id,
        layer=LayerName.LAYER1,
        flow=FlowName.OPENROAD,
        platform="nangate45",
        task_type=task_type,
        state=state,
        priority=1,
        input_manifest={},
        command_manifest=[],
        expected_outputs=[],
        acceptance_rules=[],
    )
    session.add(work_item)
    session.flush()
    return work_item


def test_operator_status_summarizes_live_state() -> None:
    with tempfile.TemporaryDirectory() as td:
        db_path = Path(td) / "cp.db"
        engine = create_engine(f"sqlite+pysqlite:///{db_path}", future=True)
        create_all(engine)
        now = utcnow()

        with Session(engine) as session:
            failed_item = _seed_item(session, item_id="failed_item", state=WorkItemState.FAILED)
            ready_item = _seed_item(session, item_id="ready_item", state=WorkItemState.READY)
            pending_item = _seed_item(session, item_id="pending_item", state=WorkItemState.ARTIFACT_SYNC)
            dispatch_item = _seed_item(session, item_id="dispatch_item", state=WorkItemState.DISPATCH_PENDING)
            review_item = _seed_item(session, item_id="review_item", state=WorkItemState.AWAITING_REVIEW)

            machine = WorkerMachine(
                machine_key="worker-1",
                hostname="eval-host",
                executor_kind="local_process",
                capabilities={},
                last_seen_at=now,
            )
            session.add(machine)
            session.flush()

            stale_lease = WorkerLease(
                work_item_id=ready_item.id,
                machine_id=machine.id,
                lease_token="lease-stale",
                status=LeaseStatus.ACTIVE,
                leased_at=now - timedelta(hours=1),
                expires_at=now - timedelta(minutes=5),
                last_heartbeat_at=now - timedelta(minutes=20),
            )
            session.add(stale_lease)
            session.flush()

            running_item = _seed_item(session, item_id="running_item", state=WorkItemState.RUNNING)
            active_lease = WorkerLease(
                work_item_id=running_item.id,
                machine_id=machine.id,
                lease_token="lease-active",
                status=LeaseStatus.ACTIVE,
                leased_at=now - timedelta(minutes=15),
                expires_at=now + timedelta(minutes=15),
                last_heartbeat_at=now - timedelta(seconds=10),
            )
            session.add(active_lease)
            session.flush()

            failed_run = Run(
                run_key="failed_run",
                work_item_id=failed_item.id,
                lease_id=stale_lease.id,
                attempt=1,
                executor_type=ExecutorType.INTERNAL_WORKER,
                machine_id=machine.id,
                checkout_commit="deadbeef",
                status=RunStatus.FAILED,
                started_at=now - timedelta(minutes=10),
                completed_at=now - timedelta(minutes=8),
                result_summary="command validate failed (exit_code=1)",
                result_payload={
                    "failure_classification": {"category": "validation_error"},
                    "failure_issue": {
                        "issue_number": 123,
                        "issue_url": "https://github.com/yhmtmt/RTLGen/issues/123",
                        "reported_utc": now.isoformat(),
                    },
                    "retry_decision": {"requeue": False},
                },
            )
            session.add(failed_run)
            session.flush()

            active_run = Run(
                run_key="running_run",
                work_item_id=running_item.id,
                lease_id=active_lease.id,
                attempt=1,
                executor_type=ExecutorType.INTERNAL_WORKER,
                machine_id=machine.id,
                checkout_commit="feedface",
                status=RunStatus.RUNNING,
                started_at=now - timedelta(minutes=3),
                result_payload={},
            )
            session.add(active_run)
            session.flush()

            submission_run = Run(
                run_key="review_run",
                work_item_id=review_item.id,
                attempt=1,
                executor_type=ExecutorType.INTERNAL_WORKER,
                machine_id=machine.id,
                checkout_commit="cafebabe",
                status=RunStatus.SUCCEEDED,
                started_at=now - timedelta(minutes=4),
                completed_at=now - timedelta(minutes=2),
                result_summary="4/4 commands succeeded",
                result_payload={},
            )
            session.add(submission_run)
            session.flush()

            session.add(
                Artifact(
                    run_id=submission_run.id,
                    kind="promotion_proposal",
                    storage_mode=ArtifactStorageMode.REPO,
                    path="control_plane/shadow_exports/l1_promotions/review_item.json",
                    sha256="abc",
                    metadata_={},
                )
            )
            session.add(
                GitHubLink(
                    work_item_id=review_item.id,
                    run_id=submission_run.id,
                    repo="yhmtmt/RTLGen",
                    branch_name="eval/review_item/s20260313t000000z",
                    pr_number=99,
                    pr_url="https://github.com/yhmtmt/RTLGen/pull/99",
                    state=GitHubLinkState.PR_OPEN,
                    metadata_={
                        "finalized_proposal_id": "prop_demo_v1",
                        "finalization_commit": "feedfacecafebeef",
                    },
                )
            )
            pending_run = Run(
                run_key="pending_run",
                work_item_id=pending_item.id,
                attempt=1,
                executor_type=ExecutorType.INTERNAL_WORKER,
                machine_id=machine.id,
                checkout_commit="deadfeed",
                status=RunStatus.SUCCEEDED,
                started_at=now - timedelta(minutes=6),
                completed_at=now - timedelta(minutes=5),
                result_summary="submission failed after completed run",
                result_payload={},
            )
            session.add(pending_run)
            pending_item.assigned_machine_key = machine.machine_key
            dispatch_item.assigned_machine_key = machine.machine_key
            session.commit()

        session_factory = build_session_factory(engine)
        with session_factory() as session:
            status = load_operator_status(session, OperatorStatusRequest(recent_limit=5))

        assert status.health_summary["status"] == "attention"
        assert "stale_leases=1" in str(status.health_summary["message"])
        assert "recent_failures=1" in str(status.health_summary["message"])
        assert "artifact_sync=1" in str(status.health_summary["message"])
        assert status.state_counts["failed"] == 1
        assert status.state_counts["ready"] == 1
        assert status.state_counts["artifact_sync"] == 1
        assert status.state_counts["dispatch_pending"] == 1
        assert status.state_counts["awaiting_review"] == 1
        assert status.state_counts["running"] == 1
        assert len(status.active_runs) == 1
        assert status.active_runs[0]["item_id"] == "running_item"
        assert status.active_runs[0]["worker_host"] == "eval-host"
        assert len(status.stale_leases) == 1
        assert status.stale_leases[0]["item_id"] == "ready_item"
        assert len(status.recent_failures) == 1
        assert len(status.dispatch_pending_items) == 1
        assert status.dispatch_pending_items[0]["item_id"] == "dispatch_item"
        assert status.dispatch_pending_items[0]["assigned_machine_key"] == "worker-1"
        assert len(status.pending_submission_items) == 1
        assert status.pending_submission_items[0]["item_id"] == "pending_item"
        assert len(status.recent_submissions) == 1
        assert status.recent_submissions[0]["finalization_status"] == "finalized"
        assert status.recent_submissions[0]["finalized_proposal_id"] == "prop_demo_v1"
        assert status.recent_submissions[0]["finalization_commit"] == "feedfacecafebeef"
        assert status.recent_failures[0]["item_id"] == "failed_item"
        assert status.recent_failures[0]["failure_category"] == "validation_error"
        assert status.recent_failures[0]["failure_issue_status"] == "reported"
        assert status.recent_failures[0]["failure_issue_number"] == 123
        assert len(status.recent_submissions) == 1
        assert status.recent_submissions[0]["item_id"] == "review_item"
        assert status.recent_submissions[0]["pr_number"] == 99


def test_operator_status_reports_evaluator_machine_capacity() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)
    with Session(engine) as session:
        from control_plane.services.lease_service import upsert_worker_machine
        machine = upsert_worker_machine(
            session,
            machine_key="worker-capacity",
            hostname="worker-capacity",
            role="evaluator",
            slot_capacity=4,
            capabilities={"platform": "nangate45", "flow": "openroad"},
        )
        task = TaskRequest(
            request_key="queue:assigned_ready",
            source="test",
            requested_by="tester",
            title="assigned ready",
            description="assigned ready",
            layer="layer2",
            flow="openroad",
            priority=1,
            request_payload={"item_id": "assigned_ready"},
        )
        session.add(task)
        session.flush()
        session.add(
            WorkItem(
                work_item_key="queue:assigned_ready",
                task_request_id=task.id,
                item_id="assigned_ready",
                layer="layer2",
                flow="openroad",
                platform="nangate45",
                task_type="l2_campaign",
                state=WorkItemState.READY,
                priority=1,
                input_manifest={},
                command_manifest=[],
                expected_outputs=[],
                acceptance_rules=[],
                assigned_machine_key=machine.machine_key,
            )
        )
        session.commit()

        status = load_operator_status(session, OperatorStatusRequest(recent_limit=5))
        row = next(r for r in status.evaluator_machines if r["machine_key"] == "worker-capacity")
        assert row["slot_capacity"] == 4
        assert row["assigned_ready"] == 1
        assert row["active_slots"] == 0


def test_operator_status_marks_resumable_pending_submission(monkeypatch) -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)
    now = utcnow()
    with Session(engine) as session:
        pending_item = _seed_item(session, item_id="pending_item", state=WorkItemState.ARTIFACT_SYNC)
        machine = WorkerMachine(
            machine_key="worker-1",
            hostname="eval-host",
            executor_kind="local_process",
            capabilities={},
            last_seen_at=now,
        )
        session.add(machine)
        session.flush()
        session.add(
            Run(
                run_key="pending_run",
                work_item_id=pending_item.id,
                attempt=1,
                executor_type=ExecutorType.INTERNAL_WORKER,
                machine_id=machine.id,
                checkout_commit="deadfeed",
                status=RunStatus.SUCCEEDED,
                started_at=now - timedelta(minutes=2),
                completed_at=now - timedelta(minutes=1),
                result_summary="submission failed after completed run",
                result_payload={},
            )
        )
        session.commit()

        monkeypatch.setattr(
            "control_plane.services.operator_status.assess_submission_eligibility",
            lambda *args, **kwargs: SimpleNamespace(eligible=False, reason="gh pr create failed after branch push"),
        )

        status = load_operator_status(session, OperatorStatusRequest(recent_limit=5))

    assert len(status.pending_submission_items) == 1
    assert status.pending_submission_items[0]["item_id"] == "pending_item"
    assert status.pending_submission_items[0]["resumable"] is True
    assert status.pending_submission_items[0]["resume_requested"] is False
    assert status.pending_submission_items[0]["reason"] == "gh pr create failed after branch push"


def test_operator_status_marks_resume_requested_pending_submission(monkeypatch) -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)
    now = utcnow()
    with Session(engine) as session:
        pending_item = _seed_item(session, item_id="pending_item", state=WorkItemState.ARTIFACT_SYNC)
        machine = WorkerMachine(
            machine_key="worker-1",
            hostname="eval-host",
            executor_kind="local_process",
            capabilities={},
            last_seen_at=now,
        )
        session.add(machine)
        session.flush()
        run = Run(
            run_key="pending_run",
            work_item_id=pending_item.id,
            attempt=1,
            executor_type=ExecutorType.INTERNAL_WORKER,
            machine_id=machine.id,
            checkout_commit="deadfeed",
            status=RunStatus.SUCCEEDED,
            started_at=now - timedelta(minutes=2),
            completed_at=now - timedelta(minutes=1),
            result_summary="submission failed after completed run",
            result_payload={},
        )
        session.add(run)
        session.flush()
        session.add(
            RunEvent(
                run_id=run.id,
                event_time=now,
                event_type="submission_retry_requested",
                event_payload={"request_id": "resume_123", "target_machine_key": machine.machine_key},
            )
        )
        session.commit()

        monkeypatch.setattr(
            "control_plane.services.operator_status.assess_submission_eligibility",
            lambda *args, **kwargs: SimpleNamespace(eligible=False, reason="gh pr create failed after branch push"),
        )

        status = load_operator_status(session, OperatorStatusRequest(recent_limit=5))

    assert len(status.pending_submission_items) == 1
    assert status.pending_submission_items[0]["item_id"] == "pending_item"
    assert status.pending_submission_items[0]["resumable"] is False
    assert status.pending_submission_items[0]["resume_requested"] is True
