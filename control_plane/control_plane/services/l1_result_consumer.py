"""Layer 1 result consumption helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timezone
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from sqlalchemy.orm import Session

from control_plane.clock import utcnow
from control_plane.models.artifacts import Artifact
from control_plane.models.enums import ArtifactStorageMode, RunStatus, WorkItemState
from control_plane.models.run_events import RunEvent
from control_plane.models.runs import Run
from control_plane.models.work_items import WorkItem


class Layer1ResultConsumerError(RuntimeError):
    pass


@dataclass(frozen=True)
class Layer1ConsumeRequest:
    repo_root: str
    item_id: str | None = None
    run_key: str | None = None
    target_path: str | None = None


@dataclass(frozen=True)
class Layer1ConsumeResult:
    item_id: str
    run_key: str
    target_path: str
    proposal_count: int
    work_item_state: str


def _default_target_path(*, item_id: str) -> str:
    return f"control_plane/shadow_exports/l1_promotions/{item_id}.json"


def _resolve_path(*, repo_root: Path, path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return repo_root / path


def _resolve_run(session: Session, request: Layer1ConsumeRequest) -> tuple[WorkItem, Run]:
    if request.run_key:
        run = session.query(Run).filter(Run.run_key == request.run_key).one_or_none()
        if run is None:
            raise Layer1ResultConsumerError(f"run not found: {request.run_key}")
        return run.work_item, run
    if not request.item_id:
        raise Layer1ResultConsumerError("item_id or run_key is required")
    work_item = session.query(WorkItem).filter(WorkItem.item_id == request.item_id).one_or_none()
    if work_item is None:
        raise Layer1ResultConsumerError(f"work item not found: {request.item_id}")
    if not work_item.runs:
        raise Layer1ResultConsumerError(f"work item has no runs: {request.item_id}")
    run = sorted(work_item.runs, key=lambda row: (row.attempt, row.created_at or utcnow()))[-1]
    return work_item, run


def _safe_float(value: str | None) -> float | None:
    if value in ("", None):
        return None
    try:
        return float(str(value).strip())
    except ValueError:
        return None


def _row_sort_key(row: dict[str, Any]) -> tuple[float, float, float, str, str]:
    cp = _safe_float(row.get("critical_path_ns"))
    area = _safe_float(row.get("die_area"))
    power = _safe_float(row.get("total_power_mw"))
    return (
        cp if cp is not None else float("inf"),
        area if area is not None else float("inf"),
        power if power is not None else float("inf"),
        str(row.get("param_hash", "")),
        str(row.get("tag", "")),
    )


def _load_metrics_rows(path: Path) -> list[dict[str, str]]:
    # Match the tolerant parsing used by scripts/build_runs_index.py because
    # historical metrics.csv rows may carry unquoted JSON in params_json.
    text = path.read_text(encoding="utf-8", errors="ignore")
    text = re.sub(r"result\.json(?=[A-Za-z0-9_])", "result.json\n", text)
    lines = text.splitlines()
    if not lines:
        return []
    header = lines[0].split(",")
    rows: list[dict[str, str]] = []
    for line in lines[1:]:
        if not line.strip():
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


def _best_metrics_row(*, repo_root: Path, metrics_csv: str) -> dict[str, Any] | None:
    path = _resolve_path(repo_root=repo_root, path_text=metrics_csv)
    if not path.exists():
        return None
    rows: list[dict[str, Any]] = []
    for row in _load_metrics_rows(path):
        if str(row.get("status", "")).strip() != "ok":
            continue
        rows.append(dict(row))
    if not rows:
        return None
    return sorted(rows, key=_row_sort_key)[0]


def _proposal_entry(*, metrics_csv: str, best_row: dict[str, Any]) -> dict[str, Any]:
    proposal: dict[str, Any] = {
        "metrics_ref": {
            "metrics_csv": metrics_csv,
            "platform": str(best_row.get("platform", "")).strip(),
            "status": str(best_row.get("status", "")).strip(),
        },
        "selection_reason": "lowest critical_path_ns, then die_area, then total_power_mw among status=ok rows",
    }
    for key in ("param_hash", "tag", "run_id", "sample_id", "batch_id", "result_path", "work_result_json"):
        value = str(best_row.get(key, "")).strip()
        if value:
            proposal["metrics_ref"][key] = value

    summary: dict[str, Any] = {}
    for key in ("critical_path_ns", "die_area", "total_power_mw"):
        value = _safe_float(best_row.get(key))
        if value is not None:
            summary[key] = value
    if summary:
        proposal["metric_summary"] = summary
    return proposal


def _build_payload(*, work_item: WorkItem, run: Run, proposals: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "version": 0.1,
        "generated_utc": utcnow().astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "item_id": work_item.item_id,
        "run_key": run.run_key,
        "layer": work_item.layer.value,
        "flow": work_item.flow.value,
        "platform": work_item.platform,
        "task_type": work_item.task_type,
        "source_commit": run.checkout_commit or work_item.source_commit,
        "objective": work_item.task_request.description,
        "input_manifest": work_item.input_manifest,
        "proposal_count": len(proposals),
        "proposals": proposals,
    }


def _upsert_artifact(session: Session, *, run: Run, target_path: str, payload: dict[str, Any]) -> None:
    artifact = (
        session.query(Artifact)
        .filter(Artifact.run_id == run.id, Artifact.kind == "promotion_proposal")
        .one_or_none()
    )
    sha256 = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    if artifact is None:
        artifact = Artifact(
            run_id=run.id,
            kind="promotion_proposal",
            storage_mode=ArtifactStorageMode.REPO,
            path=target_path,
            sha256=sha256,
            metadata_={"proposal_count": len(payload.get("proposals") or [])},
        )
        session.add(artifact)
    else:
        artifact.storage_mode = ArtifactStorageMode.REPO
        artifact.path = target_path
        artifact.sha256 = sha256
        artifact.metadata_ = {"proposal_count": len(payload.get("proposals") or [])}


def consume_l1_result(session: Session, request: Layer1ConsumeRequest) -> Layer1ConsumeResult:
    repo_root = Path(request.repo_root).resolve()
    work_item, run = _resolve_run(session, request)
    if work_item.task_type != "l1_sweep":
        raise Layer1ResultConsumerError(f"work item is not l1_sweep: {work_item.item_id}")
    if run.status != RunStatus.SUCCEEDED:
        raise Layer1ResultConsumerError(f"run is not succeeded: {run.run_key} status={run.status.value}")

    metrics_csvs = [
        str(path)
        for path in (work_item.expected_outputs or [])
        if str(path).endswith("/metrics.csv") or str(path).endswith("metrics.csv")
    ]
    proposals: list[dict[str, Any]] = []
    for metrics_csv in metrics_csvs:
        best_row = _best_metrics_row(repo_root=repo_root, metrics_csv=metrics_csv)
        if best_row is None:
            continue
        proposals.append(_proposal_entry(metrics_csv=metrics_csv, best_row=best_row))

    if not proposals:
        raise Layer1ResultConsumerError(f"no status=ok metrics rows found for work item: {work_item.item_id}")

    payload = _build_payload(work_item=work_item, run=run, proposals=proposals)
    target_rel = request.target_path or _default_target_path(item_id=work_item.item_id)
    target_path = _resolve_path(repo_root=repo_root, path_text=target_rel)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    _upsert_artifact(session, run=run, target_path=str(target_path.relative_to(repo_root)), payload=payload)
    work_item.state = WorkItemState.AWAITING_REVIEW
    session.add(
        RunEvent(
            run_id=run.id,
            event_time=utcnow(),
            event_type="l1_promotion_proposed",
            event_payload={
                "target_path": str(target_path.relative_to(repo_root)),
                "proposal_count": len(proposals),
            },
        )
    )
    session.commit()
    return Layer1ConsumeResult(
        item_id=work_item.item_id,
        run_key=run.run_key,
        target_path=str(target_path),
        proposal_count=len(proposals),
        work_item_state=work_item.state.value,
    )
