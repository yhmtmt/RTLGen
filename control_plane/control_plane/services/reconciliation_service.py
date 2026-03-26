"""Artifact-sync and queue round-trip helpers for completed internal runs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import copy
import csv
from pathlib import Path
import re
import socket
from typing import Any

from sqlalchemy.orm import Session

from control_plane.clock import utcnow
from control_plane.models.artifacts import Artifact
from control_plane.models.enums import ArtifactStorageMode, RunStatus, WorkItemState
from control_plane.models.run_events import RunEvent
from control_plane.models.runs import Run
from control_plane.models.work_items import WorkItem
from control_plane.services.dependency_gate import evaluate_work_item_dependencies
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


def _session_id_from_branch(branch_name: str | None) -> str | None:
    text = str(branch_name or "").strip()
    if not text:
        return None
    match = re.search(r"/(s[0-9]{8}t[0-9]{6}z)$", text)
    if match:
        return match.group(1)
    return None


def _default_shadow_target_path(*, item_id: str) -> str:
    return f"control_plane/shadow_exports/evaluated/{item_id}.json"


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


def _fill_handoff_placeholders(
    *,
    source_payload: dict[str, Any] | None,
    evaluator_id: str,
    session_id: str,
    host: str,
    queue_item_id: str,
    branch_name: str,
) -> dict[str, Any] | None:
    if not isinstance(source_payload, dict):
        return source_payload
    handoff = source_payload.get("handoff")
    if not isinstance(handoff, dict):
        return source_payload

    branch_template = str(handoff.get("branch", "")).strip()
    if branch_template:
        handoff["branch"] = (
            branch_template
            .replace("<session_id>", session_id)
            .replace("<evaluator_id>", evaluator_id)
            .replace("<host>", host)
            .replace("<queue_item_id>", queue_item_id)
        )
    else:
        handoff["branch"] = branch_name

    pr_body_fields = handoff.get("pr_body_fields")
    if isinstance(pr_body_fields, dict):
        pr_body_fields = dict(pr_body_fields)
        pr_body_fields["evaluator_id"] = evaluator_id
        pr_body_fields["session_id"] = session_id
        pr_body_fields["host"] = host
        pr_body_fields["queue_item_id"] = queue_item_id
        handoff["pr_body_fields"] = pr_body_fields
    return source_payload


def _relative_repo_path(path_text: str, repo_root: Path) -> str:
    path = Path(path_text)
    if not path.is_absolute():
        return str(path)
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path.resolve())


def _portable_repo_path(path_text: str, repo_root: Path) -> str | None:
    path_text = str(path_text).strip()
    if not path_text:
        return None
    path = Path(path_text)
    if not path.is_absolute():
        return str(path)
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return None


def _looks_like_result_path(path_text: str) -> bool:
    text = str(path_text).strip()
    if not text:
        return False
    if "\n" in text or "\r" in text:
        return False
    if not (text.endswith(".json") or text.endswith(".rpt") or text.endswith(".def")):
        return False
    return ("/" in text) or ("\\" in text)


def _portable_metrics_result_path(row: dict[str, Any], repo_root: Path) -> str | None:
    raw_result_path = str(row.get("result_path", "")).strip()
    result_path = _portable_repo_path(raw_result_path, repo_root) if _looks_like_result_path(raw_result_path) else None
    if result_path:
        return result_path
    raw_work_result_json = str(row.get("work_result_json", "")).strip()
    work_result_json = (
        _portable_repo_path(raw_work_result_json, repo_root) if _looks_like_result_path(raw_work_result_json) else None
    )
    if work_result_json:
        return work_result_json
    return None


def _metrics_row_matches_ref(candidate: dict[str, Any], ref: dict[str, Any]) -> bool:
    if str(candidate.get("platform", "")).strip() != str(ref.get("platform", "")).strip():
        return False
    if str(candidate.get("status", "")).strip() != str(ref.get("status", "")).strip():
        return False

    for key in ("param_hash", "tag", "run_id", "sample_id", "batch_id"):
        wanted = str(ref.get(key, "")).strip()
        if wanted and str(candidate.get(key, "")).strip() != wanted:
            return False

    sample_index = ref.get("sample_index", "")
    if sample_index not in ("", None) and str(candidate.get("sample_index", "")).strip() != str(sample_index).strip():
        return False

    return True


def _recover_metrics_result_path_from_csv(row: dict[str, Any], repo_root: Path) -> str | None:
    metrics_csv = str(row.get("metrics_csv", "")).strip()
    if not metrics_csv:
        return None
    path = (repo_root / metrics_csv).resolve()
    if not path.exists():
        return None
    for candidate in _load_metrics_rows(path):
        if _metrics_row_matches_ref(candidate, row):
            return _portable_metrics_result_path(candidate, repo_root)
    return None


def _load_metrics_rows(path: Path) -> list[dict[str, str]]:
    # Prefer standard CSV parsing for modern quoted metrics.csv rows. Fall back
    # to the historical tolerant parser for legacy rows with unquoted JSON.
    text = path.read_text(encoding="utf-8", errors="ignore")
    if not text.strip():
        return []

    with path.open("r", encoding="utf-8", newline="") as handle:
        parsed = [{str(key): str(value) for key, value in row.items()} for row in csv.DictReader(handle)]
    if parsed and all(None not in row for row in parsed):
        return parsed

    text = re.sub(r"result\.json(?=[A-Za-z0-9_])", "result.json\n", text)
    lines = text.splitlines()
    if not lines:
        return []
    header = lines[0].split(",")
    rows: list[dict[str, str]] = []
    for line in lines[1:]:
        if not line.strip():
            continue
        if "params_json" not in header:
            reader = csv.DictReader([",".join(header), line])
            candidate = next(reader, None)
            if candidate is not None:
                rows.append({str(key): str(value) for key, value in candidate.items()})
            continue
        parts = line.split(",", 9)
        if len(parts) < 10:
            continue
        front = parts[:9]
        rest = parts[9]
        if "," in rest:
            params_json, result_path = rest.rsplit(",", 1)
        else:
            params_json, result_path = rest, ""
        params_json = params_json.strip()
        if len(params_json) >= 2 and params_json[0] == '"' and params_json[-1] == '"':
            params_json = params_json[1:-1].replace('""', '"')
        values = front + [params_json, result_path]
        if len(values) != len(header):
            continue
        rows.append(dict(zip(header, values)))
    return rows


def _normalize_metrics_csv_refs(*, repo_root: Path, metrics_csv: str, allow_missing: bool = False) -> list[dict[str, Any]]:
    path = (repo_root / metrics_csv).resolve()
    if not path.exists():
        if allow_missing:
            return []
        raise ArtifactSyncError(f"metrics csv not found: {metrics_csv}")
    rows: list[dict[str, Any]] = []
    for row in _load_metrics_rows(path):
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
        result_path = _portable_metrics_result_path(row, repo_root)
        if result_path:
            ref["result_path"] = result_path
        rows.append(ref)
    return rows


def _normalize_metrics_rows(
    *,
    repo_root: Path,
    work_item: WorkItem,
    queue_result: dict[str, Any],
) -> list[dict[str, Any]]:
    status = str(queue_result.get("status", "")).strip()
    metrics_rows = queue_result.get("metrics_rows")
    if isinstance(metrics_rows, list) and metrics_rows and all(isinstance(row, dict) for row in metrics_rows):
        normalized: list[dict[str, Any]] = []
        for row in metrics_rows:
            new_row = dict(row)
            result_path = _portable_metrics_result_path(new_row, repo_root)
            if not result_path:
                result_path = _recover_metrics_result_path_from_csv(new_row, repo_root)
            if result_path:
                new_row["result_path"] = result_path
            else:
                new_row.pop("result_path", None)
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
        normalized_rows.extend(
            _normalize_metrics_csv_refs(
                repo_root=repo_root,
                metrics_csv=metrics_csv,
                allow_missing=(status == "fail"),
            )
        )
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
    if work_item.state not in {WorkItemState.ARTIFACT_SYNC, WorkItemState.AWAITING_REVIEW, WorkItemState.FAILED}:
        raise ArtifactSyncError(
            f"work item {work_item.item_id} is not ready for artifact sync from state={work_item.state.value}"
        )

    queue_result = dict((run.result_payload or {}).get("queue_result") or {})
    queue_result["metrics_rows"] = _normalize_metrics_rows(
        repo_root=repo_root,
        work_item=work_item,
        queue_result=queue_result,
    )
    requested_branch_name = request.branch_name or run.branch_name
    session_id = request.session_id or _session_id_from_branch(requested_branch_name) or _default_session_id()
    host = request.host or (run.machine.hostname if run.machine is not None else None) or socket.gethostname()
    branch_name = requested_branch_name or f"eval/{work_item.item_id}/{session_id}"
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
    original_request_payload = copy.deepcopy(dict(work_item.task_request.request_payload or {}))
    work_item.task_request.request_payload = _fill_handoff_placeholders(
        source_payload=copy.deepcopy(original_request_payload),
        evaluator_id=request.evaluator_id,
        session_id=session_id,
        host=host,
        queue_item_id=work_item.item_id,
        branch_name=branch_name,
    )

    export_result = export_queue_item(
        session,
        QueueExportRequest(
            repo_root=str(repo_root),
            item_id=work_item.item_id,
            target_state="evaluated",
            target_path=request.target_path or _default_shadow_target_path(item_id=work_item.item_id),
        ),
    )
    work_item.task_request.request_payload = original_request_payload

    _ensure_queue_snapshot_artifact(
        session,
        run=run,
        target_path=_relative_repo_path(export_result.target_path, repo_root),
        queue_sha256=export_result.queue_sha256,
    )
    gate = evaluate_work_item_dependencies(session, repo_root=repo_root, work_item=work_item)
    work_item.state = WorkItemState.ARTIFACT_SYNC if gate.satisfied else WorkItemState.BLOCKED
    session.add(
        RunEvent(
            run_id=run.id,
            event_time=utcnow(),
            event_type="artifact_synced",
            event_payload={
                "target_path": _relative_repo_path(export_result.target_path, repo_root),
                "queue_sha256": export_result.queue_sha256,
                "dependency_gate_satisfied": gate.satisfied,
                "dependency_gate_reason": gate.reason,
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
