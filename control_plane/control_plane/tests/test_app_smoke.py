"""Smoke coverage for the control-plane scaffold."""

from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile

from sqlalchemy import create_engine

from control_plane.api.app import create_app
from control_plane.db import create_all
from control_plane.clock import utcnow
from control_plane.models.enums import ExecutorType, FlowName, LayerName, RunStatus, WorkItemState
from control_plane.models.runs import Run
from control_plane.models.task_requests import TaskRequest
from control_plane.models.work_items import WorkItem


def test_health_route() -> None:
    app = create_app()
    status, headers, body = app.handle("GET", "/healthz")
    assert status == 200
    assert headers["Content-Type"] == "application/json"
    assert b'"status": "ok"' in body


def test_dashboard_route() -> None:
    app = create_app()
    status, headers, body = app.handle("GET", "/dashboard")
    assert status == 200
    assert headers["Content-Type"] == "text/html; charset=utf-8"
    assert b'RTLGen Control Plane' in body
    assert b'/api/v1/operator-status' in body
    assert b'Operator Controls' in body
    assert b'Pending Submission' in body
    assert b'Dispatch Pending' in body
    assert b'dispatch-pending-table' in body


def test_operator_status_route() -> None:
    with tempfile.TemporaryDirectory() as td:
        db_path = Path(td) / "cp.db"
        engine = create_engine(f"sqlite+pysqlite:///{db_path}", future=True)
        create_all(engine)

        previous = os.environ.get("RTLCP_DATABASE_URL")
        os.environ["RTLCP_DATABASE_URL"] = f"sqlite+pysqlite:///{db_path}"
        try:
            app = create_app()
            status, headers, body = app.handle("GET", "/api/v1/operator-status")
        finally:
            if previous is None:
                os.environ.pop("RTLCP_DATABASE_URL", None)
            else:
                os.environ["RTLCP_DATABASE_URL"] = previous

    payload = json.loads(body.decode("utf-8"))
    assert status == 200
    assert headers["Content-Type"] == "application/json"
    assert "generated_utc" in payload
    assert "change_token" in payload
    assert payload["health_summary"]["status"] in {"healthy", "attention"}
    assert isinstance(payload["state_counts"], dict)
    assert isinstance(payload["pending_submission_items"], list)
    assert isinstance(payload["dispatch_pending_items"], list)


def test_operator_status_change_token_stable_without_state_change() -> None:
    with tempfile.TemporaryDirectory() as td:
        db_path = Path(td) / "cp.db"
        engine = create_engine(f"sqlite+pysqlite:///{db_path}", future=True)
        create_all(engine)

        previous = os.environ.get("RTLCP_DATABASE_URL")
        os.environ["RTLCP_DATABASE_URL"] = f"sqlite+pysqlite:///{db_path}"
        try:
            app = create_app()
            _status1, _headers1, body1 = app.handle("GET", "/api/v1/operator-status")
            _status2, _headers2, body2 = app.handle("GET", "/api/v1/operator-status")
        finally:
            if previous is None:
                os.environ.pop("RTLCP_DATABASE_URL", None)
            else:
                os.environ["RTLCP_DATABASE_URL"] = previous

    payload1 = json.loads(body1.decode("utf-8"))
    payload2 = json.loads(body2.decode("utf-8"))
    assert payload1["change_token"] == payload2["change_token"]


def test_operator_control_routes_on_empty_db() -> None:
    with tempfile.TemporaryDirectory() as td:
        db_path = Path(td) / "cp.db"
        engine = create_engine(f"sqlite+pysqlite:///{db_path}", future=True)
        create_all(engine)

        previous = os.environ.get("RTLCP_DATABASE_URL")
        os.environ["RTLCP_DATABASE_URL"] = f"sqlite+pysqlite:///{db_path}"
        try:
            app = create_app()
            status_pc, _headers_pc, body_pc = app.handle("POST", "/api/v1/control/process-completions", b"{}")
            status_pg, _headers_pg, body_pg = app.handle("POST", "/api/v1/control/poll-github", b"{}")
            status_bf, _headers_bf, body_bf = app.handle("POST", "/api/v1/control/backfill-review-states", b"{}")
        finally:
            if previous is None:
                os.environ.pop("RTLCP_DATABASE_URL", None)
            else:
                os.environ["RTLCP_DATABASE_URL"] = previous

    payload_pc = json.loads(body_pc.decode("utf-8"))
    payload_pg = json.loads(body_pg.decode("utf-8"))
    payload_bf = json.loads(body_bf.decode("utf-8"))
    assert status_pc == 200
    assert payload_pc["results"] == []
    assert status_pg == 200
    assert payload_pg["checked_count"] == 0
    assert status_bf == 200
    assert payload_bf["results"] == []


def test_operator_submit_route_queues_retry_request() -> None:
    with tempfile.TemporaryDirectory() as td:
        db_path = Path(td) / "cp.db"
        engine = create_engine(f"sqlite+pysqlite:///{db_path}", future=True)
        create_all(engine)
        with engine.begin() as conn:
            pass
        from sqlalchemy.orm import Session
        with Session(engine) as session:
            task = TaskRequest(
                request_key="queue:retry_item",
                source="test",
                requested_by="tester",
                title="retry_item",
                description="retry_item",
                layer=LayerName.LAYER1,
                flow=FlowName.OPENROAD,
                priority=1,
                request_payload={"item_id": "retry_item"},
            )
            session.add(task)
            session.flush()
            work_item = WorkItem(
                work_item_key="queue:retry_item",
                task_request_id=task.id,
                item_id="retry_item",
                layer=LayerName.LAYER1,
                flow=FlowName.OPENROAD,
                platform="nangate45",
                task_type="l1_sweep",
                state=WorkItemState.ARTIFACT_SYNC,
                priority=1,
                input_manifest={},
                command_manifest=[],
                expected_outputs=[],
                acceptance_rules=[],
            )
            session.add(work_item)
            session.flush()
            session.add(
                Run(
                    run_key="retry_item_run_1",
                    work_item_id=work_item.id,
                    attempt=1,
                    executor_type=ExecutorType.INTERNAL_WORKER,
                    status=RunStatus.SUCCEEDED,
                    started_at=utcnow(),
                    completed_at=utcnow(),
                    result_summary="completed",
                    result_payload={},
                )
            )
            session.commit()

        previous = os.environ.get("RTLCP_DATABASE_URL")
        os.environ["RTLCP_DATABASE_URL"] = f"sqlite+pysqlite:///{db_path}"
        try:
            app = create_app()
            status, _headers, body = app.handle("POST", "/api/v1/control/items/retry_item/submit", b"{}")
        finally:
            if previous is None:
                os.environ.pop("RTLCP_DATABASE_URL", None)
            else:
                os.environ["RTLCP_DATABASE_URL"] = previous

    payload = json.loads(body.decode("utf-8"))
    assert status == 200
    assert payload["result"]["item_id"] == "retry_item"
    assert payload["result"]["already_requested"] is False
