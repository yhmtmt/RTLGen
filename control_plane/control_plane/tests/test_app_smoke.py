"""Smoke coverage for the control-plane scaffold."""

from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile

from sqlalchemy import create_engine

from control_plane.api.app import create_app
from control_plane.db import create_all


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
