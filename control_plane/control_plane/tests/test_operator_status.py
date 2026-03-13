"""Tests for the operator-facing live status summary."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path
import tempfile

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
                    "retry_decision": {"requeue": False},
                },
            )
            session.add(failed_run)
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
                    metadata_={},
                )
            )
            session.commit()

        session_factory = build_session_factory(engine)
        with session_factory() as session:
            status = load_operator_status(session, OperatorStatusRequest(recent_limit=5))

        assert status.state_counts["failed"] == 1
        assert status.state_counts["ready"] == 1
        assert status.state_counts["awaiting_review"] == 1
        assert len(status.stale_leases) == 1
        assert status.stale_leases[0]["item_id"] == "ready_item"
        assert len(status.recent_failures) == 1
        assert status.recent_failures[0]["item_id"] == "failed_item"
        assert status.recent_failures[0]["failure_category"] == "validation_error"
        assert len(status.recent_submissions) == 1
        assert status.recent_submissions[0]["item_id"] == "review_item"
        assert status.recent_submissions[0]["pr_number"] == 99
