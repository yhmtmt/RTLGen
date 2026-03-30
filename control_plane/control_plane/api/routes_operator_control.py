"""Operator control routes for dashboard-triggered actions."""

from __future__ import annotations

import json
import os
import socket

from control_plane.api.deps import get_settings
from control_plane.db import build_engine, build_session_factory, create_all
from control_plane.models.enums import WorkItemState
from control_plane.models.run_events import RunEvent
from control_plane.models.work_items import WorkItem
from control_plane.clock import utcnow
from control_plane.services.completion_service import CompletionProcessRequest, CompletionProcessingError, process_completed_items
from control_plane.services.github_poller import GitHubPollRequest, poll_github_links
from control_plane.services.review_state_backfill import ReviewStateBackfillRequest, backfill_review_states
from control_plane.services.dispatcher_service import DispatchReadyRequest, dispatch_ready_items


def _json_response(status: int, payload: dict[str, object]):
    return status, {"Content-Type": "application/json"}, json.dumps(payload, sort_keys=True).encode("utf-8")


def _json_body(body: bytes) -> dict[str, object]:
    if not body:
        return {}
    payload = json.loads(body.decode("utf-8"))
    return payload if isinstance(payload, dict) else {}


def _service_repo_root() -> str:
    return os.getenv("RTLGEN_SERVICE_REPO", "/workspaces/rtlgen-eval-clean")


def _github_repo() -> str:
    return os.getenv("RTLCP_GITHUB_REPO", "yhmtmt/RTLGen")


def _supersede_item(session, *, item_id: str, reason: str, actor: str) -> dict[str, object]:
    work_item = session.query(WorkItem).filter(WorkItem.item_id == item_id).one_or_none()
    if work_item is None:
        raise ValueError(f"work item not found: {item_id}")
    if work_item.state in {WorkItemState.MERGED, WorkItemState.SUPERSEDED}:
        raise ValueError(f"cannot supersede item from state={work_item.state.value}")
    latest_run = None
    if work_item.runs:
        latest_run = sorted(work_item.runs, key=lambda row: (row.attempt, row.created_at or utcnow()))[-1]
    work_item.state = WorkItemState.SUPERSEDED
    if latest_run is not None:
        session.add(
            RunEvent(
                run_id=latest_run.id,
                event_time=utcnow(),
                event_type="work_item_superseded",
                event_payload={"reason": reason, "actor": actor},
            )
        )
    session.commit()
    return {"item_id": work_item.item_id, "state": work_item.state.value, "reason": reason}


def register_operator_control_routes(app) -> None:
    settings = get_settings()

    def process_completions_handler(_method: str, _path: str, _params: dict[str, str], body: bytes):
        payload = _json_body(body)
        engine = build_engine(settings.database_url)
        create_all(engine)
        session_factory = build_session_factory(engine)
        with session_factory() as session:
            result = process_completed_items(
                session,
                CompletionProcessRequest(
                    repo_root=_service_repo_root(),
                    repo=_github_repo(),
                    item_id=str(payload.get("item_id") or "").strip() or None,
                    submit=bool(payload.get("submit", True)),
                    evaluator_id="control_plane",
                    host=socket.gethostname(),
                    executor="@control_plane",
                    pr_base="master",
                ),
            )
        return _json_response(200, {"results": [row.__dict__ for row in result]})

    def poll_github_handler(_method: str, _path: str, _params: dict[str, str], _body: bytes):
        engine = build_engine(settings.database_url)
        create_all(engine)
        session_factory = build_session_factory(engine)
        with session_factory() as session:
            result = poll_github_links(session, GitHubPollRequest(repo_root=_service_repo_root(), repo=_github_repo()))
        return _json_response(200, result.__dict__)


    def dispatch_ready_handler(_method: str, _path: str, _params: dict[str, str], body: bytes):
        payload = _json_body(body)
        engine = build_engine(settings.database_url)
        create_all(engine)
        session_factory = build_session_factory(engine)
        with session_factory() as session:
            result = dispatch_ready_items(
                session,
                DispatchReadyRequest(
                    max_assignments=int(payload.get("max_assignments")) if payload.get("max_assignments") is not None else None,
                    freshness_seconds=int(payload.get("freshness_seconds", 120)),
                ),
            )
        return _json_response(200, {"results": [row.__dict__ for row in result]})

    def backfill_review_handler(_method: str, _path: str, _params: dict[str, str], body: bytes):
        payload = _json_body(body)
        engine = build_engine(settings.database_url)
        create_all(engine)
        session_factory = build_session_factory(engine)
        with session_factory() as session:
            result = backfill_review_states(session, ReviewStateBackfillRequest(item_id=str(payload.get("item_id") or "").strip() or None))
        return _json_response(200, {"results": [row.__dict__ for row in result]})

    def submit_item_handler(_method: str, _path: str, params: dict[str, str], body: bytes):
        payload = _json_body(body)
        engine = build_engine(settings.database_url)
        create_all(engine)
        session_factory = build_session_factory(engine)
        with session_factory() as session:
            result = process_completed_items(
                session,
                CompletionProcessRequest(
                    repo_root=_service_repo_root(),
                    repo=_github_repo(),
                    item_id=params["item_id"],
                    submit=True,
                    evaluator_id="control_plane",
                    host=socket.gethostname(),
                    executor="@control_plane",
                    pr_base="master",
                    force=bool(payload.get("force", False)),
                ),
            )
        if not result:
            raise ValueError(f"no completion result for item: {params['item_id']}")
        return _json_response(200, {"results": [row.__dict__ for row in result]})

    def supersede_item_handler(_method: str, _path: str, params: dict[str, str], body: bytes):
        payload = _json_body(body)
        engine = build_engine(settings.database_url)
        create_all(engine)
        session_factory = build_session_factory(engine)
        with session_factory() as session:
            result = _supersede_item(
                session,
                item_id=params["item_id"],
                reason=str(payload.get("reason") or "operator_control"),
                actor="dashboard",
            )
        return _json_response(200, result)

    def guarded(handler):
        def wrapper(method: str, path: str, params: dict[str, str], body: bytes):
            try:
                return handler(method, path, params, body)
            except (ValueError, CompletionProcessingError) as exc:
                return _json_response(400, {"detail": str(exc)})
            except Exception as exc:  # pragma: no cover - defensive API boundary
                return _json_response(500, {"detail": str(exc)})
        return wrapper

    app.add_route("POST", "/api/v1/control/process-completions", guarded(process_completions_handler))
    app.add_route("POST", "/api/v1/control/dispatch-ready", guarded(dispatch_ready_handler))
    app.add_route("POST", "/api/v1/control/poll-github", guarded(poll_github_handler))
    app.add_route("POST", "/api/v1/control/backfill-review-states", guarded(backfill_review_handler))
    app.add_route("POST", "/api/v1/control/items/{item_id}/submit", guarded(submit_item_handler))
    app.add_route("POST", "/api/v1/control/items/{item_id}/supersede", guarded(supersede_item_handler))
