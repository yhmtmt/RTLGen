"""GitHub linkage routes for Phase 1."""

from __future__ import annotations

import json

from control_plane.config import Settings
from control_plane.db import build_engine, build_session_factory, create_all
from control_plane.services.github_bridge import GitHubReconcileError, GitHubReconcileNotFound, GitHubReconcileRequest, reconcile_github_link


def register_github_routes(app) -> None:
    def reconcile_handler(_method: str, _path: str, _params: dict[str, str], body: bytes):
        try:
            payload = json.loads(body.decode("utf-8") or "{}")
        except json.JSONDecodeError as exc:
            error = json.dumps({"detail": f"invalid json body: {exc}"}).encode("utf-8")
            return 400, {"Content-Type": "application/json"}, error

        if "repo" not in payload or "state" not in payload:
            error = json.dumps({"detail": "repo and state are required"}).encode("utf-8")
            return 400, {"Content-Type": "application/json"}, error

        settings = Settings.from_env()
        engine = build_engine(settings.database_url)
        create_all(engine)
        session_factory = build_session_factory(engine)
        with session_factory() as session:
            try:
                result = reconcile_github_link(
                    session,
                    GitHubReconcileRequest(
                        repo=payload["repo"],
                        item_id=payload.get("item_id"),
                        branch_name=payload.get("branch_name"),
                        pr_number=payload.get("pr_number"),
                        pr_url=payload.get("pr_url"),
                        head_sha=payload.get("head_sha"),
                        base_branch=payload.get("base_branch"),
                        state=payload["state"],
                        run_key=payload.get("run_key"),
                        metadata=payload.get("metadata"),
                    ),
                )
            except GitHubReconcileNotFound as exc:
                error = json.dumps({"detail": str(exc), "status": "not_found"}).encode("utf-8")
                return 404, {"Content-Type": "application/json"}, error
            except GitHubReconcileError as exc:
                error = json.dumps({"detail": str(exc), "status": "error"}).encode("utf-8")
                return 400, {"Content-Type": "application/json"}, error

        response = json.dumps(result.__dict__, sort_keys=True).encode("utf-8")
        return 200, {"Content-Type": "application/json"}, response

    app.add_route("POST", "/api/v1/github/reconcile", reconcile_handler)
