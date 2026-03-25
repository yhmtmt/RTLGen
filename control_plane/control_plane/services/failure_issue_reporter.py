"""Automatically open GitHub issues for terminal failed runs."""

from __future__ import annotations

from dataclasses import dataclass
import json
import subprocess
from typing import Any

from sqlalchemy.orm import Session

from control_plane.clock import utcnow
from control_plane.models.enums import RunStatus, WorkItemState
from control_plane.models.run_events import RunEvent
from control_plane.models.runs import Run
from control_plane.models.work_items import WorkItem


class FailureIssueReportError(RuntimeError):
    pass


@dataclass(frozen=True)
class FailureIssueReportRequest:
    repo: str
    max_items: int | None = None


@dataclass(frozen=True)
class FailureIssueReportResult:
    checked_count: int
    created_count: int
    skipped_count: int
    errors: list[str]


_TERMINAL_FAILURE_RUN_STATUSES = (
    RunStatus.FAILED,
    RunStatus.TIMED_OUT,
    RunStatus.CANCELED,
)


def _gh_api_issue_create(repo: str, *, title: str, body: str) -> dict[str, Any]:
    result = subprocess.run(
        [
            'gh',
            'api',
            f'repos/{repo}/issues',
            '--method',
            'POST',
            '-f',
            f'title={title}',
            '-f',
            f'body={body}',
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    if not isinstance(payload, dict):
        raise FailureIssueReportError(f'unexpected gh api payload for issue create in {repo}')
    return payload


def _failure_issue_terminal(run: Run) -> bool:
    payload = dict(run.result_payload or {})
    issue = dict(payload.get('failure_issue') or {})
    if str(issue.get('issue_number') or '').strip():
        return True
    if bool(issue.get('skipped')):
        return True
    return False


def _latest_terminal_failed_runs(
    session: Session,
    *,
    max_items: int | None = None,
) -> list[tuple[WorkItem, Run]]:
    work_items = (
        session.query(WorkItem)
        .filter(WorkItem.state == WorkItemState.FAILED)
        .order_by(WorkItem.updated_at.asc(), WorkItem.created_at.asc())
        .all()
    )
    rows: list[tuple[WorkItem, Run]] = []
    for work_item in work_items:
        latest_run = (
            session.query(Run)
            .filter(Run.work_item_id == work_item.id)
            .order_by(Run.attempt.desc(), Run.created_at.desc())
            .first()
        )
        if latest_run is None:
            continue
        if latest_run.status not in _TERMINAL_FAILURE_RUN_STATUSES:
            continue
        rows.append((work_item, latest_run))
        if max_items is not None and len(rows) >= max_items:
            break
    return rows


def _failure_category(run: Run) -> str:
    payload = dict(run.result_payload or {})
    failure = dict(payload.get('failure_classification') or {})
    category = str(failure.get('category') or '').strip()
    if category:
        return category
    return run.status.value


def _failure_detail(run: Run) -> str:
    payload = dict(run.result_payload or {})
    failure = dict(payload.get('failure_classification') or {})
    detail = str(failure.get('detail') or '').strip()
    if detail:
        return detail
    return run.result_summary or f'run ended with status={run.status.value}'


def _queue_notes(run: Run) -> list[str]:
    payload = dict(run.result_payload or {})
    queue_result = dict(payload.get('queue_result') or {})
    notes = queue_result.get('notes') or []
    if not isinstance(notes, list):
        return []
    return [str(note) for note in notes if str(note).strip()]


def _failed_command(run: Run) -> dict[str, Any] | None:
    payload = dict(run.result_payload or {})
    commands = payload.get('commands') or []
    if not isinstance(commands, list):
        return None
    for command in commands:
        if not isinstance(command, dict):
            continue
        returncode = command.get('returncode')
        if bool(command.get('timed_out')) or bool(command.get('stalled')) or bool(command.get('canceled')):
            return command
        if isinstance(returncode, int) and returncode != 0:
            return command
    return None


def _developer_loop(work_item: WorkItem) -> dict[str, Any]:
    payload = dict((work_item.task_request.request_payload or {}) if work_item.task_request is not None else {})
    developer_loop = payload.get('developer_loop') or {}
    if not isinstance(developer_loop, dict):
        return {}
    return developer_loop


def _issue_title(work_item: WorkItem, run: Run) -> str:
    return f'Failed job: {work_item.item_id} [{_failure_category(run)}]'


def _issue_body(work_item: WorkItem, run: Run) -> str:
    payload = dict(run.result_payload or {})
    checkout = dict(payload.get('checkout') or {})
    developer_loop = _developer_loop(work_item)
    evaluation = developer_loop.get('evaluation') or {}
    abstraction = developer_loop.get('abstraction') or {}
    failed_command = _failed_command(run)
    lines = [
        'Automatic failed-job report from the evaluator control plane.',
        '',
        '## Run',
        f'- item_id: `{work_item.item_id}`',
        f'- task_type: `{work_item.task_type}`',
        f'- layer: `{work_item.layer.value}`',
        f'- platform: `{work_item.platform}`',
        f'- run_key: `{run.run_key}`',
        f'- run_status: `{run.status.value}`',
        f'- result_summary: `{run.result_summary}`',
    ]
    if work_item.source_commit:
        lines.append(f'- source_commit: `{work_item.source_commit}`')
    if run.checkout_commit:
        lines.append(f'- checkout_commit: `{run.checkout_commit}`')
    if str(checkout.get('source_commit_relation') or '').strip():
        lines.append(f"- source_commit_relation: `{checkout['source_commit_relation']}`")
    if str(checkout.get('head_sha') or '').strip():
        lines.append(f"- checkout_head_sha: `{checkout['head_sha']}`")

    lines.extend(
        [
            '',
            '## Failure',
            f'- category: `{_failure_category(run)}`',
            f'- detail: {_failure_detail(run)}',
        ]
    )

    notes = _queue_notes(run)
    if notes:
        lines.append('- queue_notes:')
        for note in notes:
            lines.append(f'  - `{note}`')

    if failed_command is not None:
        lines.extend(
            [
                '',
                '## Failed Command',
                f"- name: `{failed_command.get('name') or ''}`",
                f"- command: `{failed_command.get('command') or ''}`",
                f"- returncode: `{failed_command.get('returncode')}`",
                f"- timed_out: `{bool(failed_command.get('timed_out'))}`",
                f"- stalled: `{bool(failed_command.get('stalled'))}`",
                f"- canceled: `{bool(failed_command.get('canceled'))}`",
            ]
        )
        if str(failed_command.get('stdout_log') or '').strip():
            lines.append(f"- stdout_log: `{failed_command['stdout_log']}`")
        if str(failed_command.get('stderr_log') or '').strip():
            lines.append(f"- stderr_log: `{failed_command['stderr_log']}`")

    proposal_id = str(developer_loop.get('proposal_id') or '').strip()
    proposal_path = str(developer_loop.get('proposal_path') or '').strip()
    evaluation_mode = str(evaluation.get('mode') or '').strip()
    abstraction_layer = str(abstraction.get('layer') or '').strip()
    if proposal_id or proposal_path or evaluation_mode or abstraction_layer:
        lines.append('')
        lines.append('## Proposal Context')
        if proposal_id:
            lines.append(f'- proposal_id: `{proposal_id}`')
        if proposal_path:
            lines.append(f'- proposal_path: `{proposal_path}`')
        if evaluation_mode:
            lines.append(f'- evaluation_mode: `{evaluation_mode}`')
        if abstraction_layer:
            lines.append(f'- abstraction_layer: `{abstraction_layer}`')

    return "\n".join(lines).rstrip() + "\n"


def _mark_issue_state(
    session: Session,
    *,
    run: Run,
    event_type: str,
    issue_payload: dict[str, Any],
) -> None:
    payload = dict(run.result_payload or {})
    payload['failure_issue'] = issue_payload
    run.result_payload = payload
    session.add(
        RunEvent(
            run_id=run.id,
            event_time=utcnow(),
            event_type=event_type,
            event_payload=issue_payload,
        )
    )


def report_failure_issues(session: Session, request: FailureIssueReportRequest) -> FailureIssueReportResult:
    checked_count = 0
    created_count = 0
    skipped_count = 0
    errors: list[str] = []

    for work_item, run in _latest_terminal_failed_runs(session, max_items=request.max_items):
        if _failure_issue_terminal(run):
            skipped_count += 1
            continue

        checked_count += 1
        category = _failure_category(run)
        if category == 'command_canceled':
            issue_payload = {
                'skipped': True,
                'reason': 'command_canceled',
                'attempted_utc': utcnow().isoformat(),
                'category': category,
            }
            _mark_issue_state(
                session,
                run=run,
                event_type='failure_issue_skipped',
                issue_payload=issue_payload,
            )
            session.commit()
            skipped_count += 1
            continue

        try:
            issue = _gh_api_issue_create(
                request.repo,
                title=_issue_title(work_item, run),
                body=_issue_body(work_item, run),
            )
        except Exception as exc:
            session.rollback()
            errors.append(f'{work_item.item_id}/{run.run_key}: {exc}')
            continue

        issue_number = issue.get('number')
        issue_url = str(issue.get('html_url') or '').strip() or None
        issue_payload = {
            'issue_number': int(issue_number) if issue_number is not None else None,
            'issue_url': issue_url,
            'title': _issue_title(work_item, run),
            'category': category,
            'reported_utc': utcnow().isoformat(),
        }
        _mark_issue_state(
            session,
            run=run,
            event_type='failure_issue_reported',
            issue_payload=issue_payload,
        )
        session.commit()
        created_count += 1

    return FailureIssueReportResult(
        checked_count=checked_count,
        created_count=created_count,
        skipped_count=skipped_count,
        errors=errors,
    )
