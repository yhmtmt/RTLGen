"""Backfill stale awaiting_review items that never got a PR."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Session

from control_plane.clock import utcnow
from control_plane.models.enums import GitHubLinkState, RunStatus, WorkItemState
from control_plane.models.github_links import GitHubLink
from control_plane.models.run_events import RunEvent
from control_plane.models.work_items import WorkItem

_TERMINAL_RUN_STATES = {RunStatus.SUCCEEDED, RunStatus.FAILED, RunStatus.CANCELED, RunStatus.TIMED_OUT}


@dataclass(frozen=True)
class ReviewStateBackfillRequest:
    item_id: str | None = None


@dataclass(frozen=True)
class ReviewStateBackfillRow:
    item_id: str
    previous_state: str
    new_state: str
    latest_run_key: str | None
    reason: str


def _latest_run(work_item: WorkItem):
    if not work_item.runs:
        return None
    return sorted(work_item.runs, key=lambda row: (row.attempt, row.created_at or utcnow()))[-1]


def _has_pr_link(work_item: WorkItem) -> bool:
    for link in work_item.github_links:
        if link.pr_number is not None:
            return True
    return False


def backfill_review_states(session: Session, request: ReviewStateBackfillRequest) -> list[ReviewStateBackfillRow]:
    query = session.query(WorkItem).filter(WorkItem.state == WorkItemState.AWAITING_REVIEW)
    if request.item_id:
        query = query.filter(WorkItem.item_id == request.item_id)
    changed: list[ReviewStateBackfillRow] = []
    for work_item in query.order_by(WorkItem.created_at.asc()).all():
        if _has_pr_link(work_item):
            continue
        run = _latest_run(work_item)
        if run is None or run.status not in _TERMINAL_RUN_STATES:
            continue
        work_item.state = WorkItemState.ARTIFACT_SYNC
        session.add(
            RunEvent(
                run_id=run.id,
                event_time=utcnow(),
                event_type='awaiting_review_backfilled',
                event_payload={
                    'previous_state': WorkItemState.AWAITING_REVIEW.value,
                    'new_state': WorkItemState.ARTIFACT_SYNC.value,
                    'reason': 'missing_pr_link',
                },
            )
        )
        changed.append(
            ReviewStateBackfillRow(
                item_id=work_item.item_id,
                previous_state=WorkItemState.AWAITING_REVIEW.value,
                new_state=WorkItemState.ARTIFACT_SYNC.value,
                latest_run_key=run.run_key,
                reason='missing_pr_link',
            )
        )
    if changed:
        session.commit()
    else:
        session.rollback()
    return changed
