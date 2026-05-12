"""Source reconciliation recovery coverage."""

from __future__ import annotations

from pathlib import Path
import subprocess

import pytest

from control_plane.services import source_reconciler
from control_plane.services.source_reconciler import (
    SourceReconciliationError,
    reconcile_service_repo_source,
)


def _run(*args: str) -> str:
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout.strip()


def _init_repo_with_stale_head(repo_root: Path) -> tuple[str, str]:
    origin_root = repo_root.parent / "origin.git"
    _run("git", "init", "--bare", str(origin_root))
    _run("git", "init", str(repo_root))
    _run("git", "-C", str(repo_root), "config", "user.email", "tester@example.com")
    _run("git", "-C", str(repo_root), "config", "user.name", "Tester")
    (repo_root / "README.md").write_text("initial\n", encoding="utf-8")
    _run("git", "-C", str(repo_root), "add", "README.md")
    _run("git", "-C", str(repo_root), "commit", "-m", "initial")
    _run("git", "-C", str(repo_root), "remote", "add", "origin", str(origin_root))
    _run("git", "-C", str(repo_root), "push", "-u", "origin", "HEAD:master")
    first = _run("git", "-C", str(repo_root), "rev-parse", "HEAD")

    (repo_root / "SOURCE.txt").write_text("source update\n", encoding="utf-8")
    _run("git", "-C", str(repo_root), "add", "SOURCE.txt")
    _run("git", "-C", str(repo_root), "commit", "-m", "source update")
    _run("git", "-C", str(repo_root), "push", "origin", "HEAD:master")
    second = _run("git", "-C", str(repo_root), "rev-parse", "HEAD")
    _run("git", "-C", str(repo_root), "checkout", "--detach", first)
    return first, second


def test_reconcile_service_repo_recovers_stale_git_index_lock(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    first, required = _init_repo_with_stale_head(repo_root)
    index_lock = repo_root / ".git" / "index.lock"
    index_lock.write_text("stale lock\n", encoding="utf-8")

    result = reconcile_service_repo_source(
        repo_root=str(repo_root),
        required_sha=required,
        update_ref="origin/master",
        allow_update=True,
    )

    assert result.status == "updated"
    assert result.required_sha == required
    assert result.source_commit_relation in {"exact", "descendant"}
    assert _run("git", "-C", str(repo_root), "rev-parse", "HEAD") == required
    assert first != required
    assert not index_lock.exists()


def test_reconcile_service_repo_keeps_index_lock_when_git_process_appears_active(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _, required = _init_repo_with_stale_head(repo_root)
    index_lock = repo_root / ".git" / "index.lock"
    index_lock.write_text("owned lock\n", encoding="utf-8")
    monkeypatch.setattr(source_reconciler, "_git_process_active_for_repo", lambda repo: True)

    with pytest.raises(SourceReconciliationError, match="git index lock is present"):
        reconcile_service_repo_source(
            repo_root=str(repo_root),
            required_sha=required,
            update_ref="origin/master",
            allow_update=True,
        )

    assert index_lock.exists()
