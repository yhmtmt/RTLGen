"""DB-backed submission retry requests for evaluator-side resume handling."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from control_plane.clock import utcnow
from control_plane.ids import make_id
from control_plane.models.enums import RunStatus, WorkItemState
from control_plane.models.run_events import RunEvent
from control_plane.models.runs import Run
from control_plane.models.work_items import WorkItem


class CompletionRetryError(RuntimeError):
    pass


@dataclass(frozen=True)
class SubmissionRetryStatus:
    requested: bool
    request_id: str | None
    force: bool
    target_machine_key: str | None


@dataclass(frozen=True)
class SubmissionRetryRequestResult:
    item_id: str
    run_key: str
    request_id: str
    work_item_state: str
    target_machine_key: str | None
    already_requested: bool


@dataclass(frozen=True)
class SubmissionRetryClaim:
    item_id: str
    run_key: str
    request_id: str
    force: bool
    target_machine_key: str | None


def _latest_run_for_item(work_item: WorkItem) -> Run | None:
    if not work_item.runs:
        return None
    return sorted(work_item.runs, key=lambda row: (row.attempt, row.created_at or utcnow()))[-1]


def _target_machine_key(work_item: WorkItem, run: Run | None) -> str | None:
    if str(work_item.assigned_machine_key or '').strip():
        return str(work_item.assigned_machine_key).strip()
    if run is not None and run.machine is not None and str(run.machine.machine_key or '').strip():
        return str(run.machine.machine_key).strip()
    return None


def _latest_retry_request_event(session: Session, *, run_id: str) -> RunEvent | None:
    return (
        session.query(RunEvent)
        .filter(RunEvent.run_id == run_id, RunEvent.event_type == 'submission_retry_requested')
        .order_by(RunEvent.event_time.desc())
        .first()
    )


def _latest_retry_started_event(session: Session, *, run_id: str) -> RunEvent | None:
    return (
        session.query(RunEvent)
        .filter(RunEvent.run_id == run_id, RunEvent.event_type == 'submission_retry_started')
        .order_by(RunEvent.event_time.desc())
        .first()
    )


def submission_retry_status(
    session: Session,
    *,
    work_item: WorkItem,
    run: Run | None = None,
) -> SubmissionRetryStatus:
    latest_run = run or _latest_run_for_item(work_item)
    if latest_run is None:
        return SubmissionRetryStatus(requested=False, request_id=None, force=False, target_machine_key=None)
    request_event = _latest_retry_request_event(session, run_id=latest_run.id)
    if request_event is None:
        return SubmissionRetryStatus(
            requested=False,
            request_id=None,
            force=False,
            target_machine_key=_target_machine_key(work_item, latest_run),
        )
    started_event = _latest_retry_started_event(session, run_id=latest_run.id)
    payload = dict(request_event.event_payload or {}) if isinstance(request_event.event_payload, dict) else {}
    request_id = str(payload.get('request_id', '')).strip() or None
    force = bool(payload.get('force', False))
    target_machine_key = str(payload.get('target_machine_key', '')).strip() or _target_machine_key(work_item, latest_run)
    requested = started_event is None or request_event.event_time > started_event.event_time
    return SubmissionRetryStatus(
        requested=requested,
        request_id=request_id,
        force=force,
        target_machine_key=target_machine_key,
    )


def request_submission_retry(
    session: Session,
    *,
    item_id: str,
    actor: str,
    force: bool = False,
) -> SubmissionRetryRequestResult:
    work_item = session.query(WorkItem).filter(WorkItem.item_id == item_id).one_or_none()
    if work_item is None:
        raise CompletionRetryError(f'work item not found: {item_id}')
    if work_item.state != WorkItemState.ARTIFACT_SYNC:
        raise CompletionRetryError(
            f'work item {item_id} is not ready for submission retry: state={work_item.state.value}'
        )
    latest_run = _latest_run_for_item(work_item)
    if latest_run is None:
        raise CompletionRetryError(f'work item {item_id} has no runs')
    if latest_run.status != RunStatus.SUCCEEDED:
        raise CompletionRetryError(
            f'work item {item_id} is not ready for submission retry: run_status={latest_run.status.value}'
        )
    current = submission_retry_status(session, work_item=work_item, run=latest_run)
    if current.requested and current.request_id:
        return SubmissionRetryRequestResult(
            item_id=work_item.item_id,
            run_key=latest_run.run_key,
            request_id=current.request_id,
            work_item_state=work_item.state.value,
            target_machine_key=current.target_machine_key,
            already_requested=True,
        )

    request_id = make_id('resume')
    target_machine_key = _target_machine_key(work_item, latest_run)
    session.add(
        RunEvent(
            run_id=latest_run.id,
            event_time=utcnow(),
            event_type='submission_retry_requested',
            event_payload={
                'request_id': request_id,
                'actor': actor,
                'force': force,
                'target_machine_key': target_machine_key,
            },
        )
    )
    session.commit()
    return SubmissionRetryRequestResult(
        item_id=work_item.item_id,
        run_key=latest_run.run_key,
        request_id=request_id,
        work_item_state=work_item.state.value,
        target_machine_key=target_machine_key,
        already_requested=False,
    )


def claim_submission_retry(
    session: Session,
    *,
    machine_key: str,
) -> SubmissionRetryClaim | None:
    candidates = (
        session.query(WorkItem)
        .filter(WorkItem.state == WorkItemState.ARTIFACT_SYNC)
        .order_by(WorkItem.updated_at.asc(), WorkItem.created_at.asc())
        .all()
    )
    for work_item in candidates:
        latest_run = _latest_run_for_item(work_item)
        if latest_run is None or latest_run.status != RunStatus.SUCCEEDED:
            continue
        status = submission_retry_status(session, work_item=work_item, run=latest_run)
        if not status.requested or not status.request_id:
            continue
        if status.target_machine_key and status.target_machine_key != machine_key:
            continue
        session.add(
            RunEvent(
                run_id=latest_run.id,
                event_time=utcnow(),
                event_type='submission_retry_started',
                event_payload={
                    'request_id': status.request_id,
                    'machine_key': machine_key,
                    'force': status.force,
                },
            )
        )
        session.commit()
        return SubmissionRetryClaim(
            item_id=work_item.item_id,
            run_key=latest_run.run_key,
            request_id=status.request_id,
            force=status.force,
            target_machine_key=status.target_machine_key,
        )
    return None
