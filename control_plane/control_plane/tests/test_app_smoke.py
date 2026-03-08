"""Smoke coverage for the control-plane scaffold."""

from __future__ import annotations

from control_plane.api.app import create_app


def test_health_route() -> None:
    app = create_app()
    status, headers, body = app.handle("GET", "/healthz")
    assert status == 200
    assert headers["Content-Type"] == "application/json"
    assert b'"status": "ok"' in body
