"""Poll GitHub PR state and reconcile merged review PRs into the control plane."""

from __future__ import annotations

from dataclasses import dataclass
import json
import subprocess
from typing import Any

from sqlalchemy.orm import Session

from control_plane.models.enums import GitHubLinkState
from control_plane.models.github_links import GitHubLink
from control_plane.services.github_bridge import GitHubReconcileRequest, reconcile_github_link


class GitHubPollError(RuntimeError):
    pass


@dataclass(frozen=True)
class GitHubPollRequest:
    repo_root: str
    repo: str | None = None


@dataclass(frozen=True)
class GitHubPollResult:
    checked_count: int
    merged_count: int
    skipped_count: int
    errors: list[str]


def _gh_api_pull(repo: str, pr_number: int) -> dict[str, Any]:
    result = subprocess.run(
        ["gh", "api", f"repos/{repo}/pulls/{pr_number}"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    if not isinstance(payload, dict):
        raise GitHubPollError(f"unexpected gh api payload for {repo}#{pr_number}")
    return payload


def _finalization_terminal(link: GitHubLink) -> bool:
    metadata = dict(link.metadata_ or {})
    if str(metadata.get("finalization_commit") or "").strip():
        return True
    if bool(metadata.get("finalization_skipped")):
        return True
    return False


def poll_github_links(session: Session, request: GitHubPollRequest) -> GitHubPollResult:
    query = session.query(GitHubLink).filter(
        GitHubLink.pr_number.isnot(None),
        GitHubLink.state.in_((GitHubLinkState.PR_OPEN, GitHubLinkState.PR_MERGED)),
    )
    if request.repo:
        query = query.filter(GitHubLink.repo == request.repo)
    links = query.order_by(GitHubLink.updated_at.asc(), GitHubLink.created_at.asc()).all()

    checked_count = 0
    merged_count = 0
    skipped_count = 0
    errors: list[str] = []

    for link in links:
        if link.state == GitHubLinkState.PR_MERGED and _finalization_terminal(link):
            skipped_count += 1
            continue

        checked_count += 1
        pr_number = int(link.pr_number)
        try:
            payload = _gh_api_pull(link.repo, pr_number)
        except Exception as exc:
            errors.append(f"{link.repo}#{pr_number}: {exc}")
            continue

        merged_at = str(payload.get("merged_at") or "").strip()
        pr_state = str(payload.get("state") or "").strip().lower()
        merge_commit_sha = str(payload.get("merge_commit_sha") or "").strip()
        pr_url = str(payload.get("html_url") or link.pr_url or "").strip() or None
        head_ref = payload.get("head") or {}
        base_ref = payload.get("base") or {}
        branch_name = str(head_ref.get("ref") or link.branch_name or "").strip() or None
        base_branch = str(base_ref.get("ref") or link.base_branch or "").strip() or None

        if merged_at:
            reconcile_github_link(
                session,
                GitHubReconcileRequest(
                    repo=link.repo,
                    item_id=link.work_item.item_id if link.work_item is not None else None,
                    branch_name=branch_name,
                    pr_number=pr_number,
                    pr_url=pr_url,
                    head_sha=merge_commit_sha or None,
                    base_branch=base_branch,
                    state=GitHubLinkState.PR_MERGED.value,
                    run_key=link.run.run_key if link.run is not None else None,
                    metadata={"source": "github_poller", "merged_at": merged_at},
                    repo_root=request.repo_root,
                ),
            )
            merged_count += 1
            continue

        if pr_state == "closed":
            reconcile_github_link(
                session,
                GitHubReconcileRequest(
                    repo=link.repo,
                    item_id=link.work_item.item_id if link.work_item is not None else None,
                    branch_name=branch_name,
                    pr_number=pr_number,
                    pr_url=pr_url,
                    head_sha=merge_commit_sha or None,
                    base_branch=base_branch,
                    state=GitHubLinkState.PR_CLOSED.value,
                    run_key=link.run.run_key if link.run is not None else None,
                    metadata={"source": "github_poller", "closed_at_poll_utc": __import__("datetime").datetime.utcnow().isoformat() + "Z"},
                    repo_root=request.repo_root,
                ),
            )
            continue

        skipped_count += 1

    return GitHubPollResult(
        checked_count=checked_count,
        merged_count=merged_count,
        skipped_count=skipped_count,
        errors=errors,
    )
