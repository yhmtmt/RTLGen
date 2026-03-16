"""Review package publishing for DB-native completed runs."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from control_plane.clock import utcnow
from control_plane.models.artifacts import Artifact
from control_plane.models.enums import ArtifactStorageMode
from control_plane.models.run_events import RunEvent
from control_plane.models.runs import Run
from control_plane.models.work_items import WorkItem
from control_plane.services.reconciliation_service import ArtifactSyncRequest, sync_run_artifacts


class ReviewPublishError(RuntimeError):
    pass


@dataclass(frozen=True)
class ReviewPublishRequest:
    repo_root: str
    item_id: str | None = None
    run_key: str | None = None
    evaluator_id: str = "control_plane"
    session_id: str | None = None
    host: str | None = None
    executor: str = "@control_plane"
    branch_name: str | None = None
    snapshot_target_path: str | None = None
    package_target_path: str | None = None


@dataclass(frozen=True)
class ReviewPublishResult:
    item_id: str
    run_key: str
    snapshot_path: str
    package_path: str
    review_artifact_kind: str | None
    review_artifact_path: str | None
    branch_name: str
    pr_title: str


def _resolve_run(session: Session, request: ReviewPublishRequest) -> tuple[WorkItem, Run]:
    if request.run_key:
        run = session.query(Run).filter(Run.run_key == request.run_key).one_or_none()
        if run is None:
            raise ReviewPublishError(f"run not found: {request.run_key}")
        return run.work_item, run
    if not request.item_id:
        raise ReviewPublishError("item_id or run_key is required")
    work_item = session.query(WorkItem).filter(WorkItem.item_id == request.item_id).one_or_none()
    if work_item is None:
        raise ReviewPublishError(f"work item not found: {request.item_id}")
    if not work_item.runs:
        raise ReviewPublishError(f"work item has no runs: {request.item_id}")
    run = sorted(work_item.runs, key=lambda row: (row.attempt, row.created_at or utcnow()))[-1]
    return work_item, run


def _default_snapshot_path(*, item_id: str) -> str:
    return f"control_plane/shadow_exports/review/{item_id}/evaluated.json"


def _default_package_path(*, item_id: str) -> str:
    return f"control_plane/shadow_exports/review/{item_id}/review_package.json"


def _review_artifact_kind(task_type: str) -> str | None:
    if task_type == "l1_sweep":
        return "promotion_proposal"
    if task_type == "l2_campaign":
        return "decision_proposal"
    return None


def _find_artifact(session: Session, *, run_id: str, kind: str | None) -> Artifact | None:
    if not kind:
        return None
    return (
        session.query(Artifact)
        .filter(Artifact.run_id == run_id, Artifact.kind == kind)
        .order_by(Artifact.created_at.desc())
        .first()
    )


def _resolve_rel_path(path_text: str, repo_root: Path) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return repo_root / path


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _pr_title(work_item: WorkItem) -> str:
    payload = dict(work_item.task_request.request_payload or {})
    handoff = payload.get("handoff")
    if isinstance(handoff, dict):
        title = str(handoff.get("pr_title", "")).strip()
        if title:
            return title
    return f"review: {work_item.task_request.title}"


def _handoff_payload(work_item: WorkItem) -> dict[str, Any]:
    payload = dict(work_item.task_request.request_payload or {})
    handoff = payload.get("handoff")
    return dict(handoff) if isinstance(handoff, dict) else {}


def _developer_loop_payload(work_item: WorkItem) -> dict[str, Any]:
    payload = dict(work_item.task_request.request_payload or {})
    developer_loop = payload.get("developer_loop")
    if not isinstance(developer_loop, dict):
        return {}
    return {str(key): value for key, value in developer_loop.items() if str(value).strip()}


def _materialized_handoff(*, snapshot_payload: dict[str, Any], work_item: WorkItem) -> dict[str, Any]:
    handoff = snapshot_payload.get("handoff")
    if isinstance(handoff, dict):
        return dict(handoff)
    return _handoff_payload(work_item)


def _artifact_summary(*, repo_root: Path, artifact: Artifact | None) -> dict[str, Any] | None:
    if artifact is None:
        return None
    summary: dict[str, Any] = {
        "kind": artifact.kind,
        "path": artifact.path,
        "storage_mode": artifact.storage_mode.value,
        "sha256": artifact.sha256,
    }
    path = _resolve_rel_path(artifact.path, repo_root)
    if path.exists() and path.suffix.lower() == ".json":
        try:
            summary["payload"] = _load_json(path)
        except Exception:
            pass
    return summary


def _build_body_md(
    *,
    work_item: WorkItem,
    run: Run,
    snapshot_path: str,
    review_artifact: Artifact | None,
    snapshot_payload: dict[str, Any],
    handoff: dict[str, Any],
    developer_loop: dict[str, Any],
) -> str:
    result = dict(snapshot_payload.get("result") or {})
    lines = [
        f"## Summary",
        f"- item_id: `{work_item.item_id}`",
        f"- run_key: `{run.run_key}`",
        f"- layer: `{work_item.layer.value}`",
        f"- task_type: `{work_item.task_type}`",
        f"- status: `{result.get('status', '')}`",
        f"- summary: `{result.get('summary', run.result_summary or '')}`",
        f"- queue_snapshot: `{snapshot_path}`",
    ]
    metrics_rows = result.get("metrics_rows")
    if isinstance(metrics_rows, list):
        lines.append(f"- metrics_rows_count: `{len(metrics_rows)}`")
    if review_artifact is not None:
        lines.append(f"- review_artifact: `{review_artifact.kind}` at `{review_artifact.path}`")
    proposal_id = str(developer_loop.get("proposal_id", "")).strip()
    proposal_path = str(developer_loop.get("proposal_path", "")).strip()
    if proposal_id or proposal_path:
        lines.extend(["", "## Developer Context"])
        if proposal_id:
            lines.append(f"- proposal_id: `{proposal_id}`")
        if proposal_path:
            lines.append(f"- proposal_path: `{proposal_path}`")
            lines.append(f"- reviewer_first_read: `{proposal_path}` plus `docs/developer_agent_review.md`")
    checklist = handoff.get("checklist")
    if isinstance(checklist, list) and checklist:
        lines.extend(["", "## Checklist"])
        for item in checklist:
            lines.append(f"- [ ] {item}")
    return "\n".join(lines) + "\n"


def _upsert_review_package_artifact(
    session: Session,
    *,
    run: Run,
    package_path: str,
    payload: dict[str, Any],
) -> None:
    artifact = (
        session.query(Artifact)
        .filter(Artifact.run_id == run.id, Artifact.kind == "review_package")
        .one_or_none()
    )
    sha256 = __import__("hashlib").sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    if artifact is None:
        artifact = Artifact(
            run_id=run.id,
            kind="review_package",
            storage_mode=ArtifactStorageMode.REPO,
            path=package_path,
            sha256=sha256,
            metadata_={},
        )
        session.add(artifact)
    else:
        artifact.storage_mode = ArtifactStorageMode.REPO
        artifact.path = package_path
        artifact.sha256 = sha256
        artifact.metadata_ = {}


def publish_review_package(session: Session, request: ReviewPublishRequest) -> ReviewPublishResult:
    repo_root = Path(request.repo_root).resolve()
    work_item, run = _resolve_run(session, request)

    sync_result = sync_run_artifacts(
        session,
        ArtifactSyncRequest(
            repo_root=str(repo_root),
            item_id=work_item.item_id,
            run_key=run.run_key,
            evaluator_id=request.evaluator_id,
            session_id=request.session_id,
            host=request.host,
            executor=request.executor,
            branch_name=request.branch_name,
            target_path=request.snapshot_target_path or _default_snapshot_path(item_id=work_item.item_id),
        ),
    )

    session.refresh(run)
    session.refresh(work_item)

    snapshot_rel = str(Path(sync_result.target_path).resolve().relative_to(repo_root.resolve()))
    snapshot_payload = _load_json(Path(sync_result.target_path))
    handoff = _materialized_handoff(snapshot_payload=snapshot_payload, work_item=work_item)
    review_kind = _review_artifact_kind(work_item.task_type)
    review_artifact = _find_artifact(session, run_id=run.id, kind=review_kind)
    developer_loop = _developer_loop_payload(work_item)
    branch_name = str((snapshot_payload.get("result") or {}).get("branch", run.branch_name or "")).strip()
    pr_title = _pr_title(work_item)

    package_rel = request.package_target_path or _default_package_path(item_id=work_item.item_id)
    package_path = _resolve_rel_path(package_rel, repo_root)
    package_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "version": 0.1,
        "generated_utc": utcnow().isoformat().replace("+00:00", "Z"),
        "item_id": work_item.item_id,
        "run_key": run.run_key,
        "layer": work_item.layer.value,
        "flow": work_item.flow.value,
        "task_type": work_item.task_type,
        "source_commit": run.checkout_commit or work_item.source_commit,
        "queue_snapshot": {
            "path": snapshot_rel,
            "result": snapshot_payload.get("result"),
        },
        "review_artifact": _artifact_summary(repo_root=repo_root, artifact=review_artifact),
        "developer_loop": developer_loop or None,
        "pr_payload": {
            "branch": branch_name,
            "title": pr_title,
            "body_fields": handoff.get("pr_body_fields"),
            "body_md": _build_body_md(
                work_item=work_item,
                run=run,
                snapshot_path=snapshot_rel,
                review_artifact=review_artifact,
                snapshot_payload=snapshot_payload,
                handoff=handoff,
                developer_loop=developer_loop,
            ),
            "checklist": handoff.get("checklist"),
        },
    }
    package_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    _upsert_review_package_artifact(
        session,
        run=run,
        package_path=str(package_path.relative_to(repo_root)),
        payload=payload,
    )
    session.add(
        RunEvent(
            run_id=run.id,
            event_time=utcnow(),
            event_type="review_package_published",
            event_payload={
                "target_path": str(package_path.relative_to(repo_root)),
                "snapshot_path": snapshot_rel,
                "review_artifact_kind": review_kind,
            },
        )
    )
    session.commit()
    return ReviewPublishResult(
        item_id=work_item.item_id,
        run_key=run.run_key,
        snapshot_path=str(sync_result.target_path),
        package_path=str(package_path),
        review_artifact_kind=review_artifact.kind if review_artifact is not None else None,
        review_artifact_path=review_artifact.path if review_artifact is not None else None,
        branch_name=branch_name,
        pr_title=pr_title,
    )
