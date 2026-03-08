"""Lease routes for Phase 1."""

from __future__ import annotations

import json

from control_plane.config import Settings
from control_plane.db import build_engine, build_session_factory, create_all
from control_plane.services.lease_service import LeaseConflict, LeaseNotFound, LeaseServiceError, acquire_next_lease, heartbeat_lease
from control_plane.services.run_service import LeaseNotFound as RunLeaseNotFound
from control_plane.services.run_service import RunConflict, RunLifecycleError, start_run
from control_plane.services.scheduler import NoEligibleWorkItem


def register_lease_routes(app) -> None:
    def not_implemented(_method: str, _path: str, _params: dict[str, str], _body: bytes):
        body = json.dumps({"detail": "lease API listing not implemented in cp-005"}).encode("utf-8")
        return 501, {"Content-Type": "application/json"}, body

    def acquire_next_handler(_method: str, _path: str, _params: dict[str, str], body: bytes):
        try:
            payload = json.loads(body.decode("utf-8") or "{}")
        except json.JSONDecodeError as exc:
            error = json.dumps({"detail": f"invalid json body: {exc}"}).encode("utf-8")
            return 400, {"Content-Type": "application/json"}, error
        if "machine_key" not in payload:
            error = json.dumps({"detail": "missing required field: machine_key"}).encode("utf-8")
            return 400, {"Content-Type": "application/json"}, error

        settings = Settings.from_env()
        engine = build_engine(settings.database_url)
        create_all(engine)
        session_factory = build_session_factory(engine)
        with session_factory() as session:
            try:
                result = acquire_next_lease(
                    session,
                    machine_key=payload["machine_key"],
                    hostname=payload.get("hostname"),
                    executor_kind=payload.get("executor_kind", "docker"),
                    capabilities=payload.get("capabilities"),
                    capability_filter=payload.get("capability_filter"),
                    lease_seconds=int(payload.get("lease_seconds", 1800)),
                )
            except NoEligibleWorkItem as exc:
                error = json.dumps({"detail": str(exc), "status": "no_work"}).encode("utf-8")
                return 404, {"Content-Type": "application/json"}, error
            except (LeaseConflict, LeaseServiceError) as exc:
                error = json.dumps({"detail": str(exc), "status": "error"}).encode("utf-8")
                return 400, {"Content-Type": "application/json"}, error

        response = json.dumps(result.__dict__, sort_keys=True).encode("utf-8")
        return 200, {"Content-Type": "application/json"}, response

    def heartbeat_handler(_method: str, _path: str, params: dict[str, str], body: bytes):
        try:
            payload = json.loads(body.decode("utf-8") or "{}")
        except json.JSONDecodeError as exc:
            error = json.dumps({"detail": f"invalid json body: {exc}"}).encode("utf-8")
            return 400, {"Content-Type": "application/json"}, error

        settings = Settings.from_env()
        engine = build_engine(settings.database_url)
        create_all(engine)
        session_factory = build_session_factory(engine)
        with session_factory() as session:
            try:
                result = heartbeat_lease(
                    session,
                    lease_token=params["lease_token"],
                    extend_seconds=int(payload.get("extend_seconds", 1800)),
                    progress=payload.get("progress"),
                )
            except LeaseNotFound as exc:
                error = json.dumps({"detail": str(exc), "status": "not_found"}).encode("utf-8")
                return 404, {"Content-Type": "application/json"}, error
            except LeaseServiceError as exc:
                error = json.dumps({"detail": str(exc), "status": "error"}).encode("utf-8")
                return 400, {"Content-Type": "application/json"}, error

        response = json.dumps(result.__dict__, sort_keys=True).encode("utf-8")
        return 200, {"Content-Type": "application/json"}, response

    def start_run_handler(_method: str, _path: str, params: dict[str, str], body: bytes):
        try:
            payload = json.loads(body.decode("utf-8") or "{}")
        except json.JSONDecodeError as exc:
            error = json.dumps({"detail": f"invalid json body: {exc}"}).encode("utf-8")
            return 400, {"Content-Type": "application/json"}, error

        required = ["run_key", "attempt", "executor_type"]
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
                result = start_run(
                    session,
                    lease_token=params["lease_token"],
                    run_key=payload["run_key"],
                    attempt=int(payload["attempt"]),
                    executor_type=payload["executor_type"],
                    container_image=payload.get("container_image"),
                    checkout_commit=payload.get("checkout_commit"),
                    branch_name=payload.get("branch_name"),
                )
            except RunLeaseNotFound as exc:
                error = json.dumps({"detail": str(exc), "status": "not_found"}).encode("utf-8")
                return 404, {"Content-Type": "application/json"}, error
            except RunConflict as exc:
                error = json.dumps({"detail": str(exc), "status": "conflict"}).encode("utf-8")
                return 409, {"Content-Type": "application/json"}, error
            except RunLifecycleError as exc:
                error = json.dumps({"detail": str(exc), "status": "error"}).encode("utf-8")
                return 400, {"Content-Type": "application/json"}, error

        response = json.dumps(result.__dict__, sort_keys=True).encode("utf-8")
        return 200, {"Content-Type": "application/json"}, response

    app.add_route("GET", "/api/v1/leases", not_implemented)
    app.add_route("POST", "/api/v1/leases/acquire-next", acquire_next_handler)
    app.add_route("POST", "/api/v1/leases/{lease_token}/heartbeat", heartbeat_handler)
    app.add_route("POST", "/api/v1/leases/{lease_token}/start-run", start_run_handler)
