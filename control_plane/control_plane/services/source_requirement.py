"""Source revision requirements for queued evaluator work."""

from __future__ import annotations

from pathlib import Path


DEFAULT_REQUIRED_REF = "origin/master"
SOURCE_REQUIREMENT_VERSION = 1


def build_source_requirement(
    *,
    repo_root: str | Path,
    required_sha: str,
    required_ref: str = DEFAULT_REQUIRED_REF,
    requires_daemon_restart: bool = True,
    reason: str = "evaluator runtime must contain the queued job source commit",
) -> dict[str, object]:
    """Return the queue/DB contract block describing evaluator source needs."""

    Path(repo_root).resolve()
    return {
        "version": SOURCE_REQUIREMENT_VERSION,
        "repo": "",
        "required_ref": required_ref,
        "required_sha": required_sha,
        "requires_daemon_restart": requires_daemon_restart,
        "reason": reason,
    }
