"""Dependency gating for staged developer-loop work items."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
from typing import Any

from sqlalchemy.orm import Session

from control_plane.models.artifacts import Artifact
from control_plane.models.enums import RunStatus, WorkItemState
from control_plane.models.runs import Run
from control_plane.models.work_items import WorkItem

_MATERIALIZED_ARTIFACT_KINDS = {"expected_output", "decision_proposal", "review_package", "queue_snapshot"}


@dataclass(frozen=True)
class DependencyGateConfig:
    item_ids: tuple[str, ...]
    requires_merged_inputs: bool
    requires_materialized_refs: bool


@dataclass(frozen=True)
class DependencyGateResult:
    satisfied: bool
    reason: str | None = None


def dependency_gate_config_from_payload(payload: dict[str, Any] | None) -> DependencyGateConfig:
    developer_loop = dict((payload or {}).get("developer_loop") or {})
    dependencies = dict(developer_loop.get("dependencies") or {})
    raw_item_ids = dependencies.get("item_ids") or []
    item_ids = tuple(str(item).strip() for item in raw_item_ids if str(item).strip())
    return DependencyGateConfig(
        item_ids=item_ids,
        requires_merged_inputs=bool(dependencies.get("requires_merged_inputs")),
        requires_materialized_refs=bool(dependencies.get("requires_materialized_refs")),
    )


def _latest_successful_run(work_item: WorkItem) -> Run | None:
    successful = [run for run in work_item.runs if run.status == RunStatus.SUCCEEDED]
    if not successful:
        return None
    return sorted(successful, key=lambda row: (row.attempt, row.created_at))[ -1]


def _path_exists(repo_root: Path, path_text: str) -> bool:
    path = Path(path_text)
    if not path.is_absolute():
        path = repo_root / path
    return path.exists()


def _repo_head(repo_root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:
        return None
    return result.stdout.strip() or None


def _refresh_released_source_requirement(work_item: WorkItem, *, repo_root: Path) -> None:
    head = _repo_head(repo_root)
    if not head:
        return
    work_item.source_commit = head
    if work_item.task_request is None:
        return
    payload = dict(work_item.task_request.request_payload or {})
    source_requirement = dict(payload.get("source_requirement") or {})
    if source_requirement:
        source_requirement["required_sha"] = head
        source_requirement.setdefault("required_ref", "origin/master")
        source_requirement.setdefault("requires_daemon_restart", True)
        payload["source_requirement"] = source_requirement
        work_item.task_request.request_payload = payload


def _materialized_artifacts_exist(session: Session, *, repo_root: Path, work_item: WorkItem) -> DependencyGateResult:
    run = _latest_successful_run(work_item)
    if run is None:
        return DependencyGateResult(False, f"dependency {work_item.item_id} has no successful run")

    artifacts = (
        session.query(Artifact)
        .filter(Artifact.run_id == run.id, Artifact.kind.in_(_MATERIALIZED_ARTIFACT_KINDS))
        .all()
    )
    if not artifacts:
        return DependencyGateResult(False, f"dependency {work_item.item_id} has no materialized review artifacts")

    for artifact in artifacts:
        if not _path_exists(repo_root, artifact.path):
            return DependencyGateResult(
                False,
                f"dependency {work_item.item_id} missing materialized artifact: {artifact.path}",
            )
    return DependencyGateResult(True)


def _repo_materialized_dependency_exists(*, repo_root: Path, item_id: str, requires_materialized_refs: bool) -> DependencyGateResult:
    decision_path = repo_root / "control_plane" / "shadow_exports" / "l2_decisions" / f"{item_id}.json"
    review_package = repo_root / "control_plane" / "shadow_exports" / "review" / item_id / "review_package.json"
    queue_snapshot = repo_root / "control_plane" / "shadow_exports" / "review" / item_id / "evaluated.json"
    if not decision_path.exists():
        return DependencyGateResult(False, f"dependency {item_id} not found")
    if not requires_materialized_refs:
        return DependencyGateResult(True)
    for path in (review_package, queue_snapshot):
        if not path.exists():
            return DependencyGateResult(False, f"dependency {item_id} missing materialized artifact: {path}")
    try:
        decision_payload = json.loads(decision_path.read_text(encoding="utf-8"))
    except Exception:
        return DependencyGateResult(False, f"dependency {item_id} decision artifact is unreadable")
    source_refs = decision_payload.get("source_refs")
    if isinstance(source_refs, dict):
        for rel_path in source_refs.values():
            if isinstance(rel_path, list):
                continue
            if not isinstance(rel_path, str) or not rel_path.strip():
                continue
            path = Path(rel_path)
            if path.is_absolute():
                candidate = path
            else:
                candidate = repo_root / path
            if not candidate.exists():
                return DependencyGateResult(
                    False,
                    f"dependency {item_id} missing materialized artifact: {rel_path}",
                )
    return DependencyGateResult(True)


def evaluate_work_item_dependencies(
    session: Session,
    *,
    repo_root: str | Path,
    work_item: WorkItem,
) -> DependencyGateResult:
    config = dependency_gate_config_from_payload(work_item.task_request.request_payload or {})
    if not config.item_ids:
        return DependencyGateResult(True)

    root = Path(repo_root).resolve()
    for item_id in config.item_ids:
        dependency = session.query(WorkItem).filter(WorkItem.item_id == item_id).one_or_none()
        if dependency is None:
            repo_dependency = _repo_materialized_dependency_exists(
                repo_root=root,
                item_id=item_id,
                requires_materialized_refs=config.requires_materialized_refs,
            )
            if not repo_dependency.satisfied:
                return repo_dependency
            continue
        if config.requires_merged_inputs:
            if dependency.state != WorkItemState.MERGED:
                return DependencyGateResult(False, f"dependency {item_id} is not merged")
        else:
            if _latest_successful_run(dependency) is None:
                return DependencyGateResult(False, f"dependency {item_id} has no successful run")
        if config.requires_materialized_refs:
            materialized = _materialized_artifacts_exist(session, repo_root=root, work_item=dependency)
            if not materialized.satisfied:
                return materialized
    return DependencyGateResult(True)


def refresh_blocked_dependents(session: Session, *, repo_root: str | Path, dependency_item_id: str) -> list[str]:
    root = Path(repo_root).resolve()
    released: list[str] = []
    blocked_items = session.query(WorkItem).filter(WorkItem.state == WorkItemState.BLOCKED).all()
    for work_item in blocked_items:
        config = dependency_gate_config_from_payload(work_item.task_request.request_payload or {})
        if dependency_item_id not in config.item_ids:
            continue
        gate = evaluate_work_item_dependencies(session, repo_root=root, work_item=work_item)
        if gate.satisfied:
            work_item.state = WorkItemState.DISPATCH_PENDING
            work_item.queue_snapshot_path = None
            _refresh_released_source_requirement(work_item, repo_root=root)
            released.append(work_item.item_id)
    return released


def refresh_all_blocked_items(session: Session, *, repo_root: str | Path) -> list[str]:
    root = Path(repo_root).resolve()
    released: list[str] = []
    blocked_items = session.query(WorkItem).filter(WorkItem.state == WorkItemState.BLOCKED).all()
    for work_item in blocked_items:
        gate = evaluate_work_item_dependencies(session, repo_root=root, work_item=work_item)
        if gate.satisfied:
            work_item.state = WorkItemState.DISPATCH_PENDING
            work_item.queue_snapshot_path = None
            _refresh_released_source_requirement(work_item, repo_root=root)
            released.append(work_item.item_id)
    return released
