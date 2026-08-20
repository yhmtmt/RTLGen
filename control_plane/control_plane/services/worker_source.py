"""Worker-process source identity helpers."""

from __future__ import annotations

from pathlib import Path
import subprocess
from typing import Any


def service_repo_head(repo_root: str) -> str | None:
    repo = Path(repo_root).resolve()
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    head = result.stdout.strip()
    return head or None


def capabilities_with_worker_source(
    *,
    repo_root: str,
    capabilities: dict[str, Any] | None,
    capability_filter: dict[str, Any] | None,
) -> dict[str, Any]:
    merged = dict(capabilities or {})
    for key, value in dict(capability_filter or {}).items():
        merged.setdefault(key, value)
    worker_source = dict(merged.get("worker_source") or {})
    worker_source["repo_root"] = str(Path(repo_root).resolve())
    head = service_repo_head(repo_root)
    if head:
        worker_source["head"] = head
    merged["worker_source"] = worker_source
    return merged


def source_head_satisfies_requirement(
    *, repo_root: str, worker_head: str, required_sha: str
) -> bool:
    """Check the code loaded by a worker, not the mutable checkout's current HEAD."""

    worker = str(worker_head or "").strip()
    required = str(required_sha or "").strip()
    if not required:
        return True
    if not worker:
        return False
    if worker == required:
        return True
    try:
        result = subprocess.run(
            [
                "git",
                "-C",
                str(Path(repo_root).resolve()),
                "merge-base",
                "--is-ancestor",
                required,
                worker,
            ],
            check=False,
            capture_output=True,
            text=True,
        )
    except (OSError, RuntimeError):
        return False
    return result.returncode == 0
