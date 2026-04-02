"""Tests for evaluator-side submission retry queueing and claim semantics."""

from __future__ import annotations

import tempfile
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from control_plane.clock import utcnow
from control_plane.db import create_all
from control_plane.models.enums import ExecutorType, FlowName, LayerName, RunStatus, WorkItemState
from control_plane.models.run_events import RunEvent
from control_plane.models.runs import Run
from control_plane.models.task_requests import TaskRequest
from control_plane.models.work_items import WorkItem
from control_plane.services.completion_retry_service import claim_submission_retry, request_submission_retry, submission_retry_status


def _seed_retryable_item(session: Session, *, item_id: str = "retry_item") -> tuple[WorkItem, Run]:
    task = TaskRequest(
        request_key=f"queue:{item_id}",
        source="test",
        requested_by="tester",
        title=item_id,
        description="retry test",
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
        task_type="l1_sweep",
        state=WorkItemState.ARTIFACT_SYNC,
        priority=1,
        input_manifest={},
        command_manifest=[],
        expected_outputs=["runs/index.csv"],
        acceptance_rules=[],
        assigned_machine_key="eval-a",
    )
    session.add(work_item)
    session.flush()

    run = Run(
        run_key=f"{item_id}_run_1",
        work_item_id=work_item.id,
        attempt=1,
        executor_type=ExecutorType.INTERNAL_WORKER,
        status=RunStatus.SUCCEEDED,
        started_at=utcnow(),
        completed_at=utcnow(),
        result_summary="ok",
        result_payload={},
    )
    session.add(run)
    session.commit()
    return work_item, run


def test_claim_submission_retry_only_claims_once_per_request() -> None:
    with tempfile.TemporaryDirectory() as td:
        db_path = Path(td) / "cp.db"
        engine = create_engine(f"sqlite+pysqlite:///{db_path}", future=True)
        create_all(engine)

        with Session(engine) as session:
            work_item, run = _seed_retryable_item(session)
            request = request_submission_retry(session, item_id=work_item.item_id, actor="dashboard", force=True)
            status = submission_retry_status(session, work_item=work_item, run=run)
            assert status.requested is True
            assert status.request_id == request.request_id

        with Session(engine) as session:
            claim = claim_submission_retry(session, machine_key="eval-a")
            assert claim is not None
            assert claim.request_id == request.request_id

        with Session(engine) as session:
            second_claim = claim_submission_retry(session, machine_key="eval-a")
            assert second_claim is None
            work_item = session.query(WorkItem).filter_by(item_id="retry_item").one()
            run = session.query(Run).filter_by(run_key="retry_item_run_1").one()
            status = submission_retry_status(session, work_item=work_item, run=run)
            assert status.requested is True
            duplicate = request_submission_retry(session, item_id=work_item.item_id, actor="dashboard", force=True)
            assert duplicate.already_requested is True
            assert duplicate.request_id == request.request_id

        with Session(engine) as session:
            run = session.query(Run).filter_by(run_key="retry_item_run_1").one()
            session.add(
                RunEvent(
                    run_id=run.id,
                    event_time=utcnow(),
                    event_type="submission_retry_processed",
                    event_payload={"request_id": request.request_id, "submitted": False},
                )
            )
            session.commit()

        with Session(engine) as session:
            work_item = session.query(WorkItem).filter_by(item_id="retry_item").one()
            run = session.query(Run).filter_by(run_key="retry_item_run_1").one()
            status = submission_retry_status(session, work_item=work_item, run=run)
            assert status.requested is False
