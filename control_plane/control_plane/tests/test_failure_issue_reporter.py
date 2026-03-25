"""Automatic failed-job GitHub issue reporting coverage."""

from __future__ import annotations

import json
import subprocess
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from control_plane.clock import utcnow
from control_plane.db import create_all
from control_plane.models.enums import ExecutorType, FlowName, LayerName, RunStatus, WorkItemState
from control_plane.models.runs import Run
from control_plane.models.task_requests import TaskRequest
from control_plane.models.work_items import WorkItem
from control_plane.services.failure_issue_reporter import FailureIssueReportRequest, report_failure_issues


def _session() -> Session:
    engine = create_engine('sqlite+pysqlite:///:memory:', future=True)
    create_all(engine)
    return Session(engine)


def _seed_failed_run(
    session: Session,
    *,
    item_id: str = 'l1_demo_fail_r1',
    run_status: RunStatus = RunStatus.FAILED,
    failure_category: str = 'command_failure',
    failure_issue: dict | None = None,
) -> Run:
    task = TaskRequest(
        request_key=f'queue:{item_id}',
        source='test',
        requested_by='tester',
        title=f'{item_id} title',
        description='failed job issue reporter test',
        layer=LayerName.LAYER1,
        flow=FlowName.OPENROAD,
        priority=1,
        request_payload={
            'developer_loop': {
                'proposal_id': 'prop_l1_demo_v1',
                'proposal_path': 'docs/developer_loop/prop_l1_demo_v1/proposal.json',
                'evaluation': {'mode': 'physical_metrics'},
                'abstraction': {'layer': 'circuit_block'},
            }
        },
    )
    session.add(task)
    session.flush()
    work_item = WorkItem(
        work_item_key=f'queue:{item_id}',
        task_request_id=task.id,
        item_id=item_id,
        layer=LayerName.LAYER1,
        flow=FlowName.OPENROAD,
        platform='nangate45',
        task_type='l1_sweep',
        state=WorkItemState.FAILED,
        priority=1,
        input_manifest={},
        command_manifest=[],
        expected_outputs=[],
        acceptance_rules=[],
        source_commit='abc123',
    )
    session.add(work_item)
    session.flush()
    payload = {
        'failure_classification': {
            'category': failure_category,
            'detail': 'command fail_step failed with exit_code=3',
        },
        'queue_result': {
            'status': 'fail',
            'notes': ['failure_command=fail_step'],
            'metrics_rows': [],
        },
        'commands': [
            {
                'name': 'generate',
                'command': 'python3 ok.py',
                'returncode': 0,
                'stdout_log': 'logs/generate.stdout.log',
                'stderr_log': 'logs/generate.stderr.log',
                'timed_out': False,
                'stalled': False,
                'canceled': False,
            },
            {
                'name': 'fail_step',
                'command': 'python3 fail.py',
                'returncode': 3,
                'stdout_log': 'logs/fail_step.stdout.log',
                'stderr_log': 'logs/fail_step.stderr.log',
                'timed_out': False,
                'stalled': False,
                'canceled': False,
            },
        ],
        'checkout': {
            'source_commit_relation': 'exact',
            'head_sha': 'abc123',
        },
    }
    if failure_issue is not None:
        payload['failure_issue'] = failure_issue
    run = Run(
        run_key=f'{item_id}_run_1',
        work_item_id=work_item.id,
        attempt=1,
        executor_type=ExecutorType.INTERNAL_WORKER,
        status=run_status,
        started_at=utcnow(),
        completed_at=utcnow(),
        checkout_commit='abc123',
        result_summary='command fail_step failed (exit_code=3)',
        result_payload=payload,
    )
    session.add(run)
    session.commit()
    return run


def test_report_failure_issues_creates_issue_and_persists_metadata() -> None:
    with _session() as session:
        run = _seed_failed_run(session)
        created_payload = {
            'number': 101,
            'html_url': 'https://github.com/yhmtmt/RTLGen/issues/101',
        }
        with patch('control_plane.services.failure_issue_reporter.subprocess.run') as run_mock:
            run_mock.return_value = subprocess.CompletedProcess(
                args=['gh', 'api'],
                returncode=0,
                stdout=json.dumps(created_payload),
                stderr='',
            )
            result = report_failure_issues(
                session,
                FailureIssueReportRequest(repo='yhmtmt/RTLGen'),
            )

        assert result.checked_count == 1
        assert result.created_count == 1
        assert result.skipped_count == 0
        assert result.errors == []
        run = session.query(Run).filter_by(run_key=run.run_key).one()
        failure_issue = dict((run.result_payload or {}).get('failure_issue') or {})
        assert failure_issue['issue_number'] == 101
        assert failure_issue['issue_url'] == 'https://github.com/yhmtmt/RTLGen/issues/101'
        assert failure_issue['category'] == 'command_failure'
        assert run.events[-1].event_type == 'failure_issue_reported'
        called_argv = run_mock.call_args.args[0]
        assert called_argv[:4] == ['gh', 'api', 'repos/yhmtmt/RTLGen/issues', '--method']
        assert any(str(part).startswith('title=Failed job: l1_demo_fail_r1 [command_failure]') for part in called_argv)


def test_report_failure_issues_skips_already_reported_run() -> None:
    with _session() as session:
        _seed_failed_run(
            session,
            failure_issue={
                'issue_number': 88,
                'issue_url': 'https://github.com/yhmtmt/RTLGen/issues/88',
                'reported_utc': '2026-03-25T00:00:00Z',
            },
        )
        with patch('control_plane.services.failure_issue_reporter.subprocess.run') as run_mock:
            result = report_failure_issues(
                session,
                FailureIssueReportRequest(repo='yhmtmt/RTLGen'),
            )

        assert result.checked_count == 0
        assert result.created_count == 0
        assert result.skipped_count == 1
        assert result.errors == []
        run_mock.assert_not_called()


def test_report_failure_issues_marks_command_canceled_as_skipped() -> None:
    with _session() as session:
        run = _seed_failed_run(
            session,
            item_id='l1_demo_cancel_r1',
            run_status=RunStatus.CANCELED,
            failure_category='command_canceled',
        )
        with patch('control_plane.services.failure_issue_reporter.subprocess.run') as run_mock:
            result = report_failure_issues(
                session,
                FailureIssueReportRequest(repo='yhmtmt/RTLGen'),
            )

        assert result.checked_count == 1
        assert result.created_count == 0
        assert result.skipped_count == 1
        assert result.errors == []
        run = session.query(Run).filter_by(run_key=run.run_key).one()
        failure_issue = dict((run.result_payload or {}).get('failure_issue') or {})
        assert failure_issue['skipped'] is True
        assert failure_issue['reason'] == 'command_canceled'
        assert run.events[-1].event_type == 'failure_issue_skipped'
        run_mock.assert_not_called()
