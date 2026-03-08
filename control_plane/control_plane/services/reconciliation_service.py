"""Artifact-sync and queue round-trip helpers for completed internal runs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import csv
from pathlib import Path
import socket
from typing import Any

from sqlalchemy.orm import Session

from control_plane.clock import utcnow
from control_plane.models.artifacts import Artifact
from control_plane.models.enums import ArtifactStorageMode, RunStatus, WorkItemState
from control_plane.models.run_events import RunEvent
from control_plane.models.runs import Run
from control_plane.models.work_items import WorkItem
from control_plane.services.queue_exporter import QueueExportRequest, export_queue_item


class ArtifactSyncError(RuntimeError):
    pass


@dataclass(frozen=True)
class ArtifactSyncRequest:
    repo_root: str
    item_id: str | None = None
    run_key: str | None = None
    evaluator_id: str = "control_plane"
    session_id: str | None = None
    host: str | None = None
    executor: str = "@control_plane"
    branch_name: str | None = None
    target_path: str | None = None


@dataclass(frozen=True)
class ArtifactSyncResult:
    item_id: str
    run_key: str
    target_path: str
    work_item_state: str
    metrics_row_count: int
    queue_sha256: str
    reconciliation_id: str


def _default_session_id() -> str:
    return utcnow().strftime("s%Y%m%dt%H%M%Sz").lower()


def _resolve_run(session: Session, request: ArtifactSyncRequest) -> tuple[WorkItem, Run]:
    if request.run_key:
        run = session.query(Run).filter(Run.run_key == request.run_key).one_or_none()
        if run is None:
            raise ArtifactSyncError(f"run not found: {request.run_key}")
        return run.work_item, run
    if not request.item_id:
        raise ArtifactSyncError("item_id or run_key is required")
    work_item = session.query(WorkItem).filter(WorkItem.item_id == request.item_id).one_or_none()
    if work_item is None:
        raise ArtifactSyncError(f"work item not found: {request.item_id}")
    if not work_item.runs:
        raise ArtifactSyncError(f"work item has no runs: {request.item_id}")
    run = sorted(work_item.runs, key=lambda row: (row.attempt, row.created_at or utcnow()))[-1]
    return work_item, run


def _relative_repo_path(path_text: str, repo_root: Path) -> str:
    path = Path(path_text)
    if not path.is_absolute():
        return str(path)
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path.resolve())


def _normalize_metrics_csv_refs(*, repo_root: Path, metrics_csv: str) -> list[dict[str, Any]]:
    path = (repo_root / metrics_csv).resolve()
    if not path.exists():
        raise ArtifactSyncError(f"metrics csv not found: {metrics_csv}")
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            status = str(row.get("status", "")).strip()
            platform = str(row.get("platform", "")).strip()
            param_hash = str(row.get("param_hash", "")).strip()
            tag = str(row.get("tag", "")).strip()
            if not status or not platform or (not param_hash and not tag):
                continue
            ref: dict[str, Any] = {
                "metrics_csv": metrics_csv,
                "platform": platform,
                "status": status,
            }
            for key in ("run_id", "param_hash", "tag", "sample_id", "batch_id"):
                value = str(row.get(key, "")).strip()
                if value:
                    ref[key] = value
            if row.get("sample_index", "") not in ("", None):
                try:
                    ref["sample_index"] = int(str(row.get("sample_index")).strip())
                except ValueError:
                    ref["sample_index"] = str(row.get("sample_index")).strip()
            result_path = str(row.get("result_path", "")).strip()
            if result_path:
                ref["result_path"] = _relative_repo_path(result_path, repo_root)
            rows.append(ref)
    return rows


def _normalize_metrics_rows(
    *,
    repo_root: Path,
    work_item: WorkItem,
    queue_result: dict[str, Any],
) -> list[dict[str, Any]]:
    metrics_rows = queue_result.get("metrics_rows")
    if isinstance(metrics_rows, list) and metrics_rows and all(isinstance(row, dict) for row in metrics_rows):
        normalized: list[dict[str, Any]] = []
        for row in metrics_rows:
            new_row = dict(row)
            if "result_path" in new_row and new_row["result_path"]:
                new_row["result_path"] = _relative_repo_path(str(new_row["result_path"]), repo_root)
            normalized.append(new_row)
        return normalized

    candidate_csvs: list[str] = []
    if isinstance(metrics_rows, list):
        for row in metrics_rows:
            if isinstance(row, str):
                metrics_csv = row.split(":", 1)[0]
                if metrics_csv.endswith("/metrics.csv") or metrics_csv.endswith("metrics.csv"):
                    candidate_csvs.append(metrics_csv)
    if not candidate_csvs:
        for output in work_item.expected_outputs or []:
            if str(output).endswith("/metrics.csv") or str(output).endswith("metrics.csv"):
                candidate_csvs.append(str(output))

    seen = set()
    normalized_rows: list[dict[str, Any]] = []
    for metrics_csv in candidate_csvs:
        if metrics_csv in seen:
            continue
        seen.add(metrics_csv)
        normalized_rows.extend(_normalize_metrics_csv_refs(repo_root=repo_root, metrics_csv=metrics_csv))
    return normalized_rows


def _ensure_queue_snapshot_artifact(
    session: Session,
    *,
    run: Run,
    target_path: str,
    queue_sha256: str,
) -> None:
    artifact = (
        session.query(Artifact)
        .filter(Artifact.run_id == run.id, Artifact.kind == "queue_snapshot")
        .one_or_none()
    )
    if artifact is None:
        artifact = Artifact(
            run_id=run.id,
            kind="queue_snapshot",
            storage_mode=ArtifactStorageMode.REPO,
            path=target_path,
            sha256=queue_sha256,
            metadata_={},
        )
        session.add(artifact)
    else:
        artifact.storage_mode = ArtifactStorageMode.REPO
        artifact.path = target_path
        artifact.sha256 = queue_sha256


def sync_run_artifacts(session: Session, request: ArtifactSyncRequest) -> ArtifactSyncResult:
    repo_root = Path(request.repo_root).resolve()
    work_item, run = _resolve_run(session, request)
    if run.status not in {RunStatus.SUCCEEDED, RunStatus.FAILED, RunStatus.CANCELED, RunStatus.TIMED_OUT}:
        raise ArtifactSyncError(f"run is not terminal: {run.run_key}")
    if work_item.state not in {WorkItemState.ARTIFACT_SYNC, WorkItemState.AWAITING_REVIEW}:
        raise ArtifactSyncError(
            f"work item {work_item.item_id} is not ready for artifact sync from state={work_item.state.value}"
        )

    queue_result = dict((run.result_payload or {}).get("queue_result") or {})
    queue_result["metrics_rows"] = _normalize_metrics_rows(
        repo_root=repo_root,
        work_item=work_item,
        queue_result=queue_result,
    )
    session_id = request.session_id or _default_session_id()
    host = request.host or socket.gethostname()
    branch_name = request.branch_name or run.branch_name or f"eval/{work_item.item_id}/{session_id}"
    queue_result.update(
        {
            "completed_utc": run.completed_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
            if run.completed_at
            else datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "executor": request.executor,
            "branch": branch_name,
            "evaluator_id": request.evaluator_id,
            "session_id": session_id,
            "host": host,
            "queue_item_id": work_item.item_id,
            "identity_block": (
                f"[role:evaluator][account:{request.evaluator_id}]"
                f"[session:{session_id}][host:{host}][item:{work_item.item_id}]"
            ),
            "status": queue_result.get("status")
            or ("ok" if run.status == RunStatus.SUCCEEDED else "fail"),
            "summary": queue_result.get("summary") or run.result_summary,
        }
    )
    if queue_result["status"] == "ok" and not queue_result["metrics_rows"]:
        raise ArtifactSyncError(f"run {run.run_key} has no validator-compatible metrics rows to export")

    payload = dict(run.result_payload or {})
    payload["queue_result"] = queue_result
    run.result_payload = payload
    run.branch_name = branch_name

    export_result = export_queue_item(
        session,
        QueueExportRequest(
            repo_root=str(repo_root),
            item_id=work_item.item_id,
            target_state="evaluated",
            target_path=request.target_path,
        ),
    )

    _ensure_queue_snapshot_artifact(
        session,
        run=run,
        target_path=_relative_repo_path(export_result.target_path, repo_root),
        queue_sha256=export_result.queue_sha256,
    )
    work_item.state = WorkItemState.AWAITING_REVIEW
    session.add(
        RunEvent(
            run_id=run.id,
            event_time=utcnow(),
            event_type="artifact_synced",
            event_payload={
                "target_path": _relative_repo_path(export_result.target_path, repo_root),
                "queue_sha256": export_result.queue_sha256,
            },
        )
    )
    session.commit()
    return ArtifactSyncResult(
        item_id=work_item.item_id,
        run_key=run.run_key,
        target_path=str(export_result.target_path),
        work_item_state=work_item.state.value,
        metrics_row_count=len(queue_result["metrics_rows"]),
        queue_sha256=export_result.queue_sha256,
        reconciliation_id=export_result.reconciliation_id,
    )
