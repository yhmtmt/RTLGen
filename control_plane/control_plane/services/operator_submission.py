"""One-shot operator command for review publication and PR submission."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path

from sqlalchemy.orm import Session

from control_plane.clock import utcnow
from control_plane.models.artifacts import Artifact
from control_plane.models.enums import ArtifactStorageMode
from control_plane.models.run_events import RunEvent
from control_plane.models.runs import Run
from control_plane.models.work_items import WorkItem
from control_plane.services.review_publisher import ReviewPublishRequest, publish_review_package
from control_plane.services.submission_bridge import SubmissionPrepareRequest, prepare_submission_branch
from control_plane.services.submission_executor import SubmissionExecuteRequest, execute_submission


class OperatorSubmissionError(RuntimeError):
    pass


@dataclass(frozen=True)
class OperatorSubmissionRequest:
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


@dataclass(frozen=True)
class OperatorSubmissionResult:
    item_id: str
    run_key: str
    review_published: bool
    submission_prepared: bool
    submission_prepared_reused: bool
    submission_executed: bool
    branch_name: str
    pr_number: int
    pr_url: str
    manifest_path: str


def _resolve_run(session: Session, request: OperatorSubmissionRequest) -> tuple[WorkItem, Run]:
    if request.run_key:
        run = session.query(Run).filter(Run.run_key == request.run_key).one_or_none()
        if run is None:
            raise OperatorSubmissionError(f"run not found: {request.run_key}")
        return run.work_item, run
    if not request.item_id:
        raise OperatorSubmissionError("item_id or run_key is required")
    work_item = session.query(WorkItem).filter(WorkItem.item_id == request.item_id).one_or_none()
    if work_item is None:
        raise OperatorSubmissionError(f"work item not found: {request.item_id}")
    if not work_item.runs:
        raise OperatorSubmissionError(f"work item has no runs: {request.item_id}")
    run = sorted(work_item.runs, key=lambda row: (row.attempt, row.created_at or utcnow()))[-1]
    return work_item, run


def _default_manifest_path(repo_root: Path, item_id: str) -> Path:
    return repo_root / "control_plane" / "shadow_exports" / "review" / item_id / "submission_manifest.json"


def _upsert_operator_artifact(session: Session, *, run: Run, payload: dict[str, object]) -> None:
    artifact = (
        session.query(Artifact)
        .filter(Artifact.run_id == run.id, Artifact.kind == "operator_submission")
        .one_or_none()
    )
    rel_path = f"control_plane/shadow_exports/review/{run.work_item.item_id}/operator_submission.json"
    sha256 = __import__("hashlib").sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    if artifact is None:
        artifact = Artifact(
            run_id=run.id,
            kind="operator_submission",
            storage_mode=ArtifactStorageMode.REPO,
            path=rel_path,
            sha256=sha256,
            metadata_={},
        )
        session.add(artifact)
    else:
        artifact.storage_mode = ArtifactStorageMode.REPO
        artifact.path = rel_path
        artifact.sha256 = sha256
        artifact.metadata_ = {}


def operate_submission(session: Session, request: OperatorSubmissionRequest) -> OperatorSubmissionResult:
    repo_root = Path(request.repo_root).resolve()
    work_item, run = _resolve_run(session, request)

    review_result = publish_review_package(
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

    manifest_path = _default_manifest_path(repo_root, work_item.item_id)
    submission_prepared = False
    submission_prepared_reused = False
    if manifest_path.exists():
        submission_prepared_reused = True
    else:
        prepare_submission_branch(
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
        submission_prepared = True

    execute_result = execute_submission(
        session,
        SubmissionExecuteRequest(
            repo_root=str(repo_root),
            repo=request.repo,
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
            manifest_path=str(manifest_path),
        ),
    )

    result = OperatorSubmissionResult(
        item_id=work_item.item_id,
        run_key=run.run_key,
        review_published=True,
        submission_prepared=submission_prepared,
        submission_prepared_reused=submission_prepared_reused,
        submission_executed=True,
        branch_name=execute_result.branch_name,
        pr_number=execute_result.pr_number,
        pr_url=execute_result.pr_url,
        manifest_path=execute_result.manifest_path,
    )
    payload = asdict(result)
    payload["review_snapshot_path"] = review_result.snapshot_path
    payload["review_package_path"] = review_result.package_path
    operator_path = repo_root / "control_plane" / "shadow_exports" / "review" / work_item.item_id / "operator_submission.json"
    operator_path.parent.mkdir(parents=True, exist_ok=True)
    operator_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    _upsert_operator_artifact(session, run=run, payload=payload)
    session.add(
        RunEvent(
            run_id=run.id,
            event_time=utcnow(),
            event_type="operator_submission_completed",
            event_payload=payload,
        )
    )
    session.commit()
    return result
