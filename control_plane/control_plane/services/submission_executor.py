"""Execute a prepared submission branch against GitHub and reconcile the PR."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import shutil
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
from control_plane.services.review_publisher import ReviewPublishRequest, publish_review_package
from control_plane.services.submission_bridge import (
    SubmissionPrepareRequest,
    _canonical_runs_diff_paths,
    _freeze_file,
    _review_linked_supporting_files,
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
        rel_path = str(output).strip()
        if not rel_path or not _is_canonical_runs_evidence(rel_path):
            continue
        candidate = repo_root / rel_path
        if not candidate.exists() or not candidate.is_file():
            continue
        if rel_path in seen:
            continue
        seen.add(rel_path)
        files.append(rel_path)
    return files


def _load_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SubmissionExecuteError(f"submission manifest not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _run_cmd(args: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> str:
    result = subprocess.run(args, cwd=str(cwd), check=True, text=True, capture_output=True, env=env)
    return result.stdout.strip()


def _run_cmd_capture(args: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=str(cwd), check=False, text=True, capture_output=True)


def _format_failed_command(proc: subprocess.CompletedProcess[str]) -> str:
    stderr = (proc.stderr or "").strip()
    stdout = (proc.stdout or "").strip()
    details: list[str] = []
    if stderr:
        details.append(f"stderr={stderr}")
    if stdout:
        details.append(f"stdout={stdout}")
    suffix = f": {'; '.join(details)}" if details else ""
    return f"command {proc.args!r} failed with exit code {proc.returncode}{suffix}"


def _format_pr_create_failure(
    *,
    branch_name: str,
    pr_base: str,
    worktree_path: Path,
    pr_body_path: Path,
    pr_view_before: subprocess.CompletedProcess[str],
    pr_create: subprocess.CompletedProcess[str],
    pr_view_after: subprocess.CompletedProcess[str],
) -> str:
    details = {
        'branch_name': branch_name,
        'pr_base': pr_base,
        'worktree_path': str(worktree_path),
        'body_file': str(pr_body_path),
        'body_file_exists': pr_body_path.exists(),
        'body_file_size': pr_body_path.stat().st_size if pr_body_path.exists() else None,
        'pr_view_before': _format_failed_command(pr_view_before),
        'pr_create': _format_failed_command(pr_create),
        'pr_view_after': _format_failed_command(pr_view_after),
    }
    return "gh pr create failed: " + json.dumps(details, sort_keys=True)


def _repo_diff_paths(*, cwd: Path, base_ref: str) -> list[str]:
    output = _run_cmd(["git", "diff", "--name-only", f"{base_ref}...HEAD"], cwd=cwd)
    return [line.strip() for line in output.splitlines() if line.strip()]


def _commit_env() -> dict[str, str]:
    env = dict(**__import__("os").environ)
    env.setdefault("GIT_AUTHOR_NAME", "RTLGen Control Plane")
    env.setdefault("GIT_AUTHOR_EMAIL", "control-plane@rtlgen.local")
    env.setdefault("GIT_COMMITTER_NAME", env["GIT_AUTHOR_NAME"])
    env.setdefault("GIT_COMMITTER_EMAIL", env["GIT_AUTHOR_EMAIL"])
    return env


def _copy_into_worktree(*, repo_root: Path, worktree_path: Path, rel_path: str, target_rel_path: str | None = None) -> None:
    src = repo_root / rel_path
    dst = worktree_path / (target_rel_path or rel_path)
    if not src.exists():
        raise SubmissionExecuteError(f"review file missing: {rel_path}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def _has_origin_remote(repo_root: Path) -> bool:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "remote", "get-url", "origin"],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def _resolve_submission_base(*, repo_root: Path, pr_base: str) -> tuple[str, str]:
    base_branch = pr_base.strip() or "master"
    if _has_origin_remote(repo_root):
        fetch = subprocess.run(
            ["git", "-C", str(repo_root), "fetch", "origin", base_branch],
            capture_output=True,
            text=True,
        )
        if fetch.returncode != 0:
            raise SubmissionExecuteError(fetch.stderr.strip() or f"failed to fetch origin/{base_branch}")
        base_ref = f"refs/remotes/origin/{base_branch}"
    else:
        base_ref = f"refs/heads/{base_branch}"
    try:
        base_commit = _run_cmd(["git", "rev-parse", base_ref], cwd=repo_root)
    except subprocess.CalledProcessError as exc:
        raise SubmissionExecuteError(f"submission base not found: {base_ref}") from exc
    return base_ref, base_commit


def _refresh_submission_worktree(
    *,
    repo_root: Path,
    worktree_path: Path,
    manifest: dict[str, Any],
    item_id: str,
    branch_name: str,
    pr_base: str,
) -> tuple[str, str]:
    package_rel = str(manifest.get("package_path", "")).strip()
    snapshot_rel = str(manifest.get("snapshot_path", "")).strip()
    review_rel = str(manifest.get("review_artifact_path") or "").strip()
    evidence_paths = [str(path).strip() for path in (manifest.get("evidence_paths") or []) if str(path).strip()]
    supporting_paths = [str(path).strip() for path in (manifest.get("supporting_paths") or []) if str(path).strip()]
    pr_body_rel = str(manifest.get("pr_body_path", "")).strip()
    if not package_rel or not snapshot_rel or not pr_body_rel:
        raise SubmissionExecuteError("submission manifest is missing package_path, snapshot_path, or pr_body_path")

    frozen_file_map = manifest.get("frozen_file_map") if isinstance(manifest.get("frozen_file_map"), dict) else {}

    def _source_rel(rel_path: str) -> str:
        candidate = frozen_file_map.get(rel_path)
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
        return rel_path

    package_source_rel = _source_rel(package_rel)
    package_path = repo_root / package_source_rel
    if not package_path.exists():
        raise SubmissionExecuteError(f"review package does not exist: {package_path}")
    json.loads(package_path.read_text(encoding="utf-8"))

    submission_base_commit = str(manifest.get("submission_base_commit", "")).strip()
    if not submission_base_commit:
        _submission_base_ref, submission_base_commit = _resolve_submission_base(repo_root=repo_root, pr_base=pr_base)
    _run_cmd(["git", "checkout", branch_name], cwd=worktree_path)
    _run_cmd(["git", "reset", "--hard", submission_base_commit], cwd=worktree_path)
    _run_cmd(["git", "clean", "-fd"], cwd=worktree_path)

    for rel_path in [snapshot_rel, package_rel, *([review_rel] if review_rel else []), *evidence_paths, *supporting_paths, pr_body_rel]:
        _copy_into_worktree(
            repo_root=repo_root,
            worktree_path=worktree_path,
            rel_path=_source_rel(rel_path),
            target_rel_path=rel_path,
        )

    add_args = ["git", "add", "-f", snapshot_rel, package_rel, pr_body_rel]
    if review_rel:
        add_args.append(review_rel)
    add_args.extend(evidence_paths)
    add_args.extend(supporting_paths)
    _run_cmd(add_args, cwd=worktree_path)

    status = _run_cmd(["git", "status", "--porcelain"], cwd=worktree_path)
    if status.strip():
        _run_cmd(
            ["git", "commit", "-m", f"control_plane: refresh review package for {item_id}"],
            cwd=worktree_path,
            env=_commit_env(),
        )
    return _run_cmd(["git", "rev-parse", "HEAD"], cwd=worktree_path), submission_base_commit


def _refresh_manifest_frozen_file_map(
    *,
    repo_root: Path,
    manifest: dict[str, Any],
    item_id: str,
    run_key: str,
) -> None:
    package_rel = str(manifest.get("package_path", "")).strip()
    snapshot_rel = str(manifest.get("snapshot_path", "")).strip()
    review_rel = str(manifest.get("review_artifact_path") or "").strip()
    pr_body_rel = str(manifest.get("pr_body_path", "")).strip()
    evidence_paths = [str(path).strip() for path in (manifest.get("evidence_paths") or []) if str(path).strip()]
    supporting_paths = [str(path).strip() for path in (manifest.get("supporting_paths") or []) if str(path).strip()]

    previous_frozen_file_map = manifest.get("frozen_file_map") if isinstance(manifest.get("frozen_file_map"), dict) else {}
    frozen_file_map: dict[str, str] = {}
    required_paths = [snapshot_rel, package_rel, *([review_rel] if review_rel else []), *evidence_paths, *supporting_paths, pr_body_rel]
    for rel_path in required_paths:
        if not rel_path:
            continue
        live_path = repo_root / rel_path
        if live_path.exists():
            frozen_file_map[rel_path] = _freeze_file(
                repo_root=repo_root,
                item_id=item_id,
                run_key=run_key,
                rel_path=rel_path,
            )
            continue
        previous_rel = str(previous_frozen_file_map.get(rel_path, "")).strip()
        previous_path = repo_root / previous_rel if previous_rel else None
        if previous_rel and previous_path is not None and previous_path.exists():
            frozen_file_map[rel_path] = previous_rel
            continue
        raise SubmissionExecuteError(f"review file missing: {rel_path}")
    manifest["frozen_file_map"] = frozen_file_map


def _resolve_pr_body_path(*, worktree_path: Path, manifest: dict[str, Any]) -> Path:
    pr_body_path = Path(str(manifest.get("pr_body_path", "")).strip())
    if not pr_body_path.is_absolute():
        pr_body_path = worktree_path / pr_body_path
    return pr_body_path


def _post_submit_refresh(
    session: Session,
    *,
    repo_root: Path,
    request: SubmissionExecuteRequest,
    work_item: WorkItem,
    run: Run,
    manifest_path: Path,
    manifest: dict[str, Any],
    worktree_path: Path,
    branch_name: str,
    pr_base: str,
    pr_number: int,
) -> tuple[str, str, dict[str, Any]]:
    publish_review_package(
        session,
        ReviewPublishRequest(
            repo_root=str(repo_root),
            item_id=work_item.item_id,
            run_key=run.run_key,
            evaluator_id=request.evaluator_id,
            session_id=request.session_id,
            host=request.host,
            executor=request.executor,
            branch_name=branch_name,
            snapshot_target_path=request.snapshot_target_path,
            package_target_path=request.package_target_path,
        ),
    )
    manifest = _load_manifest(manifest_path)
    commit_sha, submission_base_commit = _refresh_submission_worktree(
        repo_root=repo_root,
        worktree_path=worktree_path,
        manifest=manifest,
        item_id=work_item.item_id,
        branch_name=branch_name,
        pr_base=pr_base,
    )
    manifest["commit_sha"] = commit_sha
    manifest["submission_base_commit"] = submission_base_commit
    manifest["generated_utc"] = utcnow().isoformat().replace("+00:00", "Z")
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    _run_cmd(["git", "push", "--force-with-lease", "-u", "origin", branch_name], cwd=worktree_path)
    pr_body_path = _resolve_pr_body_path(worktree_path=worktree_path, manifest=manifest)
    pr_edit_proc = _run_cmd_capture(
        [
            "gh",
            "--repo",
            request.repo,
            "pr",
            "edit",
            str(pr_number),
            "--body-file",
            str(pr_body_path),
        ],
        cwd=worktree_path,
    )
    if pr_edit_proc.returncode != 0:
        raise SubmissionExecuteError(
            f"gh pr edit failed for PR #{pr_number}: {_format_failed_command(pr_edit_proc)}"
        )
    return commit_sha, submission_base_commit, manifest


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
    package_rel = str(manifest.get("package_path", "")).strip()
    package_payload = {}
    if package_rel:
        package_path = repo_root / package_rel
        if package_path.exists():
            try:
                loaded = json.loads(package_path.read_text(encoding="utf-8"))
            except Exception:
                loaded = None
            if isinstance(loaded, dict):
                package_payload = loaded
    manifest["evidence_paths"] = _canonical_evidence_files(repo_root=repo_root, work_item=work_item)
    manifest["supporting_paths"] = _review_linked_supporting_files(repo_root=repo_root, package_payload=package_payload)
    manifest["canonical_diff_paths"] = _canonical_runs_diff_paths(*manifest["evidence_paths"], *manifest["supporting_paths"])
    _refresh_manifest_frozen_file_map(
        repo_root=repo_root,
        manifest=manifest,
        item_id=work_item.item_id,
        run_key=run.run_key,
    )

    branch_name = str(manifest.get("branch_name", "")).strip()
    if not branch_name:
        raise SubmissionExecuteError("submission manifest is missing branch_name")
    worktree_path = Path(str(manifest.get("worktree_path", "")).strip()).resolve()
    if not worktree_path.exists():
        raise SubmissionExecuteError(f"submission worktree does not exist: {worktree_path}")
    commit_sha = str(manifest.get("commit_sha", "")).strip()
    pr_base = str(manifest.get("base_branch", request.pr_base)).strip() or request.pr_base
    pr_title = str(manifest.get("pr_title", "")).strip()
    pr_body_path = _resolve_pr_body_path(worktree_path=worktree_path, manifest=manifest)
    commit_sha, submission_base_commit = _refresh_submission_worktree(
        repo_root=repo_root,
        worktree_path=worktree_path,
        manifest=manifest,
        item_id=work_item.item_id,
        branch_name=branch_name,
        pr_base=pr_base,
    )
    evidence_paths = [str(path).strip() for path in (manifest.get("evidence_paths") or []) if str(path).strip()]
    branch_diff_paths = _repo_diff_paths(cwd=worktree_path, base_ref=submission_base_commit)
    if evidence_paths and not any(path in branch_diff_paths for path in evidence_paths):
        raise SubmissionExecuteError(
            f"submission branch has no canonical runs evidence diff for {work_item.item_id}"
        )
    manifest["commit_sha"] = commit_sha
    manifest["submission_base_commit"] = submission_base_commit
    manifest["generated_utc"] = utcnow().isoformat().replace("+00:00", "Z")
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    _run_cmd(["git", "push", "--force-with-lease", "-u", "origin", branch_name], cwd=worktree_path)
    pr_view_args = [
        "gh",
        "--repo",
        request.repo,
        "pr",
        "view",
        branch_name,
        "--json",
        "number,url,headRefName,baseRefName",
    ]
    pr_view_proc = _run_cmd_capture(pr_view_args, cwd=worktree_path)
    if pr_view_proc.returncode == 0:
        pr_view = json.loads(pr_view_proc.stdout.strip())
        pr_url = str(pr_view.get("url", "")).strip()
    else:
        pr_create_proc = _run_cmd_capture(
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
        if pr_create_proc.returncode != 0:
            pr_view_retry = _run_cmd_capture(pr_view_args, cwd=worktree_path)
            if pr_view_retry.returncode == 0:
                pr_view = json.loads(pr_view_retry.stdout.strip())
                pr_url = str(pr_view.get("url", "")).strip()
            else:
                raise SubmissionExecuteError(
                    _format_pr_create_failure(
                        branch_name=branch_name,
                        pr_base=pr_base,
                        worktree_path=worktree_path,
                        pr_body_path=pr_body_path,
                        pr_view_before=pr_view_proc,
                        pr_create=pr_create_proc,
                        pr_view_after=pr_view_retry,
                    )
                )
        else:
            pr_url = pr_create_proc.stdout.strip().splitlines()[-1].strip()
            if not pr_url:
                raise SubmissionExecuteError("gh pr create did not return a PR URL")
            pr_view_json = _run_cmd(pr_view_args, cwd=worktree_path)
            pr_view = json.loads(pr_view_json)
    try:
        pr_number = int(pr_view["number"])
    except Exception as exc:
        raise SubmissionExecuteError(
            f"gh pr view did not return a valid PR number: {json.dumps(pr_view, sort_keys=True)}"
        ) from exc

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
        "submission_base_commit": submission_base_commit,
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
                "submission_base_commit": submission_base_commit,
                "manifest_path": execution_payload["manifest_path"],
            },
        )
    )
    session.flush()

    commit_sha, submission_base_commit, manifest = _post_submit_refresh(
        session,
        repo_root=repo_root,
        request=request,
        work_item=work_item,
        run=run,
        manifest_path=manifest_path,
        manifest=manifest,
        worktree_path=worktree_path,
        branch_name=branch_name,
        pr_base=pr_base,
        pr_number=pr_number,
    )

    execution_payload["commit_sha"] = commit_sha
    execution_payload["submission_base_commit"] = submission_base_commit
    execution_path.write_text(json.dumps(execution_payload, indent=2) + "\n", encoding="utf-8")
    _upsert_execution_artifact(
        session,
        run=run,
        target_path=execution_rel,
        payload=execution_payload,
    )

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
