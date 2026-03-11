"""Layer 2 result consumption helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timezone
import csv
import hashlib
import json
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from control_plane.clock import utcnow
from control_plane.models.artifacts import Artifact
from control_plane.models.enums import ArtifactStorageMode, RunStatus, WorkItemState
from control_plane.models.run_events import RunEvent
from control_plane.models.runs import Run
from control_plane.models.work_items import WorkItem


class Layer2ResultConsumerError(RuntimeError):
    pass


@dataclass(frozen=True)
class Layer2ConsumeRequest:
    repo_root: str
    item_id: str | None = None
    run_key: str | None = None
    target_path: str | None = None


@dataclass(frozen=True)
class Layer2ConsumeResult:
    item_id: str
    run_key: str
    target_path: str
    recommended_arch_id: str
    recommended_macro_mode: str
    profile_count: int
    work_item_state: str


def _default_target_path(*, item_id: str) -> str:
    return f"control_plane/shadow_exports/l2_decisions/{item_id}.json"


def _resolve_path(*, repo_root: Path, path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return repo_root / path


def _resolve_run(session: Session, request: Layer2ConsumeRequest) -> tuple[WorkItem, Run]:
    if request.run_key:
        run = session.query(Run).filter(Run.run_key == request.run_key).one_or_none()
        if run is None:
            raise Layer2ResultConsumerError(f"run not found: {request.run_key}")
        return run.work_item, run
    if not request.item_id:
        raise Layer2ResultConsumerError("item_id or run_key is required")
    work_item = session.query(WorkItem).filter(WorkItem.item_id == request.item_id).one_or_none()
    if work_item is None:
        raise Layer2ResultConsumerError(f"work item not found: {request.item_id}")
    if not work_item.runs:
        raise Layer2ResultConsumerError(f"work item has no runs: {request.item_id}")
    run = sorted(work_item.runs, key=lambda row: (row.attempt, row.created_at or utcnow()))[-1]
    return work_item, run


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _find_output_path(work_item: WorkItem, suffix: str) -> str:
    for path in work_item.expected_outputs or []:
        if str(path).endswith(suffix):
            return str(path)
    raise Layer2ResultConsumerError(f"expected output not found for suffix {suffix}: {work_item.item_id}")


def _find_output_path_optional(work_item: WorkItem, suffix: str) -> str | None:
    for path in work_item.expected_outputs or []:
        if str(path).endswith(suffix):
            return str(path)
    return None


def _summary_best_row(rows: list[dict[str, str]]) -> dict[str, str]:
    aggregate_rows = [row for row in rows if str(row.get("scope", "")).strip() == "aggregate"]
    if not aggregate_rows:
        aggregate_rows = [row for row in rows if str(row.get("scope", "")).strip() == "model"]
    ranked = [row for row in aggregate_rows if str(row.get("objective_rank", "")).strip()]
    if ranked:
        ranked.sort(key=lambda row: int(str(row.get("objective_rank", "999999")).strip() or "999999"))
        return ranked[0]

    def as_float(value: str | None) -> float:
        try:
            return float(str(value).strip())
        except Exception:
            return float("inf")

    aggregate_rows.sort(
        key=lambda row: (
            as_float(row.get("latency_ms_mean")),
            as_float(row.get("energy_mj_mean")),
            as_float(row.get("critical_path_ns_mean")),
        )
    )
    if not aggregate_rows:
        raise Layer2ResultConsumerError("summary.csv has no aggregate/model rows")
    return aggregate_rows[0]


def _profile_recommendations(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for row in rows:
        result.append(
            {
                "profile": str(row.get("profile", "")).strip(),
                "best_arch_id": str(row.get("best_arch_id", "")).strip(),
                "best_macro_mode": str(row.get("best_macro_mode", "")).strip(),
                "objective_score": str(row.get("objective_score", "")).strip(),
                "latency_ms_mean": str(row.get("latency_ms_mean", "")).strip(),
                "energy_mj_mean": str(row.get("energy_mj_mean", "")).strip(),
                "flow_elapsed_s_mean": str(row.get("flow_elapsed_s_mean", "")).strip(),
                "best_json": str(row.get("best_json", "")).strip(),
                "report_md": str(row.get("report_md", "")).strip(),
                "pareto_csv": str(row.get("pareto_csv", "")).strip(),
            }
        )
    return result


def _build_payload(
    *,
    work_item: WorkItem,
    run: Run,
    best_point: dict[str, Any],
    summary_best: dict[str, str],
    objective_profiles: list[dict[str, Any]],
    source_refs: dict[str, str],
) -> dict[str, Any]:
    best = best_point.get("best") or {}
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
        "recommendation": {
            "arch_id": best.get("arch_id") or summary_best.get("arch_id"),
            "macro_mode": best.get("macro_mode") or summary_best.get("macro_mode"),
            "objective_rank": best.get("objective_rank") or summary_best.get("objective_rank"),
            "objective_score": best.get("objective_score") or summary_best.get("objective_score"),
            "latency_ms_mean": best.get("latency_ms_mean") or summary_best.get("latency_ms_mean"),
            "energy_mj_mean": best.get("energy_mj_mean") or summary_best.get("energy_mj_mean"),
            "critical_path_ns_mean": best.get("critical_path_ns_mean") or summary_best.get("critical_path_ns_mean"),
            "die_area_um2_mean": best.get("die_area_um2_mean") or summary_best.get("die_area_um2_mean"),
            "total_power_mw_mean": best.get("total_power_mw_mean") or summary_best.get("total_power_mw_mean"),
            "flow_elapsed_s_mean": best.get("flow_elapsed_s_mean") or summary_best.get("flow_elapsed_s_mean"),
        },
        "objective_profiles": objective_profiles,
        "source_refs": source_refs,
    }


def _upsert_artifact(session: Session, *, run: Run, target_path: str, payload: dict[str, Any]) -> None:
    artifact = (
        session.query(Artifact)
        .filter(Artifact.run_id == run.id, Artifact.kind == "decision_proposal")
        .one_or_none()
    )
    sha256 = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    if artifact is None:
        artifact = Artifact(
            run_id=run.id,
            kind="decision_proposal",
            storage_mode=ArtifactStorageMode.REPO,
            path=target_path,
            sha256=sha256,
            metadata_={"profile_count": len(payload.get("objective_profiles") or [])},
        )
        session.add(artifact)
    else:
        artifact.storage_mode = ArtifactStorageMode.REPO
        artifact.path = target_path
        artifact.sha256 = sha256
        artifact.metadata_ = {"profile_count": len(payload.get("objective_profiles") or [])}


def consume_l2_result(session: Session, request: Layer2ConsumeRequest) -> Layer2ConsumeResult:
    repo_root = Path(request.repo_root).resolve()
    work_item, run = _resolve_run(session, request)
    if work_item.task_type != "l2_campaign":
        raise Layer2ResultConsumerError(f"work item is not l2_campaign: {work_item.item_id}")
    if run.status != RunStatus.SUCCEEDED:
        raise Layer2ResultConsumerError(f"run is not succeeded: {run.run_key} status={run.status.value}")

    best_point_rel = _find_output_path(work_item, "/best_point.json")
    summary_rel = _find_output_path(work_item, "/summary.csv")
    results_rel = _find_output_path(work_item, "/results.csv")
    report_rel = _find_output_path(work_item, "/report.md")
    objective_sweep_rel = _find_output_path_optional(work_item, "/objective_sweep.csv")

    best_point = _load_json(_resolve_path(repo_root=repo_root, path_text=best_point_rel))
    summary_rows = _load_csv(_resolve_path(repo_root=repo_root, path_text=summary_rel))
    summary_best = _summary_best_row(summary_rows)
    objective_profiles: list[dict[str, Any]] = []
    if objective_sweep_rel:
        objective_sweep_path = _resolve_path(repo_root=repo_root, path_text=objective_sweep_rel)
        if objective_sweep_path.exists():
            objective_profiles = _profile_recommendations(_load_csv(objective_sweep_path))

    payload = _build_payload(
        work_item=work_item,
        run=run,
        best_point=best_point,
        summary_best=summary_best,
        objective_profiles=objective_profiles,
        source_refs={
            "best_point_json": best_point_rel,
            "summary_csv": summary_rel,
            "results_csv": results_rel,
            "report_md": report_rel,
            **({"objective_sweep_csv": objective_sweep_rel} if objective_sweep_rel else {}),
        },
    )

    recommended_arch_id = str(payload["recommendation"].get("arch_id", "")).strip()
    recommended_macro_mode = str(payload["recommendation"].get("macro_mode", "")).strip()
    if not recommended_arch_id or not recommended_macro_mode:
        raise Layer2ResultConsumerError(f"could not derive recommended point for work item: {work_item.item_id}")

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
            event_type="l2_decision_proposed",
            event_payload={
                "target_path": str(target_path.relative_to(repo_root)),
                "recommended_arch_id": recommended_arch_id,
                "recommended_macro_mode": recommended_macro_mode,
                "profile_count": len(objective_profiles),
            },
        )
    )
    session.commit()
    return Layer2ConsumeResult(
        item_id=work_item.item_id,
        run_key=run.run_key,
        target_path=str(target_path),
        recommended_arch_id=recommended_arch_id,
        recommended_macro_mode=recommended_macro_mode,
        profile_count=len(objective_profiles),
        work_item_state=work_item.state.value,
    )
