"""Prepare bot-owned submission branches from published review packages."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Any

from sqlalchemy.orm import Session

from control_plane.clock import utcnow
from control_plane.models.artifacts import Artifact
from control_plane.models.enums import ArtifactStorageMode
from control_plane.models.run_events import RunEvent
from control_plane.models.runs import Run
from control_plane.models.work_items import WorkItem
from control_plane.services.review_publisher import ReviewPublishRequest, publish_review_package


class SubmissionPrepareError(RuntimeError):
    pass


@dataclass(frozen=True)
class SubmissionPrepareRequest:
    repo_root: str
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


@dataclass(frozen=True)
class SubmissionPrepareResult:
    item_id: str
    run_key: str
    branch_name: str
    worktree_path: str
    commit_sha: str
    package_path: str
    snapshot_path: str
    pr_body_path: str
    pr_title: str
    pr_create_command: str


def _is_canonical_runs_evidence(rel_path: str) -> bool:
    parts = Path(rel_path).parts
    if not parts or parts[0] != "runs":
        return False
    blocked = {"work", "artifacts", "comparisons"}
    return not any(part in blocked for part in parts)


def _canonical_evidence_files(*, repo_root: Path, work_item: WorkItem) -> list[str]:
    files: list[str] = []
    seen: set[str] = set()
    for output in work_item.expected_outputs or []:
        rel_path = _repo_rel(str(output), repo_root)
        if not _is_canonical_runs_evidence(rel_path):
            continue
        candidate = repo_root / rel_path
        if not candidate.exists() or not candidate.is_file():
            continue
        if rel_path in seen:
            continue
        seen.add(rel_path)
        files.append(rel_path)
    return files


def _resolve_run(session: Session, request: SubmissionPrepareRequest) -> tuple[WorkItem, Run]:
    if request.run_key:
        run = session.query(Run).filter(Run.run_key == request.run_key).one_or_none()
        if run is None:
            raise SubmissionPrepareError(f"run not found: {request.run_key}")
        return run.work_item, run
    if not request.item_id:
        raise SubmissionPrepareError("item_id or run_key is required")
    work_item = session.query(WorkItem).filter(WorkItem.item_id == request.item_id).one_or_none()
    if work_item is None:
        raise SubmissionPrepareError(f"work item not found: {request.item_id}")
    if not work_item.runs:
        raise SubmissionPrepareError(f"work item has no runs: {request.item_id}")
    run = sorted(work_item.runs, key=lambda row: (row.attempt, row.created_at or utcnow()))[-1]
    return work_item, run


def _repo_rel(path_text: str, repo_root: Path) -> str:
    path = Path(path_text)
    if path.is_absolute():
        return str(path.resolve().relative_to(repo_root.resolve()))
    return str(path)


def _run_git(repo_root: Path, *args: str, env: dict[str, str] | None = None) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    return result.stdout.strip()


def _branch_exists(repo_root: Path, branch_name: str) -> bool:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "show-ref", "--verify", "--quiet", f"refs/heads/{branch_name}"],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def _worktree_root(item_id: str, requested: str | None) -> Path:
    if requested:
        return Path(requested).resolve()
    return Path(tempfile.mkdtemp(prefix=f"rtlcp-submit-{item_id}-"))


def _copy_into_worktree(*, repo_root: Path, worktree_path: Path, rel_path: str) -> None:
    src = repo_root / rel_path
    dst = worktree_path / rel_path
    if not src.exists():
        raise SubmissionPrepareError(f"review file missing: {rel_path}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def _commit_env() -> dict[str, str]:
    env = dict(**__import__("os").environ)
    env.setdefault("GIT_AUTHOR_NAME", "RTLGen Control Plane")
    env.setdefault("GIT_AUTHOR_EMAIL", "control-plane@rtlgen.local")
    env.setdefault("GIT_COMMITTER_NAME", env["GIT_AUTHOR_NAME"])
    env.setdefault("GIT_COMMITTER_EMAIL", env["GIT_AUTHOR_EMAIL"])
    return env


def _upsert_submission_artifact(
    session: Session,
    *,
    run: Run,
    target_path: str,
    payload: dict[str, Any],
) -> None:
    artifact = (
        session.query(Artifact)
        .filter(Artifact.run_id == run.id, Artifact.kind == "submission_manifest")
        .one_or_none()
    )
    sha256 = __import__("hashlib").sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    if artifact is None:
        artifact = Artifact(
            run_id=run.id,
            kind="submission_manifest",
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


def prepare_submission_branch(session: Session, request: SubmissionPrepareRequest) -> SubmissionPrepareResult:
    repo_root = Path(request.repo_root).resolve()
    work_item, run = _resolve_run(session, request)

    publish_result = publish_review_package(
        session,
        ReviewPublishRequest(
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
        ),
    )

    package_path = Path(publish_result.package_path).resolve()
    package_rel = str(package_path.relative_to(repo_root))
    package_payload = json.loads(package_path.read_text(encoding="utf-8"))
    snapshot_rel = str(package_payload["queue_snapshot"]["path"])
    branch_name = str(package_payload["pr_payload"]["branch"]).strip()
    pr_title = str(package_payload["pr_payload"]["title"]).strip()
    pr_body_md = str(package_payload["pr_payload"]["body_md"])

    review_artifact = package_payload.get("review_artifact") or {}
    review_rel = str(review_artifact.get("path", "")).strip() if isinstance(review_artifact, dict) else ""
    evidence_files = _canonical_evidence_files(repo_root=repo_root, work_item=work_item)
    files_to_copy = [snapshot_rel, package_rel]
    if review_rel:
        files_to_copy.append(review_rel)
    files_to_copy.extend(evidence_files)

    worktree_root = _worktree_root(work_item.item_id, request.worktree_root)
    worktree_path = worktree_root / "repo"
    if _branch_exists(repo_root, branch_name):
        raise SubmissionPrepareError(f"branch already exists: {branch_name}")
    _run_git(repo_root, "worktree", "add", "-b", branch_name, str(worktree_path), "HEAD")

    try:
        for rel_path in files_to_copy:
            _copy_into_worktree(repo_root=repo_root, worktree_path=worktree_path, rel_path=rel_path)

        pr_body_rel = f"control_plane/shadow_exports/review/{work_item.item_id}/pr_body.md"
        pr_body_path = worktree_path / pr_body_rel
        pr_body_path.parent.mkdir(parents=True, exist_ok=True)
        pr_body_path.write_text(pr_body_md, encoding="utf-8")

        _run_git(
            worktree_path,
            "add",
            "-f",
            snapshot_rel,
            package_rel,
            pr_body_rel,
            *( [review_rel] if review_rel else [] ),
            *evidence_files,
        )
        commit_message = request.commit_message or f"control_plane: publish review package for {work_item.item_id}"
        _run_git(worktree_path, "commit", "-m", commit_message, env=_commit_env())
        commit_sha = _run_git(worktree_path, "rev-parse", "HEAD")
    except Exception:
        try:
            _run_git(repo_root, "worktree", "remove", "--force", str(worktree_path))
        except Exception:
            pass
        try:
            _run_git(repo_root, "branch", "-D", branch_name)
        except Exception:
            pass
        raise

    manifest_rel = f"control_plane/shadow_exports/review/{work_item.item_id}/submission_manifest.json"
    manifest_path = repo_root / manifest_rel
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "version": 0.1,
        "generated_utc": utcnow().isoformat().replace("+00:00", "Z"),
        "item_id": work_item.item_id,
        "run_key": run.run_key,
        "branch_name": branch_name,
        "base_branch": request.pr_base,
        "worktree_path": str(worktree_path),
        "commit_sha": commit_sha,
        "package_path": package_rel,
        "snapshot_path": snapshot_rel,
        "review_artifact_path": review_rel or None,
        "evidence_paths": evidence_files,
        "pr_title": pr_title,
        "pr_body_path": pr_body_rel,
        "pr_create_command": (
            f"gh pr create --draft --base {request.pr_base} --head {branch_name} "
            f"--title {json.dumps(pr_title)} --body-file {pr_body_rel}"
        ),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    _upsert_submission_artifact(
        session,
        run=run,
        target_path=manifest_rel,
        payload=manifest,
    )
    session.add(
        RunEvent(
            run_id=run.id,
            event_time=utcnow(),
            event_type="submission_prepared",
            event_payload={
                "branch_name": branch_name,
                "commit_sha": commit_sha,
                "manifest_path": manifest_rel,
            },
        )
    )
    session.commit()
    return SubmissionPrepareResult(
        item_id=work_item.item_id,
        run_key=run.run_key,
        branch_name=branch_name,
        worktree_path=str(worktree_path),
        commit_sha=commit_sha,
        package_path=str(package_path),
        snapshot_path=str(repo_root / snapshot_rel),
        pr_body_path=str(worktree_path / pr_body_rel),
        pr_title=pr_title,
        pr_create_command=manifest["pr_create_command"],
    )
