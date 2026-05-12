"""Evaluator service-repo source reconciliation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import subprocess
import sys
from typing import NoReturn

from sqlalchemy.orm import Session

from control_plane.models.enums import FlowName, LeaseStatus, WorkItemState
from control_plane.models.worker_leases import WorkerLease
from control_plane.models.work_items import WorkItem
from control_plane.services.lease_service import upsert_worker_machine


class SourceReconciliationError(RuntimeError):
    pass


@dataclass(frozen=True)
class SourceReconciliationResult:
    status: str
    item_id: str | None = None
    required_sha: str | None = None
    current_sha: str | None = None
    source_commit_relation: str | None = None
    message: str | None = None
    restart_required: bool = False


def _run_git(repo_root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo_root), *args],
        check=check,
        capture_output=True,
        text=True,
    )


def _git_stdout(repo_root: Path, *args: str) -> str:
    return _run_git(repo_root, *args).stdout.strip()


def _git_success(repo_root: Path, *args: str) -> bool:
    return _run_git(repo_root, *args, check=False).returncode == 0


def _current_head(repo_root: Path) -> str | None:
    try:
        return _git_stdout(repo_root, "rev-parse", "HEAD")
    except (OSError, subprocess.CalledProcessError):
        return None


def _source_relation(repo_root: Path, required_sha: str, head_sha: str | None = None) -> str:
    if not required_sha:
        return "unspecified"
    if not _git_success(repo_root, "cat-file", "-e", f"{required_sha}^{{commit}}"):
        return "missing"
    head = head_sha or _current_head(repo_root)
    if head == required_sha:
        return "exact"
    if _git_success(repo_root, "merge-base", "--is-ancestor", required_sha, "HEAD"):
        return "descendant"
    return "mismatch"


def _machine_matches_item(*, capability_filter: dict[str, object] | None, work_item: WorkItem) -> bool:
    effective = dict(capability_filter or {})
    platform = str(effective.get("platform") or "").strip()
    flow = str(effective.get("flow") or "").strip()
    if platform and work_item.platform != platform:
        return False
    if flow and work_item.flow != FlowName(flow):
        return False
    return True


def next_source_required_item(
    session: Session,
    *,
    machine_key: str,
    hostname: str | None,
    executor_kind: str,
    machine_role: str,
    slot_capacity: int,
    capabilities: dict[str, object] | None,
    capability_filter: dict[str, object] | None,
) -> WorkItem | None:
    """Return the next READY item whose source requirement should gate dispatch."""

    machine = upsert_worker_machine(
        session,
        machine_key=machine_key,
        hostname=hostname,
        executor_kind=executor_kind,
        capabilities=capabilities,
        role=machine_role,
        slot_capacity=slot_capacity,
    )
    effective_filter = dict(machine.capabilities or {})
    effective_filter.update(capability_filter or {})
    query = (
        session.query(WorkItem)
        .filter(WorkItem.state == WorkItemState.READY)
        .filter(WorkItem.assigned_machine_key == machine.machine_key)
        .filter(~WorkItem.leases.any(WorkerLease.status == LeaseStatus.ACTIVE))
        .order_by(WorkItem.priority.desc(), WorkItem.created_at.asc(), WorkItem.item_id.asc())
    )
    for item in query.all():
        if str(item.source_commit or "").strip() and _machine_matches_item(
            capability_filter=effective_filter,
            work_item=item,
        ):
            session.commit()
            return item
    session.commit()
    return None


def reconcile_service_repo_source(
    *,
    repo_root: str,
    required_sha: str,
    update_ref: str = "origin/master",
    allow_update: bool = True,
) -> SourceReconciliationResult:
    """Ensure the service repo contains the queued source commit before execution."""

    repo_path = Path(repo_root).resolve()
    required = str(required_sha or "").strip()
    if not required:
        return SourceReconciliationResult(status="no_requirement")

    current = _current_head(repo_path)
    relation = _source_relation(repo_path, required, current)
    if relation in {"exact", "descendant"}:
        return SourceReconciliationResult(
            status="satisfied",
            required_sha=required,
            current_sha=current,
            source_commit_relation=relation,
        )

    if not allow_update:
        return SourceReconciliationResult(
            status="update_required",
            required_sha=required,
            current_sha=current,
            source_commit_relation=relation,
            restart_required=True,
            message="service repo does not contain required source commit",
        )

    try:
        _run_git(repo_path, "fetch", "--quiet", "origin")
    except (OSError, subprocess.CalledProcessError) as exc:
        raise SourceReconciliationError(f"failed to fetch origin for source reconciliation: {exc}") from exc

    if not _git_success(repo_path, "cat-file", "-e", f"{required}^{{commit}}"):
        return SourceReconciliationResult(
            status="blocked",
            required_sha=required,
            current_sha=current,
            source_commit_relation="missing",
            message=f"required source commit is not reachable after fetch: {required}",
        )

    target = required
    if update_ref and _git_success(repo_path, "merge-base", "--is-ancestor", required, update_ref):
        target = update_ref

    if _git_stdout(repo_path, "status", "--porcelain", "--untracked-files=no"):
        return SourceReconciliationResult(
            status="blocked",
            required_sha=required,
            current_sha=current,
            source_commit_relation=relation,
            message="service repo has tracked local modifications; refusing automatic checkout",
        )

    try:
        _run_git(repo_path, "checkout", "--detach", target)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise SourceReconciliationError(f"failed to checkout source target {target}: {exc}") from exc

    new_head = _current_head(repo_path)
    new_relation = _source_relation(repo_path, required, new_head)
    if new_relation not in {"exact", "descendant"}:
        return SourceReconciliationResult(
            status="blocked",
            required_sha=required,
            current_sha=new_head,
            source_commit_relation=new_relation,
            message=f"updated service repo does not satisfy required source commit: {required}",
        )

    return SourceReconciliationResult(
        status="updated",
        required_sha=required,
        current_sha=new_head,
        source_commit_relation=new_relation,
        restart_required=True,
        message=f"service repo updated to {target}",
    )


def reexec_current_process() -> NoReturn:
    os.execvpe(sys.executable, [sys.executable, *sys.argv], os.environ)
    raise AssertionError("unreachable")
