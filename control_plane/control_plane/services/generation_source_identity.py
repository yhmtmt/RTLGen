"""Helpers for proving manifest generation came from the declared source tree."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Callable


GENERATION_SOURCE_IDENTITY_VERSION = 1


def _raise(error_factory: Callable[[str], Exception], message: str) -> None:
    raise error_factory(message)


def _git_stdout(
    repo_root: Path,
    args: list[str],
    *,
    error_factory: Callable[[str], Exception],
    failure_message: str,
) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), *args],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        detail = f": {stderr}" if stderr else ""
        _raise(error_factory, f"{failure_message}{detail}")
    stdout = result.stdout.strip()
    if not stdout:
        _raise(error_factory, f"{failure_message}: empty git output")
    return stdout


def _git_status_porcelain(
    repo_root: Path,
    *,
    error_factory: Callable[[str], Exception],
    failure_message: str,
) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "status", "--porcelain"],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        detail = f": {stderr}" if stderr else ""
        _raise(error_factory, f"{failure_message}{detail}")
    return result.stdout


def resolve_source_commit(
    repo_root: Path,
    source_commit: str | None,
    *,
    error_factory: Callable[[str], Exception],
) -> str:
    resolved = str(source_commit or "").strip()
    if resolved:
        try:
            subprocess.run(
                ["git", "-C", str(repo_root), "cat-file", "-e", f"{resolved}^{{commit}}"],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as exc:
            stderr = (exc.stderr or "").strip()
            detail = f": {stderr}" if stderr else ""
            _raise(
                error_factory,
                f"provided source_commit does not resolve to a commit in repo_root {repo_root}: {resolved}{detail}",
            )
        normalized = _git_stdout(
            repo_root,
            ["rev-parse", f"{resolved}^{{commit}}"],
            error_factory=error_factory,
            failure_message=(
                f"provided source_commit resolved to empty git rev-parse output in repo_root {repo_root}: {resolved}"
            ),
        )
        try:
            subprocess.run(
                ["git", "-C", str(repo_root), "fetch", "--quiet", "origin"],
                check=True,
                capture_output=True,
                text=True,
            )
            refs = subprocess.run(
                [
                    "git",
                    "-C",
                    str(repo_root),
                    "for-each-ref",
                    "refs/remotes/origin",
                    "--contains",
                    normalized,
                    "--format=%(refname)",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as exc:
            stderr = (exc.stderr or "").strip()
            detail = f": {stderr}" if stderr else ""
            _raise(
                error_factory,
                f"failed to verify source_commit against origin for repo_root {repo_root}: {normalized}{detail}",
            )
        if not refs.stdout.strip():
            _raise(
                error_factory,
                f"provided source_commit is not reachable from origin in repo_root {repo_root}: {normalized}",
            )
        return normalized
    return _git_stdout(
        repo_root,
        ["rev-parse", "HEAD"],
        error_factory=error_factory,
        failure_message=f"failed to resolve source commit from repo_root {repo_root}",
    )


def build_generation_source_identity(
    repo_root: Path,
    *,
    declared_source_commit: str,
    error_factory: Callable[[str], Exception],
    context: str,
) -> dict[str, object]:
    repo_head = _git_stdout(
        repo_root,
        ["rev-parse", "HEAD"],
        error_factory=error_factory,
        failure_message=f"failed to resolve repo HEAD for {context} in repo_root {repo_root}",
    )
    if repo_head != declared_source_commit:
        _raise(
            error_factory,
            (
                f"{context} requires an exact-generation worktree: declared source_commit={declared_source_commit}, "
                f"repo HEAD={repo_head}. Regenerate the item from a checkout whose HEAD exactly matches the declared "
                "source commit."
            ),
        )
    porcelain = _git_status_porcelain(
        repo_root,
        error_factory=error_factory,
        failure_message=f"failed to resolve git status for {context} in repo_root {repo_root}",
    )
    if porcelain:
        status_lines = [line.rstrip() for line in porcelain.splitlines() if line.strip()]
        preview = "; ".join(status_lines[:5])
        if len(status_lines) > 5:
            preview += "; ..."
        _raise(
            error_factory,
            (
                f"{context} requires a clean exact-generation worktree: declared source_commit={declared_source_commit}, "
                f"repo HEAD={repo_head}, git status --porcelain is not empty ({preview}). "
                "Commit, stash, or remove tracked and untracked changes, then regenerate the item from the declared source commit."
            ),
        )
    return {
        "version": GENERATION_SOURCE_IDENTITY_VERSION,
        "declared_source_commit": declared_source_commit,
        "repo_head_sha": repo_head,
        "relation": "exact",
        "proof": "generator_worktree_head_exact",
        "clean": True,
    }


def validate_generation_source_identity(
    payload: dict[str, object],
    *,
    declared_source_commit: str | None,
    error_factory: Callable[[str], Exception],
    context: str,
) -> None:
    required_sha = str(declared_source_commit or "").strip()
    if not required_sha:
        return
    raw_identity = payload.get("generation_source_identity")
    if not isinstance(raw_identity, dict):
        _raise(
            error_factory,
            (
                f"{context} declares source_commit={required_sha} but is missing generation_source_identity. "
                "Regenerate the queue item from a worktree whose HEAD exactly matches the declared source commit."
            ),
        )
    identity = raw_identity
    version = identity.get("version")
    identity_source = str(identity.get("declared_source_commit") or "").strip()
    repo_head = str(identity.get("repo_head_sha") or "").strip()
    relation = str(identity.get("relation") or "").strip()
    proof = str(identity.get("proof") or "").strip()
    clean = identity.get("clean")
    if version != GENERATION_SOURCE_IDENTITY_VERSION:
        _raise(
            error_factory,
            (
                f"{context} has generation_source_identity with unsupported version={version!r}; "
                f"expected version={GENERATION_SOURCE_IDENTITY_VERSION}. "
                "Regenerate the queue item with the exact-generation worktree contract."
            ),
        )
    if identity_source != required_sha or repo_head != required_sha or relation != "exact":
        _raise(
            error_factory,
            (
                f"{context} has generation_source_identity that does not prove exact generation from declared "
                f"source_commit={required_sha}: declared_source_commit={identity_source or '<missing>'}, "
                f"repo_head_sha={repo_head or '<missing>'}, relation={relation or '<missing>'}. "
                "Regenerate the queue item from the declared source commit."
            ),
        )
    if clean is not True:
        _raise(
            error_factory,
            (
                f"{context} has generation_source_identity that does not prove a clean generation worktree for "
                f"declared source_commit={required_sha}: clean={clean!r}. "
                "Regenerate the queue item from a clean checkout whose HEAD exactly matches the declared source commit."
            ),
        )
    if proof != "generator_worktree_head_exact":
        _raise(
            error_factory,
            (
                f"{context} has unsupported generation_source_identity proof={proof or '<missing>'}. "
                "Regenerate the queue item with the exact-generation worktree contract."
            ),
        )
