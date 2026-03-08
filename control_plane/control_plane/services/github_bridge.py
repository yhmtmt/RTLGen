"""GitHub branch and PR reconciliation for cp-007."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

from sqlalchemy.orm import Session

from control_plane.clock import utcnow
from control_plane.models.enums import GitHubLinkState, WorkItemState
from control_plane.models.github_links import GitHubLink
from control_plane.models.run_events import RunEvent
from control_plane.models.runs import Run
from control_plane.models.work_items import WorkItem

_EVAL_BRANCH_RE = re.compile(r"^eval/(?P<item_id>[^/]+)/(?P<session_id>[^/]+)$")


class GitHubReconcileError(RuntimeError):
    pass


class GitHubReconcileNotFound(GitHubReconcileError):
    pass


@dataclass(frozen=True)
class GitHubReconcileResult:
    item_id: str
    github_link_id: str
    state: str
    branch_name: str | None
    pr_number: int | None
    work_item_state: str
    run_id: str | None


@dataclass(frozen=True)
class GitHubReconcileRequest:
    repo: str
    item_id: str | None = None
    branch_name: str | None = None
    pr_number: int | None = None
    pr_url: str | None = None
    head_sha: str | None = None
    base_branch: str | None = None
    state: str = "none"
    run_key: str | None = None
    metadata: dict[str, Any] | None = None


def _infer_item_id(branch_name: str | None) -> str | None:
    if not branch_name:
        return None
    match = _EVAL_BRANCH_RE.match(branch_name)
    if match is None:
        return None
    return match.group("item_id")


def _resolve_work_item(session: Session, request: GitHubReconcileRequest) -> WorkItem:
    item_id = request.item_id or _infer_item_id(request.branch_name)
    if not item_id:
        raise GitHubReconcileError("item_id is required unless branch_name matches eval/<item_id>/<session_id>")
    work_item = session.query(WorkItem).filter(WorkItem.item_id == item_id).one_or_none()
    if work_item is None:
        raise GitHubReconcileNotFound(f"work item not found: {item_id}")
    return work_item


def _resolve_run(session: Session, run_key: str | None) -> Run | None:
    if not run_key:
        return None
    run = session.query(Run).filter(Run.run_key == run_key).one_or_none()
    if run is None:
        raise GitHubReconcileNotFound(f"run not found: {run_key}")
    return run


def _select_existing_link(session: Session, work_item_id: str, request: GitHubReconcileRequest) -> GitHubLink | None:
    query = session.query(GitHubLink).filter(GitHubLink.work_item_id == work_item_id, GitHubLink.repo == request.repo)
    if request.pr_number is not None:
        link = query.filter(GitHubLink.pr_number == request.pr_number).one_or_none()
        if link is not None:
            return link
    if request.branch_name:
        link = query.filter(GitHubLink.branch_name == request.branch_name).one_or_none()
        if link is not None:
            return link
    return None


def _advance_work_item_state(work_item: WorkItem, state: GitHubLinkState) -> None:
    if state == GitHubLinkState.PR_OPEN and work_item.state not in {WorkItemState.MERGED, WorkItemState.SUPERSEDED}:
        if work_item.state not in {WorkItemState.AWAITING_REVIEW, WorkItemState.MERGED}:
            work_item.state = WorkItemState.AWAITING_REVIEW
    elif state == GitHubLinkState.PR_MERGED:
        work_item.state = WorkItemState.MERGED


def _emit_run_event(session: Session, run: Run | None, event_type: str, payload: dict[str, Any]) -> None:
    if run is None:
        return
    session.add(
        RunEvent(
            run_id=run.id,
            event_time=utcnow(),
            event_type=event_type,
            event_payload=payload,
        )
    )


def reconcile_github_link(session: Session, request: GitHubReconcileRequest) -> GitHubReconcileResult:
    work_item = _resolve_work_item(session, request)
    run = _resolve_run(session, request.run_key)
    state = GitHubLinkState(request.state)

    link = _select_existing_link(session, work_item.id, request)
    if link is None:
        link = GitHubLink(
            work_item_id=work_item.id,
            run_id=run.id if run is not None else None,
            repo=request.repo,
            branch_name=request.branch_name,
            pr_number=request.pr_number,
            pr_url=request.pr_url,
            head_sha=request.head_sha,
            base_branch=request.base_branch,
            state=state,
            metadata_=request.metadata or {},
        )
        session.add(link)
    else:
        if run is not None:
            link.run_id = run.id
        if request.branch_name is not None:
            link.branch_name = request.branch_name
        if request.pr_number is not None:
            link.pr_number = request.pr_number
        if request.pr_url is not None:
            link.pr_url = request.pr_url
        if request.head_sha is not None:
            link.head_sha = request.head_sha
        if request.base_branch is not None:
            link.base_branch = request.base_branch
        link.state = state
        if request.metadata is not None:
            link.metadata_ = request.metadata

    if run is not None and request.branch_name and run.branch_name != request.branch_name:
        run.branch_name = request.branch_name

    _advance_work_item_state(work_item, state)

    event_payload = {
        "repo": request.repo,
        "branch_name": request.branch_name,
        "pr_number": request.pr_number,
        "state": state.value,
    }
    if state == GitHubLinkState.PR_MERGED:
        _emit_run_event(session, run, "pr_merged", event_payload)
    else:
        _emit_run_event(session, run, "pr_linked", event_payload)

    session.flush()
    session.commit()
    return GitHubReconcileResult(
        item_id=work_item.item_id,
        github_link_id=link.id,
        state=link.state.value,
        branch_name=link.branch_name,
        pr_number=link.pr_number,
        work_item_state=work_item.state.value,
        run_id=run.id if run is not None else None,
    )
