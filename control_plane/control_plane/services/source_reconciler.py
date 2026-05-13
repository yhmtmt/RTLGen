"""Evaluator service-repo source reconciliation."""

from __future__ import annotations

from dataclasses import dataclass
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys
import time
from typing import NoReturn

from sqlalchemy.orm import Session

from control_plane.models.enums import FlowName, LeaseStatus, WorkItemState
from control_plane.models.worker_leases import WorkerLease
from control_plane.models.work_items import WorkItem
from control_plane.services.lease_service import upsert_worker_machine


class SourceReconciliationError(RuntimeError):
    pass


_SOURCE_RECONCILE_LOCK_NAME = "rtlcp-source-reconcile.lock"
_SOURCE_RECONCILE_LOCK_TIMEOUT_SECONDS = 30.0
_SOURCE_RECONCILE_LOCK_POLL_SECONDS = 0.2


@dataclass(frozen=True)
class SourceReconciliationResult:
    status: str
    item_id: str | None = None
    required_sha: str | None = None
    current_sha: str | None = None
    source_commit_relation: str | None = None
    message: str | None = None
    restart_required: bool = False
    quarantine_paths: tuple[str, ...] = ()


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


def _git_common_dir(repo_root: Path) -> Path:
    raw = _git_stdout(repo_root, "rev-parse", "--git-common-dir")
    path = Path(raw)
    if path.is_absolute():
        return path
    return (repo_root / path).resolve()


def _git_path(repo_root: Path, name: str) -> Path:
    raw = _git_stdout(repo_root, "rev-parse", "--git-path", name)
    path = Path(raw)
    if path.is_absolute():
        return path
    return (repo_root / path).resolve()


def _pid_is_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _read_lock_pid(lock_path: Path) -> int | None:
    try:
        for line in lock_path.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("pid="):
                return int(line.split("=", 1)[1].strip())
    except (OSError, ValueError):
        return None
    return None


def _remove_stale_control_lock(lock_path: Path) -> bool:
    pid = _read_lock_pid(lock_path)
    if pid is not None and _pid_is_alive(pid):
        return False
    try:
        lock_path.unlink()
        return True
    except FileNotFoundError:
        return True
    except OSError:
        return False


@contextmanager
def _source_reconcile_lock(repo_root: Path):
    """Serialize evaluator service-checkout mutation across control-plane daemons."""

    try:
        lock_dir = _git_common_dir(repo_root)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise SourceReconciliationError(f"failed to resolve git common dir for source reconciliation: {exc}") from exc
    lock_path = lock_dir / _SOURCE_RECONCILE_LOCK_NAME
    deadline = time.monotonic() + _SOURCE_RECONCILE_LOCK_TIMEOUT_SECONDS
    fd: int | None = None
    while True:
        try:
            fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
            payload = f"pid={os.getpid()}\ncreated_at={time.time()}\nrepo_root={repo_root}\n"
            os.write(fd, payload.encode("utf-8"))
            break
        except FileExistsError:
            if not _remove_stale_control_lock(lock_path):
                if time.monotonic() >= deadline:
                    raise SourceReconciliationError(
                        f"source reconciliation lock is busy: {lock_path}"
                    )
                time.sleep(_SOURCE_RECONCILE_LOCK_POLL_SECONDS)
                continue
        except OSError as exc:
            raise SourceReconciliationError(f"failed to acquire source reconciliation lock {lock_path}: {exc}") from exc

    try:
        yield
    finally:
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass
        try:
            lock_path.unlink()
        except FileNotFoundError:
            pass
        except OSError:
            pass


def _git_process_active_for_repo(repo_root: Path) -> bool:
    """Best-effort guard before removing a stale Git index lock."""

    try:
        common_dir = _git_common_dir(repo_root)
    except (OSError, subprocess.CalledProcessError):
        common_dir = repo_root / ".git"
    needles = {str(repo_root), str(common_dir)}
    try:
        result = subprocess.run(
            ["ps", "-eo", "pid=,comm=,args="],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return True
    current_pid = os.getpid()
    for line in result.stdout.splitlines():
        text = line.strip()
        if not text:
            continue
        parts = text.split(maxsplit=2)
        try:
            pid = int(parts[0])
        except (ValueError, IndexError):
            continue
        if pid == current_pid:
            continue
        if "git" not in text:
            continue
        if any(needle in text for needle in needles):
            return True
    return False


def _recover_stale_git_index_lock(repo_root: Path) -> bool:
    """Remove Git's index.lock only when no live Git process appears to own it."""

    try:
        index_lock = _git_path(repo_root, "index.lock")
    except (OSError, subprocess.CalledProcessError):
        return False
    if not index_lock.exists():
        return False
    if _git_process_active_for_repo(repo_root):
        raise SourceReconciliationError(
            f"git index lock is present and a git process still appears active: {index_lock}"
        )
    try:
        index_lock.unlink()
        return True
    except FileNotFoundError:
        return False
    except OSError as exc:
        raise SourceReconciliationError(f"failed to remove stale git index lock {index_lock}: {exc}") from exc


def _checkout_blocking_untracked_paths(stderr: str) -> list[str]:
    marker = "The following untracked working tree files would be overwritten by checkout:"
    paths: list[str] = []
    collecting = False
    for line in stderr.splitlines():
        text = line.strip()
        if marker in text:
            collecting = True
            continue
        if not collecting:
            continue
        if not text:
            continue
        if text.startswith("Please ") or text == "Aborting":
            break
        if text.startswith("error:"):
            continue
        paths.append(text)
    return paths


def _safe_repo_relative_path(raw_path: str) -> Path:
    path = Path(raw_path)
    if path.is_absolute() or not path.parts or any(part in {"", ".", ".."} for part in path.parts):
        raise SourceReconciliationError(f"unsafe checkout blocker path reported by git: {raw_path}")
    return path


def _source_quarantine_root() -> Path:
    root = os.environ.get("RTLCP_SOURCE_QUARANTINE_ROOT", "/tmp")
    return Path(root).resolve()


def _quarantine_untracked_checkout_blockers(repo_root: Path, paths: list[str], target: str) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    quarantine_dir = _source_quarantine_root() / f"{repo_root.name}-checkout-blockers-{stamp}-{os.getpid()}"
    moved: list[dict[str, str]] = []
    for raw_path in paths:
        rel_path = _safe_repo_relative_path(raw_path)
        if _git_success(repo_root, "ls-files", "--error-unmatch", "--", str(rel_path)):
            raise SourceReconciliationError(f"checkout blocker is tracked in current service repo: {rel_path}")
        source = (repo_root / rel_path).resolve()
        try:
            source.relative_to(repo_root)
        except ValueError as exc:
            raise SourceReconciliationError(f"checkout blocker escapes service repo: {rel_path}") from exc
        if not source.exists():
            continue
        destination = quarantine_dir / rel_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(destination))
        moved.append({"source": str(rel_path), "quarantined_to": str(destination)})

    if not moved:
        raise SourceReconciliationError(
            "git reported untracked checkout blockers, but none could be found to quarantine"
        )
    manifest = {
        "repo_root": str(repo_root),
        "target": target,
        "moved": moved,
        "created_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    quarantine_dir.mkdir(parents=True, exist_ok=True)
    (quarantine_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return quarantine_dir


def _checkout_error_message(target: str, exc: Exception, context: str | None = None) -> str:
    stderr = str(getattr(exc, "stderr", "") or "").strip()
    prefix = f"failed to checkout source target {target}"
    if context:
        prefix = f"{prefix} {context}"
    if stderr:
        return f"{prefix}: {stderr}"
    return f"{prefix}: {exc}"


def _checkout_source_target(repo_root: Path, target: str) -> tuple[Path, ...]:
    quarantine_dirs: list[Path] = []
    recovered_index_lock = False
    quarantine_attempts = 0

    while True:
        try:
            _run_git(repo_root, "checkout", "--detach", target)
            return tuple(quarantine_dirs)
        except (OSError, subprocess.CalledProcessError) as exc:
            stderr = getattr(exc, "stderr", "") or ""
            if "index.lock" in stderr and not recovered_index_lock:
                recovered_index_lock = True
                if not _recover_stale_git_index_lock(repo_root):
                    raise SourceReconciliationError(_checkout_error_message(target, exc)) from exc
                continue

            blocker_paths = _checkout_blocking_untracked_paths(stderr)
            if blocker_paths and quarantine_attempts < 3:
                quarantine_attempts += 1
                quarantine_dirs.append(_quarantine_untracked_checkout_blockers(repo_root, blocker_paths, target))
                continue

            context = None
            if recovered_index_lock:
                context = "after stale index lock recovery"
            if quarantine_dirs:
                paths = ", ".join(str(path) for path in quarantine_dirs)
                context = f"after quarantining untracked blockers at {paths}"
            raise SourceReconciliationError(_checkout_error_message(target, exc, context)) from exc


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

    with _source_reconcile_lock(repo_path):
        return _reconcile_service_repo_source_locked(
            repo_path=repo_path,
            required=required,
            update_ref=update_ref,
            allow_update=allow_update,
        )


def _reconcile_service_repo_source_locked(
    *,
    repo_path: Path,
    required: str,
    update_ref: str,
    allow_update: bool,
) -> SourceReconciliationResult:
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

    _recover_stale_git_index_lock(repo_path)
    if _git_stdout(repo_path, "status", "--porcelain", "--untracked-files=no"):
        return SourceReconciliationResult(
            status="blocked",
            required_sha=required,
            current_sha=current,
            source_commit_relation=relation,
            message="service repo has tracked local modifications; refusing automatic checkout",
        )

    quarantine_paths = _checkout_source_target(repo_path, target)

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

    message = f"service repo updated to {target}"
    if quarantine_paths:
        message = f"{message}; quarantined untracked checkout blockers at {', '.join(str(path) for path in quarantine_paths)}"

    return SourceReconciliationResult(
        status="updated",
        required_sha=required,
        current_sha=new_head,
        source_commit_relation=new_relation,
        restart_required=True,
        message=message,
        quarantine_paths=tuple(str(path) for path in quarantine_paths),
    )


def reexec_current_process() -> NoReturn:
    os.execvpe(sys.executable, [sys.executable, *sys.argv], os.environ)
    raise AssertionError("unreachable")
