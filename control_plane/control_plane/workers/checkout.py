"""Repository checkout helpers for the internal worker loop."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess


class CheckoutError(RuntimeError):
    pass


@dataclass(frozen=True)
class CheckoutInfo:
    repo_root: str
    work_dir: str
    head_sha: str | None
    git_dirty: bool | None
    source_commit: str | None
    source_commit_matches: bool | None


def _run_git(repo_root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def prepare_checkout(
    *,
    repo_root: str,
    source_commit: str | None = None,
    enforce_source_commit: bool = False,
) -> CheckoutInfo:
    repo_path = Path(repo_root).resolve()
    if not repo_path.exists():
        raise CheckoutError(f"repo root does not exist: {repo_path}")
    if not repo_path.is_dir():
        raise CheckoutError(f"repo root is not a directory: {repo_path}")

    head_sha: str | None = None
    git_dirty: bool | None = None
    try:
        head_sha = _run_git(repo_path, "rev-parse", "HEAD")
        git_dirty = bool(_run_git(repo_path, "status", "--porcelain", "--untracked-files=no"))
    except (subprocess.CalledProcessError, FileNotFoundError):
        head_sha = None
        git_dirty = None

    source_commit_matches = None
    if source_commit:
        source_commit_matches = head_sha == source_commit
        if enforce_source_commit and not source_commit_matches:
            raise CheckoutError(
                f"source commit mismatch: expected {source_commit}, found {head_sha or 'unknown'}"
            )

    return CheckoutInfo(
        repo_root=str(repo_path),
        work_dir=str(repo_path),
        head_sha=head_sha,
        git_dirty=git_dirty,
        source_commit=source_commit,
        source_commit_matches=source_commit_matches,
    )
