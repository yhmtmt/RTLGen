"""Queue snapshot exporter for cp-006."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from control_plane.models.enums import QueueReconciliationDirection, QueueReconciliationStatus, RunStatus, WorkItemState
from control_plane.models.queue_reconciliations import QueueReconciliation
from control_plane.models.runs import Run
from control_plane.models.work_items import WorkItem


class QueueExportError(RuntimeError):
    pass


class QueueExportConflict(QueueExportError):
    pass


@dataclass(frozen=True)
class QueueExportRequest:
    repo_root: str
    item_id: str
    target_state: str
    target_path: str | None = None

    def resolve_path(self, fallback: str | None = None) -> Path:
        candidate = self.target_path or fallback
        if not candidate:
            raise QueueExportError("target_path is required when no fallback queue path exists")
        path = Path(candidate)
        if path.is_absolute():
            return path
        return Path(self.repo_root) / path


@dataclass(frozen=True)
class QueueExportResult:
    item_id: str
    target_state: str
    target_path: str
    reconciliation_id: str
    queue_sha256: str


def _json_sha256(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    from hashlib import sha256

    return sha256(canonical).hexdigest()


def _record_reconciliation(
    session: Session,
    *,
    item_id: str,
    queue_path: str,
    queue_sha256: str,
    db_work_item_id: str,
    status: QueueReconciliationStatus,
    message: str,
) -> QueueReconciliation:
    row = QueueReconciliation(
        item_id=item_id,
        direction=QueueReconciliationDirection.EXPORT,
        queue_path=queue_path,
        queue_sha256=queue_sha256,
        db_work_item_id=db_work_item_id,
        status=status,
        message=message,
    )
    session.add(row)
    session.flush()
    return row


def _default_path_for_state(item_id: str, target_state: str) -> str:
    folder = "evaluated" if target_state == "evaluated" else "queued"
    return f"runs/eval_queue/openroad/{folder}/{item_id}.json"


def _find_latest_run(work_item: WorkItem) -> Run | None:
    if not work_item.runs:
        return None
    return sorted(work_item.runs, key=lambda run: (run.attempt, run.created_at))[ -1 ]


def _status_to_queue_status(run_status: RunStatus) -> str:
    if run_status == RunStatus.SUCCEEDED:
        return "ok"
    if run_status in {RunStatus.FAILED, RunStatus.CANCELED, RunStatus.TIMED_OUT}:
        return "fail"
    raise QueueExportError(f"cannot map non-terminal run status to evaluated queue result: {run_status.value}")


def _merge_result(run: Run, work_item: WorkItem) -> dict[str, Any]:
    payload = deepcopy(run.result_payload or {})
    queue_result = deepcopy(payload.get("queue_result") or {})

    queue_result.setdefault("completed_utc", run.completed_at.isoformat() if run.completed_at else None)
    queue_result.setdefault("executor", run.executor_type.value)
    queue_result.setdefault("branch", run.branch_name)
    queue_result.setdefault("queue_item_id", work_item.item_id)
    queue_result.setdefault("status", _status_to_queue_status(run.status))
    queue_result.setdefault("summary", run.result_summary)

    if queue_result["status"] == "ok":
        metrics_rows = queue_result.get("metrics_rows")
        if not isinstance(metrics_rows, list) or not metrics_rows:
            raise QueueExportError(
                f"evaluated export for {work_item.item_id} requires non-empty queue_result.metrics_rows when status=ok"
            )

    export_keys = (
        "branch",
        "completed_utc",
        "evaluator_id",
        "executor",
        "host",
        "identity_block",
        "metrics_rows",
        "queue_item_id",
        "session_id",
        "status",
        "summary",
    )
    return {key: queue_result[key] for key in export_keys if key in queue_result}


def export_queue_item(session: Session, request: QueueExportRequest) -> QueueExportResult:
    work_item = session.query(WorkItem).filter(WorkItem.item_id == request.item_id).one_or_none()
    if work_item is None:
        raise QueueExportError(f"work item not found: {request.item_id}")

    source_payload = deepcopy(work_item.task_request.request_payload or {})
    if not source_payload:
        raise QueueExportError(f"work item {request.item_id} has no source payload to export")

    target_state = request.target_state
    if target_state not in {"queued", "evaluated"}:
        raise QueueExportError(f"unsupported target_state: {target_state}")

    export_payload = deepcopy(source_payload)
    export_payload["state"] = target_state
    export_payload["item_id"] = work_item.item_id
    export_payload["title"] = work_item.task_request.title
    export_payload["layer"] = work_item.layer.value
    export_payload["flow"] = work_item.flow.value
    export_payload["priority"] = work_item.priority
    export_payload["requested_by"] = work_item.task_request.requested_by
    export_payload["platform"] = work_item.platform

    fallback_path = _default_path_for_state(work_item.item_id, target_state)
    target_path = request.resolve_path(fallback=fallback_path)

    if target_state == "queued":
        export_payload["result"] = None
    else:
        latest_run = _find_latest_run(work_item)
        if latest_run is None:
            raise QueueExportError(f"evaluated export for {work_item.item_id} requires at least one run")
        if latest_run.status not in {RunStatus.SUCCEEDED, RunStatus.FAILED, RunStatus.CANCELED, RunStatus.TIMED_OUT}:
            raise QueueExportConflict(
                f"evaluated export for {work_item.item_id} requires a terminal run, found {latest_run.status.value}"
            )
        export_payload["result"] = _merge_result(latest_run, work_item)

    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(json.dumps(export_payload, indent=2) + "\n", encoding="utf-8")
    queue_sha = _json_sha256(export_payload)
    reconciliation = _record_reconciliation(
        session,
        item_id=work_item.item_id,
        queue_path=str(target_path),
        queue_sha256=queue_sha,
        db_work_item_id=work_item.id,
        status=QueueReconciliationStatus.APPLIED,
        message=f"exported queue item as {target_state}",
    )
    session.commit()
    return QueueExportResult(
        item_id=work_item.item_id,
        target_state=target_state,
        target_path=str(target_path),
        reconciliation_id=reconciliation.id,
        queue_sha256=queue_sha,
    )
