"""Run lifecycle coverage for cp-004."""

from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from control_plane.api.app import create_app
from control_plane.clock import utcnow
from control_plane.db import create_all
from control_plane.models.enums import LeaseStatus, WorkItemState
from control_plane.models.run_events import RunEvent
from control_plane.models.runs import Run
from control_plane.models.task_requests import TaskRequest
from control_plane.models.work_items import WorkItem
from control_plane.models.worker_leases import WorkerLease
from control_plane.models.worker_machines import WorkerMachine
from control_plane.services.run_service import (
    append_run_event,
    complete_run,
    is_run_cancel_requested,
    request_run_cancel,
    start_run,
)
from control_plane.workers import executor as executor_module
from control_plane.services import worker_daemon as worker_daemon_module


def make_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)
    return Session(engine)


def seed_leased_work_item(session: Session) -> tuple[WorkerLease, WorkItem]:
    task = TaskRequest(
        request_key="queue:test_item",
        source="test",
        requested_by="tester",
        title="test item",
        description="test objective",
        layer="layer2",
        flow="openroad",
        priority=1,
        request_payload={"item_id": "test_item"},
    )
    session.add(task)
    session.flush()
    work_item = WorkItem(
        work_item_key="queue:test_item",
        task_request_id=task.id,
        item_id="test_item",
        layer="layer2",
        flow="openroad",
        platform="nangate45",
        task_type="l2_campaign",
        state=WorkItemState.LEASED,
        priority=1,
        input_manifest={},
        command_manifest=[],
        expected_outputs=[],
        acceptance_rules=[],
    )
    session.add(work_item)
    machine = WorkerMachine(
        machine_key="machine-1",
        hostname="machine-1",
        executor_kind="docker",
        capabilities={"platform": "nangate45"},
    )
    session.add(machine)
    session.flush()
    lease = WorkerLease(
        work_item_id=work_item.id,
        machine_id=machine.id,
        lease_token="lease-token-1",
        status=LeaseStatus.ACTIVE,
        leased_at=utcnow(),
        expires_at=utcnow(),
    )
    session.add(lease)
    session.commit()
    return lease, work_item


def test_start_append_complete_run_lifecycle() -> None:
    with make_session() as session:
        lease, work_item = seed_leased_work_item(session)
        started = start_run(
            session,
            lease_token=lease.lease_token,
            run_key="run-1",
            attempt=1,
            executor_type="internal_worker",
            container_image="rtlgen-eval:test",
            checkout_commit="abc123",
        )
        assert started.status == "running"
        run = session.query(Run).filter_by(run_key="run-1").one()
        session.refresh(work_item)
        assert run.work_item_id == work_item.id
        assert work_item.state == WorkItemState.RUNNING

        event = append_run_event(
            session,
            run_key="run-1",
            event_type="command_finished",
            event_payload={"command": "validate", "exit_code": 0},
        )
        assert event.event_type == "command_finished"

        completed = complete_run(
            session,
            run_key="run-1",
            status="succeeded",
            result_summary="ok",
            result_payload={"rows": 2},
            artifacts=[
                {
                    "kind": "report_md",
                    "storage_mode": "repo",
                    "path": "runs/campaigns/example/report.md",
                    "metadata": {"note": "smoke"},
                }
            ],
        )
        assert completed.status == "succeeded"
        session.refresh(work_item)
        run = session.query(Run).filter_by(run_key="run-1").one()
        lease = session.query(WorkerLease).filter_by(lease_token=lease.lease_token).one()
        assert run.status.value == "succeeded"
        assert lease.status == LeaseStatus.RELEASED
        assert work_item.state == WorkItemState.ARTIFACT_SYNC
        assert session.query(RunEvent).filter_by(run_id=run.id).count() == 3


def test_run_routes_work_in_process() -> None:
    with tempfile.TemporaryDirectory() as td:
        db_path = Path(td) / "cp.db"
        engine = create_engine(f"sqlite+pysqlite:///{db_path}", future=True)
        create_all(engine)
        with Session(engine) as session:
            seed_leased_work_item(session)

        old = os.environ.get("RTLCP_DATABASE_URL")
        os.environ["RTLCP_DATABASE_URL"] = f"sqlite+pysqlite:///{db_path}"
        try:
            app = create_app()
            status, _, body = app.handle(
                "POST",
                "/api/v1/leases/lease-token-1/start-run",
                json.dumps(
                    {
                        "run_key": "run-api-1",
                        "attempt": 1,
                        "executor_type": "internal_worker",
                    }
                ).encode("utf-8"),
            )
            assert status == 200
            assert json.loads(body.decode("utf-8"))["run_key"] == "run-api-1"

            status, _, body = app.handle(
                "POST",
                "/api/v1/runs/run-api-1/events",
                json.dumps(
                    {
                        "event_type": "heartbeat",
                        "event_payload": {"phase": "run_campaign"},
                    }
                ).encode("utf-8"),
            )
            assert status == 200
            assert json.loads(body.decode("utf-8"))["event_type"] == "heartbeat"

            status, _, body = app.handle(
                "POST",
                "/api/v1/runs/run-api-1/complete",
                json.dumps(
                    {
                        "status": "failed",
                        "result_summary": "flow failed",
                        "result_payload": {"reason": "mock"},
                    }
                ).encode("utf-8"),
            )
            assert status == 200
            assert json.loads(body.decode("utf-8"))["status"] == "failed"
        finally:
            if old is None:
                del os.environ["RTLCP_DATABASE_URL"]
            else:
                os.environ["RTLCP_DATABASE_URL"] = old


def test_request_run_cancel_marks_active_run() -> None:
    with make_session() as session:
        lease, _ = seed_leased_work_item(session)
        start_run(
            session,
            lease_token=lease.lease_token,
            run_key="run-cancel-1",
            attempt=1,
            executor_type="internal_worker",
        )

        result = request_run_cancel(
            session,
            run_key="run-cancel-1",
            requested_by="tester",
            reason="operator stop",
        )
        assert result.event_type == "cancel_requested"
        assert is_run_cancel_requested(session, run_key="run-cancel-1") is True

        again = request_run_cancel(session, run_key="run-cancel-1", requested_by="tester")
        assert again.event_id == result.event_id


def test_complete_run_truncates_failure_signature() -> None:
    with make_session() as session:
        lease, work_item = seed_leased_work_item(session)
        start_run(
            session,
            lease_token=lease.lease_token,
            run_key="run-long-signature",
            attempt=1,
            executor_type="internal_worker",
        )
        long_detail = "db-error:" + ("x" * 600)
        complete_run(
            session,
            run_key="run-long-signature",
            status="failed",
            result_summary="flow failed",
            result_payload={
                "failure_classification": {
                    "category": "worker_error",
                    "stage": "finalization",
                    "detail": long_detail,
                }
            },
        )
        run = session.query(Run).filter_by(run_key="run-long-signature").one()
        assert run.failure_signature is not None
        assert len(run.failure_signature) <= 255
        assert '[sha1:' in run.failure_signature
        session.refresh(work_item)
        assert work_item.state == WorkItemState.FAILED


def test_worker_daemon_survives_run_worker_exception(monkeypatch) -> None:
    class DummySessionFactory:
        def __call__(self):
            raise AssertionError('session_factory should not be used when run_worker is monkeypatched')

    def boom(session_factory, *, config, max_items):
        raise RuntimeError('simulated worker crash')

    monkeypatch.setattr(worker_daemon_module, 'run_worker', boom)
    result = worker_daemon_module.run_worker_daemon(
        DummySessionFactory(),
        config=worker_daemon_module.WorkerDaemonConfig(
            worker=executor_module.WorkerConfig(repo_root='/tmp', machine_key='test-worker'),
            max_polls=1,
            stop_on_no_work=False,
            run_scheduler_maintenance=False,
        ),
        log_fn=lambda _message: None,
    )
    assert len(result.results) == 1
    assert result.results[0].status == 'worker_error'
    assert 'simulated worker crash' in str(result.results[0].summary)
