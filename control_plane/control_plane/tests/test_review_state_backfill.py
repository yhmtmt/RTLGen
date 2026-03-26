from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from control_plane.clock import utcnow
from control_plane.db import create_all
from control_plane.models.enums import ExecutorType, FlowName, GitHubLinkState, LayerName, RunStatus, WorkItemState
from control_plane.models.github_links import GitHubLink
from control_plane.models.runs import Run
from control_plane.models.run_events import RunEvent
from control_plane.models.task_requests import TaskRequest
from control_plane.models.work_items import WorkItem
from control_plane.services.review_state_backfill import ReviewStateBackfillRequest, backfill_review_states


def _seed_item(session: Session, *, item_id: str, state: WorkItemState, with_pr: bool) -> WorkItem:
    task = TaskRequest(
        request_key=f"queue:{item_id}",
        source="test",
        requested_by="tester",
        title=item_id,
        description="backfill test",
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
        state=state,
        priority=1,
        input_manifest={},
        command_manifest=[],
        expected_outputs=[],
        acceptance_rules=[],
    )
    session.add(work_item)
    session.flush()
    run = Run(
        run_key=f"run-{item_id}",
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
    session.flush()
    if with_pr:
        session.add(
            GitHubLink(
                work_item_id=work_item.id,
                run_id=run.id,
                repo="yhmtmt/RTLGen",
                branch_name=f"eval/{item_id}/s20260326t000000z",
                pr_number=123,
                pr_url="https://github.com/yhmtmt/RTLGen/pull/123",
                state=GitHubLinkState.PR_OPEN,
                metadata_={},
            )
        )
    session.commit()
    return work_item


def test_backfill_review_states_moves_only_items_without_prs() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)
    with Session(engine) as session:
        _seed_item(session, item_id="stale_review", state=WorkItemState.AWAITING_REVIEW, with_pr=False)
        _seed_item(session, item_id="real_review", state=WorkItemState.AWAITING_REVIEW, with_pr=True)

        rows = backfill_review_states(session, ReviewStateBackfillRequest())
        assert [row.item_id for row in rows] == ["stale_review"]

        stale = session.query(WorkItem).filter_by(item_id="stale_review").one()
        real = session.query(WorkItem).filter_by(item_id="real_review").one()
        assert stale.state == WorkItemState.ARTIFACT_SYNC
        assert real.state == WorkItemState.AWAITING_REVIEW
        event = session.query(RunEvent).join(Run, RunEvent.run_id == Run.id).filter(Run.work_item_id == stale.id).one()
        assert event.event_type == "awaiting_review_backfilled"
