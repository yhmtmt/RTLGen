"""Queue routes for Phase 1."""

from __future__ import annotations

import json

from control_plane.config import Settings
from control_plane.db import build_engine, build_session_factory, create_all
from control_plane.services.queue_exporter import QueueExportConflict, QueueExportError, QueueExportRequest, export_queue_item
from control_plane.services.queue_importer import QueueImportConflict, QueueImportError, QueueImportRequest, import_queue_item


def register_queue_routes(app) -> None:
    def list_placeholder(_method: str, _path: str, _params: dict[str, str], _body: bytes):
        body = json.dumps({"detail": "queue listing not implemented in cp-006"}).encode("utf-8")
        return 501, {"Content-Type": "application/json"}, body

    def import_handler(_method: str, _path: str, _params: dict[str, str], body: bytes):
        try:
            payload = json.loads(body.decode("utf-8") or "{}")
        except json.JSONDecodeError as exc:
            error = json.dumps({"detail": f"invalid json body: {exc}"}).encode("utf-8")
            return 400, {"Content-Type": "application/json"}, error

        settings = Settings.from_env()
        repo_root = payload.get("repo_root")
        queue_path = payload.get("queue_path")
        if not repo_root or not queue_path:
            error = json.dumps({"detail": "repo_root and queue_path are required"}).encode("utf-8")
            return 400, {"Content-Type": "application/json"}, error

        engine = build_engine(settings.database_url)
        create_all(engine)
        session_factory = build_session_factory(engine)
        with session_factory() as session:
            try:
                result = import_queue_item(
                    session,
                    QueueImportRequest(
                        repo_root=repo_root,
                        queue_path=queue_path,
                        source_commit=payload.get("source_commit"),
                        mode=payload.get("mode", "upsert"),
                    ),
                )
            except QueueImportConflict as exc:
                error = json.dumps({"detail": str(exc), "status": "conflict"}).encode("utf-8")
                return 409, {"Content-Type": "application/json"}, error
            except QueueImportError as exc:
                error = json.dumps({"detail": str(exc), "status": "error"}).encode("utf-8")
                return 400, {"Content-Type": "application/json"}, error

        response = json.dumps(result.__dict__, sort_keys=True).encode("utf-8")
        return 200, {"Content-Type": "application/json"}, response

    def export_handler(_method: str, _path: str, params: dict[str, str], body: bytes):
        try:
            payload = json.loads(body.decode("utf-8") or "{}")
        except json.JSONDecodeError as exc:
            error = json.dumps({"detail": f"invalid json body: {exc}"}).encode("utf-8")
            return 400, {"Content-Type": "application/json"}, error

        settings = Settings.from_env()
        if "repo_root" not in payload or "target_state" not in payload:
            error = json.dumps({"detail": "repo_root and target_state are required"}).encode("utf-8")
            return 400, {"Content-Type": "application/json"}, error

        engine = build_engine(settings.database_url)
        create_all(engine)
        session_factory = build_session_factory(engine)
        with session_factory() as session:
            try:
                result = export_queue_item(
                    session,
                    QueueExportRequest(
                        repo_root=payload["repo_root"],
                        item_id=params["item_id"],
                        target_state=payload["target_state"],
                        target_path=payload.get("target_path"),
                    ),
                )
            except QueueExportConflict as exc:
                error = json.dumps({"detail": str(exc), "status": "conflict"}).encode("utf-8")
                return 409, {"Content-Type": "application/json"}, error
            except QueueExportError as exc:
                error = json.dumps({"detail": str(exc), "status": "error"}).encode("utf-8")
                return 400, {"Content-Type": "application/json"}, error

        response = json.dumps(result.__dict__, sort_keys=True).encode("utf-8")
        return 200, {"Content-Type": "application/json"}, response

    app.add_route("GET", "/api/v1/queue", list_placeholder)
    app.add_route("POST", "/api/v1/queue/import", import_handler)
    app.add_route("POST", "/api/v1/queue/export/{item_id}", export_handler)
