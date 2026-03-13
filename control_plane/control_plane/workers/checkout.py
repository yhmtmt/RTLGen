"""Repository checkout helpers for the internal worker loop."""

from __future__ import annotations

from dataclasses import dataclass
import configparser
from pathlib import Path
import subprocess
import tempfile
import shutil


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
    source_commit_relation: str | None
    materialized_submodules: tuple[str, ...]
    checkout_mode: str
    cleanup_path: str | None


def _run_git(repo_root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _git_success(repo_root: Path, *args: str) -> bool:
    result = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def _read_submodule_paths(repo_root: Path) -> list[str]:
    gitmodules = repo_root / ".gitmodules"
    if not gitmodules.exists():
        return []
    parser = configparser.ConfigParser()
    parser.read(gitmodules, encoding="utf-8")
    paths: list[str] = []
    for section in parser.sections():
        if parser.has_option(section, "path"):
            rel = parser.get(section, "path").strip()
            if rel:
                paths.append(rel)
    return paths


def _materialize_missing_submodules(
    checkout_root: Path,
    *,
    required_submodules: list[str] | tuple[str, ...] | None = None,
) -> tuple[str, ...]:
    allowed = set(required_submodules or [])
    missing: list[str] = []
    for rel in _read_submodule_paths(checkout_root):
        if allowed and rel not in allowed:
            continue
        path = checkout_root / rel
        if (not path.exists()) or (path.is_dir() and not any(path.iterdir())):
            missing.append(rel)
    if not missing:
        return ()
    subprocess.run(
        ["git", "-C", str(checkout_root), "submodule", "update", "--init", *missing],
        check=True,
        capture_output=True,
        text=True,
    )
    return tuple(missing)


def _ensure_source_commit(anchor_repo: Path, source_commit: str) -> None:
    if _git_success(anchor_repo, "cat-file", "-e", f"{source_commit}^{{commit}}"):
        return
    subprocess.run(
        ["git", "-C", str(anchor_repo), "fetch", "--quiet", "origin", source_commit],
        check=True,
        capture_output=True,
        text=True,
    )
    if not _git_success(anchor_repo, "cat-file", "-e", f"{source_commit}^{{commit}}"):
        raise CheckoutError(f"source commit not available after fetch: {source_commit}")


def _create_worktree(anchor_repo: Path, target_commit: str | None) -> tuple[Path, str]:
    temp_root = Path(tempfile.mkdtemp(prefix="rtlcp-worktree-"))
    checkout_root = temp_root / "repo"
    commitish = target_commit or "HEAD"
    subprocess.run(
        ["git", "-C", str(anchor_repo), "worktree", "add", "--detach", str(checkout_root), commitish],
        check=True,
        capture_output=True,
        text=True,
    )
    return checkout_root, str(temp_root)


def cleanup_checkout(info: CheckoutInfo) -> None:
    if info.checkout_mode != "worktree":
        return
    if info.cleanup_path is None:
        return
    cleanup_root = Path(info.cleanup_path)
    checkout_root = Path(info.work_dir)
    anchor_repo = Path(info.repo_root)
    try:
        subprocess.run(
            ["git", "-C", str(anchor_repo), "worktree", "remove", "--force", str(checkout_root)],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError:
        pass
    shutil.rmtree(cleanup_root, ignore_errors=True)


def prepare_checkout(
    *,
    repo_root: str,
    source_commit: str | None = None,
    enforce_source_commit: bool = False,
    required_submodules: list[str] | tuple[str, ...] | None = None,
) -> CheckoutInfo:
    repo_path = Path(repo_root).resolve()
    if not repo_path.exists():
        raise CheckoutError(f"repo root does not exist: {repo_path}")
    if not repo_path.is_dir():
        raise CheckoutError(f"repo root is not a directory: {repo_path}")

    try:
        if source_commit:
            _ensure_source_commit(repo_path, source_commit)
        checkout_path, cleanup_path = _create_worktree(repo_path, source_commit)
    except (subprocess.CalledProcessError, FileNotFoundError, CheckoutError) as exc:
        raise CheckoutError(f"failed to prepare worktree: {exc}") from exc

    try:
        materialized_submodules = _materialize_missing_submodules(
            checkout_path,
            required_submodules=required_submodules,
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        cleanup_checkout(
            CheckoutInfo(
                repo_root=str(repo_path),
                work_dir=str(checkout_path),
                head_sha=None,
                git_dirty=None,
                source_commit=source_commit,
                source_commit_matches=None,
                source_commit_relation=None,
                materialized_submodules=(),
                checkout_mode="worktree",
                cleanup_path=cleanup_path,
            )
        )
        raise CheckoutError(f"failed to materialize submodules: {exc}") from exc

    head_sha: str | None = None
    git_dirty: bool | None = None
    try:
        head_sha = _run_git(checkout_path, "rev-parse", "HEAD")
        git_dirty = bool(_run_git(checkout_path, "status", "--porcelain", "--untracked-files=no"))
    except (subprocess.CalledProcessError, FileNotFoundError):
        head_sha = None
        git_dirty = None

    source_commit_matches = None
    source_commit_relation: str | None = None
    if source_commit:
        source_commit_matches = head_sha == source_commit
        source_commit_relation = "mismatch"
        if source_commit_matches:
            source_commit_relation = "exact"
        elif head_sha is not None:
            try:
                subprocess.run(
                    ["git", "-C", str(repo_path), "merge-base", "--is-ancestor", source_commit, "HEAD"],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                source_commit_relation = "descendant"
            except subprocess.CalledProcessError:
                source_commit_relation = "mismatch"
            except FileNotFoundError:
                source_commit_relation = "unknown"
        if enforce_source_commit and source_commit_relation not in {"exact", "descendant"}:
            raise CheckoutError(
                "source commit not satisfied: "
                f"expected at-or-ahead-of {source_commit}, found {head_sha or 'unknown'}"
            )

    return CheckoutInfo(
        repo_root=str(repo_path),
        work_dir=str(checkout_path),
        head_sha=head_sha,
        git_dirty=git_dirty,
        source_commit=source_commit,
        source_commit_matches=source_commit_matches,
        source_commit_relation=source_commit_relation,
        materialized_submodules=materialized_submodules,
        checkout_mode="worktree",
        cleanup_path=cleanup_path,
    )
