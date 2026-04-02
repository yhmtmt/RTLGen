"""Queue item importer for cp-003."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import subprocess
import json
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from control_plane.models.enums import FlowName, LayerName, QueueReconciliationDirection, QueueReconciliationStatus, WorkItemState
from control_plane.models.queue_reconciliations import QueueReconciliation
from control_plane.models.task_requests import TaskRequest
from control_plane.models.work_items import WorkItem


_STATE_RANK = {
    WorkItemState.DRAFT: 0,
    WorkItemState.DISPATCH_PENDING: 1,
    WorkItemState.READY: 2,
    WorkItemState.LEASED: 3,
    WorkItemState.RUNNING: 3,
    WorkItemState.ARTIFACT_SYNC: 4,
    WorkItemState.AWAITING_REVIEW: 5,
    WorkItemState.MERGED: 6,
    WorkItemState.FAILED: 90,
    WorkItemState.BLOCKED: 91,
    WorkItemState.SUPERSEDED: 92,
}


class QueueImportError(RuntimeError):
    pass


class QueueImportConflict(QueueImportError):
    pass


@dataclass(frozen=True)
class QueueImportResult:
    item_id: str
    status: str
    work_item_id: str
    reconciliation_id: str
    queue_path: str
    queue_sha256: str


@dataclass(frozen=True)
class QueueImportRequest:
    repo_root: str
    queue_path: str
    source_commit: str | None = None
    mode: str = "upsert"

    def resolve_path(self) -> Path:
        path = Path(self.queue_path)
        if path.is_absolute():
            return path
        return Path(self.repo_root) / path


def _json_sha256(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(canonical).hexdigest()


def _semantic_payload(payload: dict[str, Any]) -> dict[str, Any]:
    handoff = payload.get("handoff") or {}
    semantic_handoff = {
        "branch": handoff.get("branch"),
        "pr_title": handoff.get("pr_title"),
        "identity_block_format": handoff.get("identity_block_format"),
        "checklist": handoff.get("checklist"),
    }
    return {
        "version": payload.get("version"),
        "item_id": payload.get("item_id"),
        "title": payload.get("title"),
        "layer": payload.get("layer"),
        "flow": payload.get("flow"),
        "priority": payload.get("priority"),
        "created_utc": payload.get("created_utc"),
        "requested_by": payload.get("requested_by"),
        "platform": payload.get("platform"),
        "task": payload.get("task"),
        "handoff": semantic_handoff,
    }


def _queue_state_to_work_item_state(queue_state: str) -> WorkItemState:
    if queue_state == "evaluated":
        return WorkItemState.AWAITING_REVIEW
    return WorkItemState.DISPATCH_PENDING


def _resolve_source_commit(repo_root: Path, source_commit: str | None) -> str | None:
    resolved = str(source_commit or "").strip()
    if not resolved:
        return None
    try:
        subprocess.run(
            ["git", "-C", str(repo_root), "cat-file", "-e", f"{resolved}^{{commit}}"],
            check=True,
            capture_output=True,
            text=True,
        )
        result = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", f"{resolved}^{{commit}}"],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        detail = f": {stderr}" if stderr else ""
        raise QueueImportError(
            f"provided source_commit does not resolve to a commit in repo_root {repo_root}: {resolved}{detail}"
        ) from exc
    normalized = result.stdout.strip()
    if not normalized:
        raise QueueImportError(
            f"provided source_commit resolved to empty git rev-parse output in repo_root {repo_root}: {resolved}"
        )
    return normalized


def _merge_state(current: WorkItemState, imported: WorkItemState) -> WorkItemState:
    return imported if _STATE_RANK[imported] > _STATE_RANK[current] else current


def _derive_task_type(payload: dict[str, Any]) -> str:
    task = payload.get("task") or {}
    commands = task.get("commands") or []
    command_names = [cmd.get("name") for cmd in commands if isinstance(cmd, dict)]
    if payload.get("layer") == "layer1":
        if "run_eval" in command_names:
            return "l1_sweep"
        return "layer1_queue_item"
    if payload.get("layer") == "layer2":
        if "run_campaign" in command_names:
            return "l2_campaign"
        return "layer2_queue_item"
    return "queue_item"


def _record_reconciliation(
    session: Session,
    *,
    item_id: str,
    queue_path: str,
    queue_sha256: str,
    status: QueueReconciliationStatus,
    db_work_item_id: str | None,
    message: str,
) -> QueueReconciliation:
    row = QueueReconciliation(
        item_id=item_id,
        direction=QueueReconciliationDirection.IMPORT,
        queue_path=queue_path,
        queue_sha256=queue_sha256,
        db_work_item_id=db_work_item_id,
        status=status,
        message=message,
    )
    session.add(row)
    session.flush()
    return row


def import_queue_item(session: Session, request: QueueImportRequest) -> QueueImportResult:
    repo_root = Path(request.repo_root)
    resolved_source_commit = _resolve_source_commit(repo_root, request.source_commit)

    queue_file = request.resolve_path()
    if not queue_file.exists():
        raise QueueImportError(f"queue file not found: {queue_file}")

    payload = json.loads(queue_file.read_text(encoding="utf-8"))
    item_id = payload.get("item_id")
    if not item_id:
        raise QueueImportError(f"queue item missing item_id: {queue_file}")

    queue_sha = _json_sha256(payload)
    semantic_payload = _semantic_payload(payload)
    semantic_sha = _json_sha256(semantic_payload)

    existing = session.query(WorkItem).filter(WorkItem.item_id == item_id).one_or_none()
    if existing is None:
        task_request = TaskRequest(
            request_key=f"queue:{item_id}",
            source="git_queue_import",
            requested_by=payload.get("requested_by", "unknown"),
            title=payload.get("title", item_id),
            description=payload.get("task", {}).get("objective", ""),
            layer=LayerName(payload.get("layer")),
            flow=FlowName(payload.get("flow")),
            priority=int(payload.get("priority", 1)),
            request_payload=payload,
            source_commit=resolved_source_commit,
        )
        session.add(task_request)
        session.flush()

        work_item = WorkItem(
            work_item_key=f"queue:{item_id}",
            task_request_id=task_request.id,
            item_id=item_id,
            layer=LayerName(payload.get("layer")),
            flow=FlowName(payload.get("flow")),
            platform=payload.get("platform", "unknown"),
            task_type=_derive_task_type(payload),
            state=_queue_state_to_work_item_state(payload.get("state", "queued")),
            priority=int(payload.get("priority", 1)),
            source_mode=(payload.get("task") or {}).get("source_mode"),
            input_manifest=(payload.get("task") or {}).get("inputs") or {},
            command_manifest=(payload.get("task") or {}).get("commands") or [],
            expected_outputs=(payload.get("task") or {}).get("expected_outputs") or [],
            acceptance_rules=(payload.get("task") or {}).get("acceptance") or [],
            queue_snapshot_path=str(queue_file),
            source_commit=resolved_source_commit,
        )
        session.add(work_item)
        session.flush()
        reconciliation = _record_reconciliation(
            session,
            item_id=item_id,
            queue_path=str(queue_file),
            queue_sha256=queue_sha,
            status=QueueReconciliationStatus.APPLIED,
            db_work_item_id=work_item.id,
            message="imported new queue item",
        )
        session.commit()
        return QueueImportResult(
            item_id=item_id,
            status="applied",
            work_item_id=work_item.id,
            reconciliation_id=reconciliation.id,
            queue_path=str(queue_file),
            queue_sha256=queue_sha,
        )

    existing_payload = existing.task_request.request_payload
    existing_semantic_sha = _json_sha256(_semantic_payload(existing_payload))
    if existing_semantic_sha != semantic_sha:
        reconciliation = _record_reconciliation(
            session,
            item_id=item_id,
            queue_path=str(queue_file),
            queue_sha256=queue_sha,
            status=QueueReconciliationStatus.CONFLICT,
            db_work_item_id=existing.id,
            message="queue item semantic payload conflicts with existing work item",
        )
        session.commit()
        raise QueueImportConflict(
            f"semantic conflict for item_id={item_id}; reconciliation_id={reconciliation.id}"
        )

    changed = False
    if existing_payload != payload:
        existing.task_request.request_payload = payload
        existing.task_request.requested_by = payload.get("requested_by", existing.task_request.requested_by)
        existing.task_request.title = payload.get("title", existing.task_request.title)
        existing.task_request.description = (payload.get("task") or {}).get("objective", existing.task_request.description)
        existing.task_request.priority = int(payload.get("priority", existing.task_request.priority))
        existing.task_request.source_commit = request.source_commit
        changed = True

    imported_state = _queue_state_to_work_item_state(payload.get("state", "queued"))
    merged_state = _merge_state(existing.state, imported_state)
    if merged_state != existing.state:
        existing.state = merged_state
        changed = True

    new_queue_path = str(queue_file)
    if existing.queue_snapshot_path != new_queue_path:
        existing.queue_snapshot_path = new_queue_path
        changed = True

    if resolved_source_commit and existing.source_commit != resolved_source_commit:
        existing.source_commit = resolved_source_commit
        changed = True

    if changed:
        existing.priority = int(payload.get("priority", existing.priority))
        existing.platform = payload.get("platform", existing.platform)
        existing.source_mode = (payload.get("task") or {}).get("source_mode")
        existing.input_manifest = (payload.get("task") or {}).get("inputs") or {}
        existing.command_manifest = (payload.get("task") or {}).get("commands") or []
        existing.expected_outputs = (payload.get("task") or {}).get("expected_outputs") or []
        existing.acceptance_rules = (payload.get("task") or {}).get("acceptance") or []

    reconciliation = _record_reconciliation(
        session,
        item_id=item_id,
        queue_path=str(queue_file),
        queue_sha256=queue_sha,
        status=QueueReconciliationStatus.APPLIED if changed else QueueReconciliationStatus.SKIPPED,
        db_work_item_id=existing.id,
        message="updated existing queue item" if changed else "queue item already imported with matching content",
    )
    session.commit()
    return QueueImportResult(
        item_id=item_id,
        status="applied" if changed else "skipped",
        work_item_id=existing.id,
        reconciliation_id=reconciliation.id,
        queue_path=str(queue_file),
        queue_sha256=queue_sha,
    )
