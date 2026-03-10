"""Execute a prepared submission branch against GitHub and reconcile the PR."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
from typing import Any

from sqlalchemy.orm import Session

from control_plane.clock import utcnow
from control_plane.models.artifacts import Artifact
from control_plane.models.enums import ArtifactStorageMode
from control_plane.models.run_events import RunEvent
from control_plane.models.runs import Run
from control_plane.models.work_items import WorkItem
from control_plane.services.github_bridge import GitHubReconcileRequest, reconcile_github_link
from control_plane.services.submission_bridge import (
    SubmissionPrepareRequest,
    prepare_submission_branch,
)


class SubmissionExecuteError(RuntimeError):
    pass


@dataclass(frozen=True)
class SubmissionExecuteRequest:
    repo_root: str
    repo: str
    item_id: str | None = None
    run_key: str | None = None
    evaluator_id: str = "control_plane"
    session_id: str | None = None
    host: str | None = None
    executor: str = "@control_plane"
    branch_name: str | None = None
    snapshot_target_path: str | None = None
    package_target_path: str | None = None
    worktree_root: str | None = None
    commit_message: str | None = None
    pr_base: str = "master"
    manifest_path: str | None = None


@dataclass(frozen=True)
class SubmissionExecuteResult:
    item_id: str
    run_key: str
    branch_name: str
    commit_sha: str
    pr_number: int
    pr_url: str
    manifest_path: str
    github_link_id: str
    work_item_state: str


def _resolve_run(session: Session, request: SubmissionExecuteRequest) -> tuple[WorkItem, Run]:
    if request.run_key:
        run = session.query(Run).filter(Run.run_key == request.run_key).one_or_none()
        if run is None:
            raise SubmissionExecuteError(f"run not found: {request.run_key}")
        return run.work_item, run
    if not request.item_id:
        raise SubmissionExecuteError("item_id or run_key is required")
    work_item = session.query(WorkItem).filter(WorkItem.item_id == request.item_id).one_or_none()
    if work_item is None:
        raise SubmissionExecuteError(f"work item not found: {request.item_id}")
    if not work_item.runs:
        raise SubmissionExecuteError(f"work item has no runs: {request.item_id}")
    run = sorted(work_item.runs, key=lambda row: (row.attempt, row.created_at or utcnow()))[-1]
    return work_item, run


def _default_manifest_path(repo_root: Path, item_id: str) -> Path:
    return repo_root / "control_plane" / "shadow_exports" / "review" / item_id / "submission_manifest.json"


def _load_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SubmissionExecuteError(f"submission manifest not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _run_cmd(args: list[str], *, cwd: Path) -> str:
    result = subprocess.run(args, cwd=str(cwd), check=True, text=True, capture_output=True)
    return result.stdout.strip()


def _upsert_execution_artifact(
    session: Session,
    *,
    run: Run,
    target_path: str,
    payload: dict[str, Any],
) -> None:
    artifact = (
        session.query(Artifact)
        .filter(Artifact.run_id == run.id, Artifact.kind == "submission_execution")
        .one_or_none()
    )
    sha256 = __import__("hashlib").sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    if artifact is None:
        artifact = Artifact(
            run_id=run.id,
            kind="submission_execution",
            storage_mode=ArtifactStorageMode.REPO,
            path=target_path,
            sha256=sha256,
            metadata_={},
        )
        session.add(artifact)
    else:
        artifact.storage_mode = ArtifactStorageMode.REPO
        artifact.path = target_path
        artifact.sha256 = sha256
        artifact.metadata_ = {}


def execute_submission(session: Session, request: SubmissionExecuteRequest) -> SubmissionExecuteResult:
    repo_root = Path(request.repo_root).resolve()
    work_item, run = _resolve_run(session, request)

    manifest_path = Path(request.manifest_path).resolve() if request.manifest_path else _default_manifest_path(repo_root, work_item.item_id)
    if not manifest_path.exists():
        prepared = prepare_submission_branch(
            session,
            SubmissionPrepareRequest(
                repo_root=str(repo_root),
                item_id=work_item.item_id,
                run_key=run.run_key,
                evaluator_id=request.evaluator_id,
                session_id=request.session_id,
                host=request.host,
                executor=request.executor,
                branch_name=request.branch_name,
                snapshot_target_path=request.snapshot_target_path,
                package_target_path=request.package_target_path,
                worktree_root=request.worktree_root,
                commit_message=request.commit_message,
                pr_base=request.pr_base,
            ),
        )
        manifest_path = repo_root / "control_plane" / "shadow_exports" / "review" / work_item.item_id / "submission_manifest.json"
    manifest = _load_manifest(manifest_path)

    branch_name = str(manifest.get("branch_name", "")).strip()
    if not branch_name:
        raise SubmissionExecuteError("submission manifest is missing branch_name")
    worktree_path = Path(str(manifest.get("worktree_path", "")).strip()).resolve()
    if not worktree_path.exists():
        raise SubmissionExecuteError(f"submission worktree does not exist: {worktree_path}")
    commit_sha = str(manifest.get("commit_sha", "")).strip()
    pr_base = str(manifest.get("base_branch", request.pr_base)).strip() or request.pr_base
    pr_title = str(manifest.get("pr_title", "")).strip()
    pr_body_path = Path(str(manifest.get("pr_body_path", "")).strip())
    if not pr_body_path.is_absolute():
        pr_body_path = worktree_path / pr_body_path
    if not pr_body_path.exists():
        raise SubmissionExecuteError(f"PR body file does not exist: {pr_body_path}")

    _run_cmd(["git", "push", "-u", "origin", branch_name], cwd=worktree_path)
    pr_create_out = _run_cmd(
        [
            "gh",
            "--repo",
            request.repo,
            "pr",
            "create",
            "--draft",
            "--base",
            pr_base,
            "--head",
            branch_name,
            "--title",
            pr_title,
            "--body-file",
            str(pr_body_path),
        ],
        cwd=worktree_path,
    )
    pr_url = pr_create_out.strip().splitlines()[-1].strip()
    if not pr_url:
        raise SubmissionExecuteError("gh pr create did not return a PR URL")

    pr_view_json = _run_cmd(
        [
            "gh",
            "--repo",
            request.repo,
            "pr",
            "view",
            branch_name,
            "--json",
            "number,url,headRefName,baseRefName",
        ],
        cwd=worktree_path,
    )
    pr_view = json.loads(pr_view_json)
    try:
        pr_number = int(pr_view["number"])
    except Exception as exc:
        raise SubmissionExecuteError(f"gh pr view did not return a valid PR number: {pr_view_json}") from exc

    reconcile = reconcile_github_link(
        session,
        GitHubReconcileRequest(
            repo=request.repo,
            item_id=work_item.item_id,
            branch_name=str(pr_view.get("headRefName", branch_name)).strip() or branch_name,
            pr_number=pr_number,
            pr_url=str(pr_view.get("url", pr_url)).strip() or pr_url,
            base_branch=str(pr_view.get("baseRefName", pr_base)).strip() or pr_base,
            head_sha=commit_sha or None,
            state="pr_open",
            run_key=run.run_key,
            metadata={"submission_manifest": str(manifest_path.relative_to(repo_root))},
        ),
    )

    execution_rel = f"control_plane/shadow_exports/review/{work_item.item_id}/submission_execution.json"
    execution_path = repo_root / execution_rel
    execution_path.parent.mkdir(parents=True, exist_ok=True)
    execution_payload = {
        "version": 0.1,
        "generated_utc": utcnow().isoformat().replace("+00:00", "Z"),
        "item_id": work_item.item_id,
        "run_key": run.run_key,
        "branch_name": branch_name,
        "commit_sha": commit_sha,
        "pr_number": pr_number,
        "pr_url": str(pr_view.get("url", pr_url)).strip() or pr_url,
        "repo": request.repo,
        "manifest_path": str(manifest_path.relative_to(repo_root)),
        "pr_base": str(pr_view.get("baseRefName", pr_base)).strip() or pr_base,
    }
    execution_path.write_text(json.dumps(execution_payload, indent=2) + "\n", encoding="utf-8")

    _upsert_execution_artifact(
        session,
        run=run,
        target_path=execution_rel,
        payload=execution_payload,
    )
    session.add(
        RunEvent(
            run_id=run.id,
            event_time=utcnow(),
            event_type="submission_executed",
            event_payload={
                "branch_name": branch_name,
                "pr_number": pr_number,
                "pr_url": execution_payload["pr_url"],
                "manifest_path": execution_payload["manifest_path"],
            },
        )
    )
    session.commit()
    return SubmissionExecuteResult(
        item_id=work_item.item_id,
        run_key=run.run_key,
        branch_name=branch_name,
        commit_sha=commit_sha,
        pr_number=pr_number,
        pr_url=execution_payload["pr_url"],
        manifest_path=str(manifest_path),
        github_link_id=reconcile.github_link_id,
        work_item_state=reconcile.work_item_state,
    )
