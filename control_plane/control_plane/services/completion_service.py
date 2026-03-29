"""Notebook-side processing for completed work items."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from control_plane.artifact_policy import is_transportable_expected_output
from control_plane.models.enums import WorkItemState
from control_plane.models.run_events import RunEvent
from control_plane.models.runs import Run
from control_plane.models.work_items import WorkItem
from control_plane.services.l1_result_consumer import Layer1ConsumeRequest, consume_l1_result
from control_plane.services.l2_result_consumer import Layer2ConsumeRequest, consume_l2_result
from control_plane.services.operator_submission import (
    OperatorSubmissionError,
    OperatorSubmissionRequest,
    operate_submission,
)


class CompletionProcessingError(RuntimeError):
    pass


@dataclass(frozen=True)
class CompletionProcessRequest:
    repo_root: str
    repo: str | None = None
    item_id: str | None = None
    submit: bool = False
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
class CompletionProcessResult:
    item_id: str
    run_key: str
    task_type: str
    consumed: bool
    submitted: bool
    work_item_state: str
    target_path: str | None = None
    pr_url: str | None = None
    submission_error: str | None = None


def _latest_run_for_item(work_item: WorkItem) -> Run:
    if not work_item.runs:
        raise CompletionProcessingError(f"work item has no runs: {work_item.item_id}")
    return sorted(work_item.runs, key=lambda row: (row.attempt, row.created_at))[ -1]


def _is_materializable_supporting_output(rel_path: str) -> bool:
    path = Path(rel_path)
    if path.is_absolute():
        return False
    if ".." in path.parts:
        return False
    return str(path).startswith("runs/")


def _materialize_expected_output_artifacts(*, repo_root: str, run: Run) -> list[str]:
    repo_path = Path(repo_root).resolve()
    materialized: list[str] = []
    for artifact in run.artifacts:
        if artifact.kind not in {"expected_output", "supporting_output"}:
            continue
        rel_path = str(artifact.path).strip()
        metadata = artifact.metadata_ or {}
        transport_policy = metadata.get("transport_policy")
        if artifact.kind == "expected_output":
            if not is_transportable_expected_output(rel_path):
                continue
            if transport_policy not in (None, "inline_text_evidence"):
                continue
        else:
            if not _is_materializable_supporting_output(rel_path):
                continue
            if transport_policy != "inline_text_supporting":
                continue
        inline_text = metadata.get("inline_utf8")
        if not isinstance(inline_text, str):
            continue
        if not rel_path:
            continue
        path = repo_path / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(inline_text, encoding="utf-8")
        materialized.append(rel_path)
    return materialized


def _record_submission_failure(session: Session, *, run: Run, error: str) -> None:
    session.add(
        RunEvent(
            run_id=run.id,
            event_time=utcnow(),
            event_type="submission_failed",
            event_payload={"error": error},
        )
    )
    session.commit()


def _iter_target_items(session: Session, *, item_id: str | None) -> list[WorkItem]:
    query = session.query(WorkItem)
    if item_id:
        work_item = query.filter(WorkItem.item_id == item_id).one_or_none()
        if work_item is None:
            raise CompletionProcessingError(f"work item not found: {item_id}")
        return [work_item]
    return (
        query.filter(WorkItem.state == WorkItemState.ARTIFACT_SYNC)
        .order_by(WorkItem.updated_at.asc(), WorkItem.created_at.asc())
        .all()
    )


def process_completed_items(session: Session, request: CompletionProcessRequest) -> list[CompletionProcessResult]:
    results: list[CompletionProcessResult] = []
    for work_item in _iter_target_items(session, item_id=request.item_id):
        if work_item.state != WorkItemState.ARTIFACT_SYNC:
            if request.item_id:
                raise CompletionProcessingError(
                    f"work item {work_item.item_id} is not ready for completion processing: state={work_item.state.value}"
                )
            continue

        latest_run = _latest_run_for_item(work_item)
        _materialize_expected_output_artifacts(repo_root=request.repo_root, run=latest_run)
        if work_item.task_type == "l1_sweep":
            consume_result = consume_l1_result(
                session,
                Layer1ConsumeRequest(
                    repo_root=request.repo_root,
                    item_id=work_item.item_id,
                ),
            )
            target_path = consume_result.target_path
        elif work_item.task_type == "l2_campaign":
            consume_result = consume_l2_result(
                session,
                Layer2ConsumeRequest(
                    repo_root=request.repo_root,
                    item_id=work_item.item_id,
                ),
            )
            target_path = consume_result.target_path
        else:
            raise CompletionProcessingError(f"unsupported task_type for completion processing: {work_item.task_type}")

        submitted = False
        pr_url: str | None = None
        submission_error: str | None = None
        if request.submit:
            if not request.repo:
                raise CompletionProcessingError("repo is required when submit=True")
            try:
                operate_result = operate_submission(
                    session,
                    OperatorSubmissionRequest(
                        repo_root=request.repo_root,
                        repo=request.repo,
                        item_id=work_item.item_id,
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
                        force=request.force,
                    ),
                )
            except Exception as exc:
                submission_error = str(exc)
                _record_submission_failure(session, run=latest_run, error=submission_error)
            else:
                submitted = True
                pr_url = operate_result.pr_url

        session.refresh(work_item)
        results.append(
            CompletionProcessResult(
                item_id=work_item.item_id,
                run_key=latest_run.run_key,
                task_type=work_item.task_type,
                consumed=True,
                submitted=submitted,
                work_item_state=work_item.state.value,
                target_path=target_path,
                pr_url=pr_url,
                submission_error=submission_error,
            )
        )

    return results
