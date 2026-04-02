"""One-shot operator command for review publication and PR submission."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
import subprocess
from typing import Any, Optional

from sqlalchemy.orm import Session

from control_plane.clock import utcnow
from control_plane.models.artifacts import Artifact
from control_plane.models.enums import ArtifactStorageMode, GitHubLinkState, WorkItemState
from control_plane.models.github_links import GitHubLink
from control_plane.models.run_events import RunEvent
from control_plane.models.runs import Run
from control_plane.models.work_items import WorkItem
from control_plane.services.l1_result_consumer import (
    Layer1ConsumeRequest,
    Layer1ResultConsumerError,
    consume_l1_result,
)
from control_plane.services.l2_result_consumer import (
    Layer2ConsumeRequest,
    Layer2ResultConsumerError,
    consume_l2_result,
)
from control_plane.services.review_publisher import (
    ReviewPublishError,
    ReviewPublishRequest,
    publish_review_package,
)
from control_plane.services.submission_bridge import SubmissionPrepareError, SubmissionPrepareRequest, prepare_submission_branch
from control_plane.services.submission_executor import SubmissionExecuteError, SubmissionExecuteRequest, execute_submission
from control_plane.services.docs_paths import resolve_proposal_file


class OperatorSubmissionError(RuntimeError):
    pass


@dataclass(frozen=True)
class SubmissionEligibility:
    item_id: str
    run_key: str | None
    task_type: str
    work_item_state: str
    eligible: bool
    reason: str | None


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
    force: bool = False


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


def _load_existing_submission_identity(manifest_path: Path) -> tuple[str | None, str | None]:
    if not manifest_path.exists():
        return None, None
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        return None, None
    branch_name = str(payload.get("branch_name", "")).strip() or None
    session_id = None
    if branch_name:
        match = re.search(r"/(s[0-9]{8}t[0-9]{6}z)$", branch_name)
        if match:
            session_id = match.group(1)
    return branch_name, session_id


def _load_existing_submission_manifest(manifest_path: Path) -> dict[str, Any] | None:
    if not manifest_path.exists():
        return None
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def _manifest_supporting_files_exist(*, repo_root: Path, manifest: dict[str, Any]) -> bool:
    required_rel_paths: list[str] = []
    for key in ("package_path", "snapshot_path", "pr_body_path"):
        rel_path = str(manifest.get(key, "")).strip()
        if not rel_path:
            return False
        required_rel_paths.append(rel_path)
    review_rel = str(manifest.get("review_artifact_path", "")).strip()
    if review_rel:
        required_rel_paths.append(review_rel)
    for rel_path in manifest.get("evidence_paths") or []:
        rel_text = str(rel_path).strip()
        if rel_text:
            required_rel_paths.append(rel_text)
    for rel_path in manifest.get("supporting_paths") or []:
        rel_text = str(rel_path).strip()
        if rel_text:
            required_rel_paths.append(rel_text)

    frozen_file_map = manifest.get("frozen_file_map") if isinstance(manifest.get("frozen_file_map"), dict) else {}
    for rel_path in required_rel_paths:
        candidate = str(frozen_file_map.get(rel_path, "")).strip()
        path = repo_root / (candidate or rel_path)
        if not path.exists() or not path.is_file():
            return False
    return True


def _is_reusable_submission_manifest(
    session: Session,
    *,
    repo_root: Path,
    work_item: WorkItem,
    run: Run,
    manifest_path: Path,
) -> bool:
    manifest = _load_existing_submission_manifest(manifest_path)
    if manifest is None:
        return False
    if str(manifest.get("run_key", "")).strip() != run.run_key:
        return False
    if not _manifest_supporting_files_exist(repo_root=repo_root, manifest=manifest):
        return False
    branch_name = str(manifest.get("branch_name", "")).strip()
    if not branch_name:
        return False
    link = (
        session.query(GitHubLink)
        .filter(GitHubLink.work_item_id == work_item.id, GitHubLink.branch_name == branch_name)
        .order_by(GitHubLink.updated_at.desc(), GitHubLink.created_at.desc())
        .first()
    )
    if link is None:
        return True
    return link.state in {GitHubLinkState.NONE, GitHubLinkState.BRANCH_CREATED, GitHubLinkState.PR_OPEN}


def _required_review_artifact_kind(task_type: str) -> str | None:
    if task_type == "l1_sweep":
        return "promotion_proposal"
    if task_type == "l2_campaign":
        return "decision_proposal"
    return None


def _is_canonical_runs_evidence(rel_path: str) -> bool:
    parts = Path(rel_path).parts
    if not parts or parts[0] != "runs":
        return False
    blocked = {"work", "artifacts", "comparisons"}
    return not any(part in blocked for part in parts)


def _has_canonical_runs_evidence(work_item: WorkItem) -> bool:
    return any(_is_canonical_runs_evidence(str(output)) for output in (work_item.expected_outputs or []))


def _has_canonical_runs_evidence_diff(*, repo_root: Path, work_item: WorkItem) -> bool:
    evidence_files: list[str] = []
    seen: set[str] = set()
    for output in work_item.expected_outputs or []:
        rel_path = str(output).strip()
        if not _is_canonical_runs_evidence(rel_path):
            continue
        candidate = repo_root / rel_path
        if not candidate.exists() or not candidate.is_file() or rel_path in seen:
            continue
        seen.add(rel_path)
        evidence_files.append(rel_path)
    if not evidence_files:
        return False
    completed = subprocess.run(
        ['git', '-C', str(repo_root), 'status', '--porcelain', '--', *evidence_files],
        check=True,
        capture_output=True,
        text=True,
    )
    return bool(completed.stdout.strip())


def _has_review_artifact(session: Session, *, run_id: str, kind: str | None) -> bool:
    if not kind:
        return False
    artifact = (
        session.query(Artifact)
        .filter(Artifact.run_id == run_id, Artifact.kind == kind)
        .one_or_none()
    )
    return artifact is not None


def _review_artifact(session: Session, *, run_id: str, kind: str | None) -> Artifact | None:
    if not kind:
        return None
    return (
        session.query(Artifact)
        .filter(Artifact.run_id == run_id, Artifact.kind == kind)
        .one_or_none()
    )


def _review_artifact_exists_on_disk(*, repo_root: Path, artifact: Artifact | None) -> bool:
    if artifact is None:
        return False
    path = repo_root / str(artifact.path)
    return path.exists() and path.is_file()


def _latest_submission_failure_reason(session: Session, *, run_id: str) -> str | None:
    event = (
        session.query(RunEvent)
        .filter(RunEvent.run_id == run_id, RunEvent.event_type == "submission_failed")
        .order_by(RunEvent.event_time.desc())
        .first()
    )
    if event is None or not isinstance(event.event_payload, dict):
        return None
    reason = str(event.event_payload.get("error", "")).strip()
    return reason or None


def _proposal_linkage_reason(*, repo_root: Path, work_item: WorkItem) -> str | None:
    payload = (work_item.task_request.request_payload or {}) if work_item.task_request is not None else {}
    developer_loop = payload.get("developer_loop")
    if not isinstance(developer_loop, dict):
        return "missing developer_loop proposal linkage"
    proposal_id = str(developer_loop.get("proposal_id", "")).strip() or None
    proposal_path = str(developer_loop.get("proposal_path", "")).strip() or None
    if proposal_id is None and proposal_path is None:
        return "missing developer_loop proposal linkage"
    proposal_json = resolve_proposal_file(repo_root, proposal_path=proposal_path, proposal_id=proposal_id)
    if proposal_json is None or not proposal_json.exists():
        return "developer_loop proposal linkage does not resolve to a proposal"
    return None


def _terminal_proposal_reason(*, repo_root: Path, work_item: WorkItem) -> str | None:
    payload = (work_item.task_request.request_payload or {}) if work_item.task_request is not None else {}
    developer_loop = payload.get("developer_loop")
    if not isinstance(developer_loop, dict):
        return None
    proposal_id = str(developer_loop.get("proposal_id", "")).strip() or None
    proposal_path = str(developer_loop.get("proposal_path", "")).strip() or None
    proposal_json = resolve_proposal_file(repo_root, proposal_path=proposal_path, proposal_id=proposal_id)
    if proposal_json is None:
        return None
    promotion_result_path = proposal_json.parent / "promotion_result.json"
    if not promotion_result_path.exists():
        return None
    try:
        promotion_result = json.loads(promotion_result_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    decision = str(promotion_result.get("decision", "")).strip().lower()
    if decision in {"promote", "promoted", "superseded", "closed", "rejected"}:
        return f"proposal already finalized with decision={decision}"
    return None


def _ensure_review_artifact_materialized(
    session: Session,
    *,
    repo_root: Path,
    work_item: WorkItem,
    run: Run,
) -> None:
    required_kind = _required_review_artifact_kind(work_item.task_type)
    artifact = _review_artifact(session, run_id=run.id, kind=required_kind)
    if artifact is not None and _review_artifact_exists_on_disk(repo_root=repo_root, artifact=artifact):
        return

    target_path = str(artifact.path).strip() if artifact is not None else None
    if work_item.task_type == "l1_sweep":
        consume_l1_result(
            session,
            Layer1ConsumeRequest(
                repo_root=str(repo_root),
                item_id=work_item.item_id,
                run_key=run.run_key,
                target_path=target_path or None,
            ),
        )
    elif work_item.task_type == "l2_campaign":
        consume_l2_result(
            session,
            Layer2ConsumeRequest(
                repo_root=str(repo_root),
                item_id=work_item.item_id,
                run_key=run.run_key,
                target_path=target_path or None,
            ),
        )
    session.refresh(work_item)
    session.refresh(run)


def _load_review_artifact_payload(
    session: Session,
    *,
    repo_root: Path,
    run_id: str,
    kind: str | None,
) -> dict[str, Any] | None:
    if not kind:
        return None
    artifact = (
        session.query(Artifact)
        .filter(Artifact.run_id == run_id, Artifact.kind == kind)
        .one_or_none()
    )
    if artifact is None:
        return None
    path = repo_root / str(artifact.path)
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def _validate_submission_review_payload(repo_root: Path, *, session: Session, work_item: WorkItem, run: Run) -> None:
    required_kind = _required_review_artifact_kind(work_item.task_type)
    payload = _load_review_artifact_payload(session, repo_root=repo_root, run_id=run.id, kind=required_kind)
    if not isinstance(payload, dict):
        return
    if work_item.task_type != "l2_campaign":
        return
    evaluation_record = payload.get("evaluation_record")
    proposal_assessment = payload.get("proposal_assessment")
    if not isinstance(evaluation_record, dict):
        return
    evaluation_mode = str(evaluation_record.get("evaluation_mode", "")).strip()
    comparison_role = str(evaluation_record.get("comparison_role", "")).strip()
    if evaluation_mode != "paired_comparison" or comparison_role != "candidate":
        return
    abstraction_layer = str(evaluation_record.get("abstraction_layer", "")).strip()
    if not abstraction_layer:
        raise OperatorSubmissionError(
            f"work item {work_item.item_id} is not eligible for submission: invalid decision_proposal payload: missing abstraction_layer"
        )
    if not isinstance(proposal_assessment, dict):
        raise OperatorSubmissionError(
            f"work item {work_item.item_id} is not eligible for submission: invalid decision_proposal payload: missing proposal_assessment"
        )
    baseline_item_id = str(proposal_assessment.get("baseline_item_id", "")).strip()
    if not baseline_item_id:
        raise OperatorSubmissionError(
            f"work item {work_item.item_id} is not eligible for submission: invalid decision_proposal payload: missing baseline_item_id"
        )
    outcome = str(proposal_assessment.get("outcome", "")).strip()
    if outcome == "unavailable":
        raise OperatorSubmissionError(
            f"work item {work_item.item_id} is not eligible for submission: invalid decision_proposal payload: unresolved paired baseline"
        )


def _check_submission_eligibility(session: Session, *, repo_root: Path, work_item: WorkItem, run: Run, force: bool) -> None:
    eligibility = assess_submission_eligibility(session, work_item=work_item, run=run, repo_root=repo_root)
    if force or eligibility.eligible:
        return
    raise OperatorSubmissionError(
        f"work item {work_item.item_id} is not eligible for submission: {eligibility.reason}"
    )


def assess_submission_eligibility(
    session: Session,
    *,
    work_item: WorkItem,
    run: Optional[Run] = None,
    repo_root: Path | None = None,
) -> SubmissionEligibility:
    latest_run = run
    if latest_run is None and work_item.runs:
        latest_run = sorted(work_item.runs, key=lambda row: (row.attempt, row.created_at or utcnow()))[-1]

    reason: str | None = None
    if work_item.state not in {WorkItemState.ARTIFACT_SYNC, WorkItemState.AWAITING_REVIEW}:
        reason = f"state={work_item.state.value}"
    elif latest_run is None:
        reason = "no_runs"
    else:
        required_kind = _required_review_artifact_kind(work_item.task_type)
        artifact = _review_artifact(session, run_id=latest_run.id, kind=required_kind)
        submission_failure_reason = _latest_submission_failure_reason(session, run_id=latest_run.id)
        if not required_kind:
            reason = f"unsupported_task_type={work_item.task_type}"
        elif submission_failure_reason is not None:
            reason = submission_failure_reason
        elif repo_root is not None:
            proposal_linkage_reason = _proposal_linkage_reason(repo_root=repo_root, work_item=work_item)
            terminal_reason = _terminal_proposal_reason(repo_root=repo_root, work_item=work_item)
            manifest_path = _default_manifest_path(repo_root, work_item.item_id)
            reusable_manifest = _is_reusable_submission_manifest(
                session,
                repo_root=repo_root,
                work_item=work_item,
                run=latest_run,
                manifest_path=manifest_path,
            )
            if proposal_linkage_reason is not None:
                reason = proposal_linkage_reason
            elif terminal_reason is not None:
                reason = terminal_reason
            elif artifact is None:
                reason = f"missing {required_kind} artifact"
            elif not _review_artifact_exists_on_disk(repo_root=repo_root, artifact=artifact):
                reason = f"missing {required_kind} review file"
            elif not _has_canonical_runs_evidence(work_item):
                reason = "missing canonical runs evidence outputs"
            elif not reusable_manifest and not _has_canonical_runs_evidence_diff(repo_root=repo_root, work_item=work_item):
                reason = "no canonical runs evidence diff"
        elif artifact is None:
            reason = f"missing {required_kind} artifact"
        elif not _has_canonical_runs_evidence(work_item):
            reason = "missing canonical runs evidence outputs"

    return SubmissionEligibility(
        item_id=work_item.item_id,
        run_key=latest_run.run_key if latest_run is not None else None,
        task_type=work_item.task_type,
        work_item_state=work_item.state.value,
        eligible=reason is None,
        reason=reason,
    )


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
    try:
        _ensure_review_artifact_materialized(session, repo_root=repo_root, work_item=work_item, run=run)
        _check_submission_eligibility(session, repo_root=repo_root, work_item=work_item, run=run, force=request.force)
        if not request.force:
            _validate_submission_review_payload(repo_root, session=session, work_item=work_item, run=run)
    except (
        Layer1ResultConsumerError,
        Layer2ResultConsumerError,
        ReviewPublishError,
        SubmissionPrepareError,
        SubmissionExecuteError,
    ) as exc:
        raise OperatorSubmissionError(str(exc)) from exc
    manifest_path = _default_manifest_path(repo_root, work_item.item_id)
    reusable_manifest = _is_reusable_submission_manifest(
        session,
        repo_root=repo_root,
        work_item=work_item,
        run=run,
        manifest_path=manifest_path,
    )
    existing_branch_name, existing_session_id = (
        _load_existing_submission_identity(manifest_path) if reusable_manifest else (None, None)
    )
    effective_branch_name = request.branch_name or existing_branch_name
    effective_session_id = request.session_id or existing_session_id

    try:
        review_result = publish_review_package(
            session,
            ReviewPublishRequest(
                repo_root=str(repo_root),
                item_id=work_item.item_id,
                run_key=run.run_key,
                evaluator_id=request.evaluator_id,
                session_id=effective_session_id,
                host=request.host,
                executor=request.executor,
                branch_name=effective_branch_name,
                snapshot_target_path=request.snapshot_target_path,
                package_target_path=request.package_target_path,
            ),
        )

        submission_prepared = False
        submission_prepared_reused = False
        if reusable_manifest:
            submission_prepared_reused = True
        else:
            prepare_submission_branch(
                session,
                SubmissionPrepareRequest(
                    repo_root=str(repo_root),
                    item_id=work_item.item_id,
                    run_key=run.run_key,
                    evaluator_id=request.evaluator_id,
                    session_id=effective_session_id,
                    host=request.host,
                    executor=request.executor,
                    branch_name=effective_branch_name,
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
                session_id=effective_session_id,
                host=request.host,
                executor=request.executor,
                branch_name=effective_branch_name,
                snapshot_target_path=request.snapshot_target_path,
                package_target_path=request.package_target_path,
                worktree_root=request.worktree_root,
                commit_message=request.commit_message,
                pr_base=request.pr_base,
                manifest_path=str(manifest_path),
            ),
        )
    except (ReviewPublishError, SubmissionPrepareError, SubmissionExecuteError) as exc:
        raise OperatorSubmissionError(str(exc)) from exc

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
