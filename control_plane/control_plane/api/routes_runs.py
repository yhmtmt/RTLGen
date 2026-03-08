"""Run routes for Phase 1."""

from __future__ import annotations

import json

from control_plane.config import Settings
from control_plane.db import build_engine, build_session_factory, create_all
from control_plane.services.run_service import RunLifecycleError, RunNotFound, append_run_event, complete_run


def register_run_routes(app) -> None:
    def not_implemented(_method: str, _path: str, _params: dict[str, str], _body: bytes):
        body = json.dumps({"detail": "run listing not implemented in cp-004"}).encode("utf-8")
        return 501, {"Content-Type": "application/json"}, body

    def append_event_handler(_method: str, _path: str, params: dict[str, str], body: bytes):
        try:
            payload = json.loads(body.decode("utf-8") or "{}")
        except json.JSONDecodeError as exc:
            error = json.dumps({"detail": f"invalid json body: {exc}"}).encode("utf-8")
            return 400, {"Content-Type": "application/json"}, error
        if "event_type" not in payload:
            error = json.dumps({"detail": "missing required field: event_type"}).encode("utf-8")
            return 400, {"Content-Type": "application/json"}, error

        settings = Settings.from_env()
        engine = build_engine(settings.database_url)
        create_all(engine)
        session_factory = build_session_factory(engine)
        with session_factory() as session:
            try:
                result = append_run_event(
                    session,
                    run_key=params["run_key"],
                    event_type=payload["event_type"],
                    event_payload=payload.get("event_payload"),
                )
            except RunNotFound as exc:
                error = json.dumps({"detail": str(exc), "status": "not_found"}).encode("utf-8")
                return 404, {"Content-Type": "application/json"}, error

        response = json.dumps(result.__dict__, sort_keys=True).encode("utf-8")
        return 200, {"Content-Type": "application/json"}, response

    def complete_run_handler(_method: str, _path: str, params: dict[str, str], body: bytes):
        try:
            payload = json.loads(body.decode("utf-8") or "{}")
        except json.JSONDecodeError as exc:
            error = json.dumps({"detail": f"invalid json body: {exc}"}).encode("utf-8")
            return 400, {"Content-Type": "application/json"}, error

        required = ["status", "result_summary"]
        missing = [key for key in required if key not in payload]
        if missing:
            error = json.dumps({"detail": f"missing required fields: {', '.join(missing)}"}).encode("utf-8")
            return 400, {"Content-Type": "application/json"}, error

        settings = Settings.from_env()
        engine = build_engine(settings.database_url)
        create_all(engine)
        session_factory = build_session_factory(engine)
        with session_factory() as session:
            try:
                result = complete_run(
                    session,
                    run_key=params["run_key"],
                    status=payload["status"],
                    result_summary=payload["result_summary"],
                    result_payload=payload.get("result_payload"),
                    artifacts=payload.get("artifacts"),
                )
            except RunNotFound as exc:
                error = json.dumps({"detail": str(exc), "status": "not_found"}).encode("utf-8")
                return 404, {"Content-Type": "application/json"}, error
            except RunLifecycleError as exc:
                error = json.dumps({"detail": str(exc), "status": "error"}).encode("utf-8")
                return 400, {"Content-Type": "application/json"}, error

        response = json.dumps(result.__dict__, sort_keys=True).encode("utf-8")
        return 200, {"Content-Type": "application/json"}, response

    app.add_route("GET", "/api/v1/runs", not_implemented)
    app.add_route("POST", "/api/v1/runs/{run_key}/events", append_event_handler)
    app.add_route("POST", "/api/v1/runs/{run_key}/complete", complete_run_handler)
