"""Deterministic internal worker execution loop."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import shutil
from typing import Any

from sqlalchemy.orm import Session, sessionmaker

from control_plane.ids import make_id
from control_plane.models.enums import RunStatus, WorkItemState
from control_plane.models.runs import Run
from control_plane.models.work_items import WorkItem
from control_plane.services.completion_service import (
    CompletionProcessRequest,
    CompletionProcessingError,
    process_completed_items,
)
from control_plane.services.completion_retry_service import claim_submission_retry
from control_plane.services.lease_service import acquire_next_lease
from control_plane.services.run_service import (
    append_run_event,
    complete_run,
    is_run_cancel_requested,
    start_run,
)
from control_plane.services.scheduler import NoEligibleWorkItem
from control_plane.workers.artifact_stage import (
    build_queue_result_payload,
    collect_expected_output_artifacts,
    collect_linked_results_artifacts,
    collect_log_artifacts,
)
from control_plane.workers.checkout import CheckoutError, cleanup_checkout, prepare_checkout
from control_plane.workers.command_runner import run_command_manifest, summarize_command_results
from control_plane.workers.heartbeat import LeaseHeartbeatPump


@dataclass(frozen=True)
class WorkerConfig:
    repo_root: str
    machine_key: str
    hostname: str | None = None
    executor_kind: str = "local_process"
    machine_role: str = "evaluator"
    slot_capacity: int = 1
    capabilities: dict[str, Any] | None = None
    capability_filter: dict[str, Any] | None = None
    lease_seconds: int = 1800
    heartbeat_seconds: int = 30
    command_timeout_seconds: int | None = None
    command_stall_timeout_seconds: int | None = None
    command_progress_seconds: int = 60
    max_retry_attempts: int = 2
    enforce_source_commit: bool = True
    log_root: str | None = None
    auto_process_completions: bool = False
    completion_submit: bool = False
    completion_repo: str | None = None
    completion_evaluator_id: str = "control_plane"
    completion_session_id: str | None = None
    completion_host: str | None = None
    completion_executor: str = "@control_plane"
    completion_branch_name: str | None = None
    completion_snapshot_target_path: str | None = None
    completion_package_target_path: str | None = None
    completion_worktree_root: str | None = None
    completion_commit_message: str | None = None
    completion_pr_base: str = "master"
    completion_force: bool = False


@dataclass(frozen=True)
class WorkerLoopResult:
    status: str
    item_id: str | None = None
    run_key: str | None = None
    command_count: int = 0
    summary: str | None = None


def _classify_failure(
    *,
    command_results,
    worker_error: str | None,
    checkout_error: str | None,
    attempt: int,
    max_retry_attempts: int,
) -> dict[str, Any]:
    if checkout_error is not None:
        category = "checkout_error"
        retryable = True
        failed_command = None
        detail = checkout_error
    elif worker_error is not None:
        category = "worker_error"
        retryable = True
        failed_command = None
        detail = worker_error
    else:
        failed = next((result for result in command_results if result.returncode != 0), None)
        if failed is None:
            return {
                "category": "none",
                "retryable": False,
                "requeue": False,
                "attempt": attempt,
                "max_retry_attempts": max_retry_attempts,
                "failed_command_name": None,
                "detail": None,
            }
        failed_command = failed.name
        detail = "timed out" if failed.timed_out else f"exit_code={failed.returncode}"
        if failed.timed_out:
            category = "command_timeout"
            retryable = False
        elif failed.stalled:
            category = "command_stall"
            retryable = False
        elif failed.canceled:
            category = "command_canceled"
            retryable = False
        elif failed.name in {"validate", "validate_runs", "validate_campaign"}:
            category = "validation_error"
            retryable = False
        else:
            category = "command_failure"
            retryable = False

    stage = "checkout" if checkout_error is not None else ("worker" if worker_error is not None else (failed_command or "execution"))
    signature = detail if isinstance(detail, str) else None
    requeue = retryable and attempt < max_retry_attempts
    return {
        "category": category,
        "stage": stage,
        "signature": signature,
        "retryable": retryable,
        "requeue": requeue,
        "attempt": attempt,
        "max_retry_attempts": max_retry_attempts,
        "failed_command_name": failed_command,
        "detail": detail,
    }


def _load_work_item(session: Session, work_item_id: str) -> WorkItem:
    work_item = session.query(WorkItem).filter(WorkItem.id == work_item_id).one_or_none()
    if work_item is None:
        raise RuntimeError(f"work item not found: {work_item_id}")
    return work_item


def _next_attempt(session: Session, work_item_id: str) -> int:
    latest = (
        session.query(Run)
        .filter(Run.work_item_id == work_item_id)
        .order_by(Run.attempt.desc())
        .first()
    )
    return 1 if latest is None else int(latest.attempt) + 1


def _trial_policy(work_item: WorkItem) -> dict[str, int]:
    raw = dict(getattr(work_item, "trial_policy_json", {}) or {})
    if str(work_item.task_type) != "l1_sweep":
        return {"trial_count": 1, "seed_start": 0, "stop_after_failures": 1}
    trial_count = max(int(raw.get("trial_count", 1) or 1), 1)
    seed_start = int(raw.get("seed_start", 0) or 0)
    stop_after_failures = raw.get("stop_after_failures", trial_count)
    stop_after_failures = max(1, min(int(stop_after_failures or trial_count), trial_count))
    return {
        "trial_count": trial_count,
        "seed_start": seed_start,
        "stop_after_failures": stop_after_failures,
    }


def _completed_trial_runs(session: Session, work_item_id: str) -> list[Run]:
    runs = (
        session.query(Run)
        .filter(Run.work_item_id == work_item_id)
        .order_by(Run.attempt.asc(), Run.created_at.asc())
        .all()
    )
    completed: list[Run] = []
    for run in runs:
        if run.status not in {RunStatus.SUCCEEDED, RunStatus.FAILED, RunStatus.CANCELED, RunStatus.TIMED_OUT}:
            continue
        payload = dict(run.result_payload or {}) if isinstance(run.result_payload, dict) else {}
        retry = bool((payload.get("retry_decision") or {}).get("requeue"))
        if retry:
            continue
        completed.append(run)
    return completed


def _next_trial_index(session: Session, work_item: WorkItem) -> int:
    return len(_completed_trial_runs(session, work_item.id)) + 1


def _trial_out_root(work_item: WorkItem, trial_index: int) -> str | None:
    policy = _trial_policy(work_item)
    if policy["trial_count"] <= 1:
        return None
    out_root = str((work_item.input_manifest or {}).get("out_root", "")).strip()
    if not out_root:
        return None
    return f"{out_root}/trials/trial_{trial_index:03d}"


def _active_expected_outputs(work_item: WorkItem, trial_index: int) -> list[str]:
    expected_outputs = [str(path) for path in (work_item.expected_outputs or [])]
    trial_out_root = _trial_out_root(work_item, trial_index)
    out_root = str((work_item.input_manifest or {}).get("out_root", "")).strip()
    if not trial_out_root or not out_root:
        return expected_outputs
    prefix = f"{out_root}/"
    trial_prefix = f"{out_root}/trials/trial_"
    replacement = f"{trial_out_root}/"
    result: list[str] = []
    for rel_path in expected_outputs:
        if rel_path == "runs/index.csv":
            result.append(rel_path)
        elif rel_path.startswith(trial_prefix):
            result.append(rel_path)
        elif rel_path.startswith(prefix):
            result.append(rel_path.replace(prefix, replacement, 1))
        else:
            result.append(rel_path)
    return result


def _active_command_manifest(work_item: WorkItem, trial_index: int) -> list[dict[str, str]]:
    commands = [dict(row) for row in (work_item.command_manifest or [])]
    trial_out_root = _trial_out_root(work_item, trial_index)
    out_root = str((work_item.input_manifest or {}).get("out_root", "")).strip()
    policy = _trial_policy(work_item)
    flow_seed = None
    if str(work_item.task_type) == "l1_sweep" and policy["trial_count"] > 1:
        flow_seed = policy["seed_start"] + trial_index - 1
    token = f"--out_root {out_root}"
    replacement = f"--out_root {trial_out_root}"
    for command in commands:
        run_text = str(command.get("run", ""))
        if trial_out_root and out_root and token in run_text:
            command["run"] = run_text.replace(token, replacement)
            run_text = str(command.get("run", ""))
        if flow_seed is not None and "python3 scripts/run_sweep.py" in run_text and "FLOW_RANDOM_SEED=" not in run_text:
            command["run"] = run_text.replace(
                "python3 scripts/run_sweep.py",
                f"FLOW_RANDOM_SEED={flow_seed} python3 scripts/run_sweep.py",
                1,
            )
    return commands


def _should_continue_trials(session: Session, work_item: WorkItem) -> bool:
    policy = _trial_policy(work_item)
    completed = _completed_trial_runs(session, work_item.id)
    completed_count = len(completed)
    success_count = sum(1 for run in completed if run.status == RunStatus.SUCCEEDED)
    failure_count = completed_count - success_count
    if completed_count >= policy["trial_count"]:
        return False
    if success_count == 0 and failure_count >= policy["stop_after_failures"]:
        return False
    return True


def _promote_post_run_state(*, session_factory: sessionmaker, work_item_id: str, run_key: str) -> tuple[bool, bool]:
    with session_factory() as session:
        work_item = _load_work_item(session, work_item_id)
        completed = _completed_trial_runs(session, work_item.id)
        success_count = sum(1 for row in completed if row.status == RunStatus.SUCCEEDED)
        continue_trials = _should_continue_trials(session, work_item)
        if continue_trials:
            work_item.state = WorkItemState.READY if work_item.assigned_machine_key else WorkItemState.DISPATCH_PENDING
            next_trial_index = len(completed) + 1
            next_seed = _trial_policy(work_item)["seed_start"] + next_trial_index - 1
            session.commit()
            append_run_event(
                session,
                run_key=run_key,
                event_type="trial_scheduled",
                event_payload={"next_trial_index": next_trial_index, "next_seed": next_seed},
            )
            return True, False
        if success_count > 0:
            if work_item.state != WorkItemState.ARTIFACT_SYNC:
                work_item.state = WorkItemState.ARTIFACT_SYNC
                session.commit()
            append_run_event(
                session,
                run_key=run_key,
                event_type="trial_set_completed",
                event_payload={"success_count": success_count, "completed_trials": len(completed)},
            )
            return False, True
        return False, False


def _log_dir(config: WorkerConfig, item_id: str, run_key: str) -> str:
    root = Path(config.log_root or (Path(config.repo_root) / "control_plane" / "logs")).resolve()
    path = root / item_id / run_key
    path.mkdir(parents=True, exist_ok=True)
    return str(path)


SUPPORTED_IMMEDIATE_COMPLETION_TASK_TYPES = {"l1_sweep", "l2_campaign"}


def _build_completion_request(
    *,
    config: WorkerConfig,
    item_id: str,
    repo_root: str | None = None,
    force: bool | None = None,
) -> CompletionProcessRequest:
    return CompletionProcessRequest(
        repo_root=repo_root or config.repo_root,
        repo=config.completion_repo,
        item_id=item_id,
        submit=config.completion_submit and bool(config.completion_repo),
        evaluator_id=config.completion_evaluator_id,
        session_id=config.completion_session_id,
        host=config.completion_host or config.hostname,
        executor=config.completion_executor,
        branch_name=config.completion_branch_name,
        snapshot_target_path=config.completion_snapshot_target_path,
        package_target_path=config.completion_package_target_path,
        worktree_root=config.completion_worktree_root,
        commit_message=config.completion_commit_message,
        pr_base=config.completion_pr_base,
        force=config.completion_force if force is None else force,
    )


def _sync_expected_outputs_to_repo(*, checkout_root: str, repo_root: str, expected_outputs: list[str]) -> None:
    source_root = Path(checkout_root).resolve()
    target_root = Path(repo_root).resolve()
    if source_root == target_root:
        return

    rel_paths: set[str] = {str(path) for path in (expected_outputs or []) if str(path).strip()}
    rel_paths.update(
        artifact.path
        for artifact in collect_linked_results_artifacts(
            repo_root=str(source_root),
            expected_outputs=expected_outputs or [],
        )
        if str(artifact.path).strip()
    )

    for rel_path in sorted(rel_paths):
        source_path = (source_root / rel_path).resolve()
        if not source_path.exists() or not source_path.is_file():
            continue
        target_path = (target_root / rel_path).resolve()
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target_path)


def _sync_completion_artifacts_to_repo(
    *,
    checkout_root: str,
    repo_root: str,
    item_id: str,
    target_path: str | None,
) -> None:
    source_root = Path(checkout_root).resolve()
    target_root = Path(repo_root).resolve()
    if source_root == target_root:
        return

    def _copy_file(rel_path: str) -> None:
        source_path = (source_root / rel_path).resolve()
        if not source_path.exists() or not source_path.is_file():
            return
        target_path_obj = (target_root / rel_path).resolve()
        if source_path == target_path_obj:
            return
        target_path_obj.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target_path_obj)

    def _copy_tree(rel_dir: str) -> None:
        source_dir = (source_root / rel_dir).resolve()
        if not source_dir.exists() or not source_dir.is_dir():
            return
        for source_path in sorted(source_dir.rglob('*')):
            if not source_path.is_file():
                continue
            rel_path = str(source_path.relative_to(source_root))
            _copy_file(rel_path)

    if target_path:
        _copy_file(str(target_path))
    _copy_tree(f'control_plane/shadow_exports/review/{item_id}')
    _copy_tree(f'control_plane/shadow_exports/frozen_review/{item_id}')
    _copy_tree(f'control_plane/shadow_exports/l1_trials/{item_id}')


def _record_completion_result(
    *,
    session_factory: sessionmaker,
    run_key: str,
    event_type: str,
    payload: dict[str, Any],
) -> None:
    with session_factory() as session:
        append_run_event(
            session,
            run_key=run_key,
            event_type=event_type,
            event_payload=payload,
        )


def _process_requested_submission_retry(
    session_factory: sessionmaker,
    *,
    config: WorkerConfig,
) -> WorkerLoopResult | None:
    if not config.auto_process_completions or not config.completion_repo:
        return None
    with session_factory() as session:
        claim = claim_submission_retry(session, machine_key=config.machine_key)
    if claim is None:
        return None
    request = _build_completion_request(config=config, item_id=claim.item_id, force=claim.force or config.completion_force)
    try:
        with session_factory() as session:
            results = process_completed_items(session, request)
    except CompletionProcessingError as exc:
        _record_completion_result(
            session_factory=session_factory,
            run_key=claim.run_key,
            event_type="submission_retry_failed",
            payload={"error": str(exc), "item_id": claim.item_id, "request_id": claim.request_id},
        )
        return WorkerLoopResult(status="retry_failed", item_id=claim.item_id, run_key=claim.run_key, summary=str(exc))
    except Exception as exc:
        _record_completion_result(
            session_factory=session_factory,
            run_key=claim.run_key,
            event_type="submission_retry_failed",
            payload={"error": str(exc), "item_id": claim.item_id, "request_id": claim.request_id},
        )
        return WorkerLoopResult(status="retry_failed", item_id=claim.item_id, run_key=claim.run_key, summary=str(exc))

    if not results:
        _record_completion_result(
            session_factory=session_factory,
            run_key=claim.run_key,
            event_type="submission_retry_skipped",
            payload={"item_id": claim.item_id, "request_id": claim.request_id, "reason": "no_completion_results"},
        )
        return WorkerLoopResult(status="retry_skipped", item_id=claim.item_id, run_key=claim.run_key, summary="no completion results")

    result = results[0]
    _record_completion_result(
        session_factory=session_factory,
        run_key=claim.run_key,
        event_type="submission_retry_processed",
        payload={
            "item_id": result.item_id,
            "request_id": claim.request_id,
            "task_type": result.task_type,
            "consumed": result.consumed,
            "submitted": result.submitted,
            "work_item_state": result.work_item_state,
            "target_path": result.target_path,
            "pr_url": result.pr_url,
            "submission_error": result.submission_error,
        },
    )
    summary = result.pr_url or result.submission_error or result.work_item_state
    return WorkerLoopResult(status="resumed", item_id=result.item_id, run_key=result.run_key, summary=summary)


def _process_completed_work_item(
    session_factory: sessionmaker,
    *,
    config: WorkerConfig,
    work_item: WorkItem,
    run_key: str,
    completion_repo_root: str,
) -> None:
    if not config.auto_process_completions:
        return
    if work_item.task_type not in SUPPORTED_IMMEDIATE_COMPLETION_TASK_TYPES:
        return

    request = _build_completion_request(
        config=config,
        item_id=work_item.item_id,
        repo_root=completion_repo_root,
    )
    try:
        with session_factory() as session:
            results = process_completed_items(session, request)
    except CompletionProcessingError as exc:
        error = str(exc)
        event_type = "completion_processing_failed"
        if "not ready for completion processing" in error:
            event_type = "completion_processing_skipped"
        _record_completion_result(
            session_factory=session_factory,
            run_key=run_key,
            event_type=event_type,
            payload={"error": error, "item_id": work_item.item_id},
        )
        return
    except Exception as exc:
        _record_completion_result(
            session_factory=session_factory,
            run_key=run_key,
            event_type="completion_processing_failed",
            payload={"error": str(exc), "item_id": work_item.item_id},
        )
        return

    if not results:
        _record_completion_result(
            session_factory=session_factory,
            run_key=run_key,
            event_type="completion_processing_skipped",
            payload={"item_id": work_item.item_id, "reason": "no_completion_results"},
        )
        return

    result = results[0]
    try:
        _sync_completion_artifacts_to_repo(
            checkout_root=completion_repo_root,
            repo_root=config.repo_root,
            item_id=work_item.item_id,
            target_path=result.target_path,
        )
    except Exception as exc:
        _record_completion_result(
            session_factory=session_factory,
            run_key=run_key,
            event_type="completion_processing_failed",
            payload={"error": str(exc), "item_id": work_item.item_id, "phase": "artifact_sync"},
        )
        return
    _record_completion_result(
        session_factory=session_factory,
        run_key=run_key,
        event_type="completion_processed",
        payload={
            "item_id": result.item_id,
            "task_type": result.task_type,
            "consumed": result.consumed,
            "submitted": result.submitted,
            "work_item_state": result.work_item_state,
            "target_path": result.target_path,
            "pr_url": result.pr_url,
            "submission_error": result.submission_error,
        },
    )


def _materialize_generated_inputs(*, checkout_root: str, work_item: WorkItem) -> None:
    generated_campaign = ((work_item.input_manifest or {}).get("generated_campaign") or None)
    if not generated_campaign:
        return
    base_campaign_path = str(generated_campaign.get("base_campaign_path", "")).strip()
    target_path = str(generated_campaign.get("path", "")).strip()
    outputs = dict(generated_campaign.get("outputs") or {})
    if not base_campaign_path or not target_path:
        raise RuntimeError("generated_campaign requires base_campaign_path and path")
    repo_root = Path(checkout_root).resolve()
    base_file = (repo_root / base_campaign_path).resolve()
    target_file = (repo_root / target_path).resolve()
    campaign = json.loads(base_file.read_text(encoding="utf-8"))
    if not outputs:
        raise RuntimeError("generated_campaign.outputs is required")
    campaign_dir = str(outputs.get("campaign_dir", "")).strip()
    clean_outputs = bool(generated_campaign.get("clean_outputs", False)) or str(work_item.task_type) == "l2_campaign"
    if clean_outputs and campaign_dir:
        output_root = (repo_root / campaign_dir).resolve()
        if output_root.exists():
            if output_root.is_dir():
                shutil.rmtree(output_root)
            else:
                output_root.unlink()
    campaign["outputs"] = outputs
    target_file.parent.mkdir(parents=True, exist_ok=True)
    target_file.write_text(json.dumps(campaign, indent=2) + "\n", encoding="utf-8")


def execute_one_work_item(session_factory: sessionmaker, *, config: WorkerConfig) -> WorkerLoopResult:
    retry_result = _process_requested_submission_retry(session_factory, config=config)
    if retry_result is not None:
        return retry_result

    with session_factory() as session:
        try:
            acquired = acquire_next_lease(
                session,
                machine_key=config.machine_key,
                hostname=config.hostname,
                executor_kind=config.executor_kind,
                capabilities=config.capabilities,
                capability_filter=config.capability_filter,
                lease_seconds=config.lease_seconds,
                machine_role=config.machine_role,
                slot_capacity=config.slot_capacity,
            )
        except NoEligibleWorkItem:
            return WorkerLoopResult(status="no_work", summary="no eligible work item")

    with session_factory() as session:
        work_item = _load_work_item(session, acquired.work_item_id)
        attempt = _next_attempt(session, work_item.id)
        trial_index = _next_trial_index(session, work_item)
        seed = _trial_policy(work_item)["seed_start"] + trial_index - 1
        run_key = f"{work_item.item_id}_{make_id('run')}"

    checkout_error: str | None = None
    checkout_info = None
    try:
        checkout_info = prepare_checkout(
            repo_root=config.repo_root,
            source_commit=work_item.source_commit,
            enforce_source_commit=config.enforce_source_commit,
            required_submodules=((work_item.input_manifest or {}).get("required_submodules") or None),
        )
    except CheckoutError as exc:
        checkout_error = str(exc)

    with session_factory() as session:
        started = start_run(
            session,
            lease_token=acquired.lease_token,
            run_key=run_key,
            attempt=attempt,
            executor_type="internal_worker",
            checkout_commit=checkout_info.head_sha if checkout_info is not None else None,
            trial_index=trial_index,
            seed=seed,
            trial_group_key=work_item.item_id,
        )

    if checkout_error is not None:
        failure = _classify_failure(
            command_results=[],
            worker_error=None,
            checkout_error=checkout_error,
            attempt=attempt,
            max_retry_attempts=config.max_retry_attempts,
        )
        with session_factory() as session:
            append_run_event(
                session,
                run_key=run_key,
                event_type="checkout_failed",
                event_payload={"error": checkout_error},
            )
            if failure["requeue"]:
                append_run_event(
                    session,
                    run_key=run_key,
                    event_type="run_requeued",
                    event_payload={"failure_classification": failure},
                )
            complete_run(
                session,
                run_key=run_key,
                status="failed",
                result_summary=f"checkout failed: {checkout_error}",
                result_payload={
                    "checkout_error": checkout_error,
                    "failure_classification": failure,
                    "retry_decision": {
                        "requeue": failure["requeue"],
                        "attempt": failure["attempt"],
                        "max_retry_attempts": failure["max_retry_attempts"],
                    },
                },
                artifacts=[],
            )
        return WorkerLoopResult(
            status="failed",
            item_id=work_item.item_id,
            run_key=run_key,
            summary=f"checkout failed: {checkout_error}",
        )

    with session_factory() as session:
        append_run_event(
            session,
            run_key=run_key,
            event_type="checkout_prepared",
            event_payload={
                "repo_root": checkout_info.repo_root,
                "head_sha": checkout_info.head_sha,
                "git_dirty": checkout_info.git_dirty,
                "source_commit": checkout_info.source_commit,
                "source_commit_matches": checkout_info.source_commit_matches,
                "source_commit_relation": checkout_info.source_commit_relation,
                "materialized_submodules": list(checkout_info.materialized_submodules),
            },
        )

    _materialize_generated_inputs(
        checkout_root=checkout_info.work_dir,
        work_item=work_item,
    )

    heartbeat = LeaseHeartbeatPump(
        session_factory=session_factory,
        lease_token=acquired.lease_token,
        heartbeat_seconds=config.heartbeat_seconds,
        extend_seconds=config.lease_seconds,
    )
    heartbeat.start()
    heartbeat.update_progress({"phase": "starting", "item_id": work_item.item_id})

    log_dir = _log_dir(config, work_item.item_id, run_key)
    command_results = []
    worker_error: str | None = None
    try:
        active_command_manifest = _active_command_manifest(work_item, trial_index)
        active_expected_outputs = _active_expected_outputs(work_item, trial_index)
        command_results = run_command_manifest(
            command_manifest=active_command_manifest,
            work_dir=checkout_info.work_dir,
            log_dir=log_dir,
            timeout_seconds=config.command_timeout_seconds,
            stall_timeout_seconds=config.command_stall_timeout_seconds,
            progress_interval_seconds=config.command_progress_seconds,
            cancel_requested=lambda: _is_cancel_requested(
                session_factory=session_factory,
                run_key=run_key,
            ),
            on_command_started=lambda payload: _record_command_started(
                session_factory=session_factory,
                run_key=run_key,
                item_id=work_item.item_id,
                payload=payload,
                heartbeat=heartbeat,
            ),
            on_command_progress=lambda payload: _record_command_progress(
                session_factory=session_factory,
                run_key=run_key,
                item_id=work_item.item_id,
                payload=payload,
                heartbeat=heartbeat,
            ),
            on_command_finished=lambda result: _record_command_result(
                session_factory=session_factory,
                run_key=run_key,
                item_id=work_item.item_id,
                result=result,
                heartbeat=heartbeat,
            ),
        )
    except Exception as exc:
        worker_error = str(exc)
    finally:
        heartbeat_error = heartbeat.stop()

    success = worker_error is None and bool(command_results) and all(result.returncode == 0 for result in command_results)
    if not command_results and not work_item.command_manifest:
        success = True

    artifacts = collect_expected_output_artifacts(
        repo_root=checkout_info.work_dir,
        expected_outputs=active_expected_outputs,
    ) + collect_linked_results_artifacts(
        repo_root=checkout_info.work_dir,
        expected_outputs=active_expected_outputs,
    ) + collect_log_artifacts(
        repo_root=checkout_info.work_dir,
        command_results=command_results,
    )
    queue_result = build_queue_result_payload(
        repo_root=checkout_info.work_dir,
        expected_outputs=active_expected_outputs,
        command_results=command_results,
        success=success,
    )
    result_payload = {
        "queue_result": {
            "status": queue_result.status,
            "metrics_rows": queue_result.metrics_rows,
            "notes": queue_result.notes,
        },
        "trial": {"trial_index": trial_index, "seed": seed, "trial_group_key": work_item.item_id},
        "active_expected_outputs": active_expected_outputs,
        "checkout": {
            "repo_root": checkout_info.repo_root,
            "head_sha": checkout_info.head_sha,
            "git_dirty": checkout_info.git_dirty,
            "source_commit": checkout_info.source_commit,
            "source_commit_matches": checkout_info.source_commit_matches,
            "source_commit_relation": checkout_info.source_commit_relation,
            "materialized_submodules": list(checkout_info.materialized_submodules),
        },
        "commands": [
            {
                "name": result.name,
                "command": result.command,
                "returncode": result.returncode,
                "duration_seconds": result.duration_seconds,
                "stdout_log": result.stdout_log,
                "stderr_log": result.stderr_log,
                "timed_out": result.timed_out,
                "stalled": result.stalled,
                "canceled": result.canceled,
            }
            for result in command_results
        ],
    }
    if heartbeat_error is not None:
        result_payload["heartbeat_error"] = heartbeat_error
        if worker_error is None:
            worker_error = f"heartbeat_error={heartbeat_error}"
    if worker_error is not None:
        result_payload["worker_error"] = worker_error
    failure = _classify_failure(
        command_results=command_results,
        worker_error=worker_error,
        checkout_error=None,
        attempt=attempt,
        max_retry_attempts=config.max_retry_attempts,
    )
    result_payload["failure_classification"] = failure
    result_payload["retry_decision"] = {
        "requeue": failure["requeue"],
        "attempt": failure["attempt"],
        "max_retry_attempts": failure["max_retry_attempts"],
    }
    if not success:
        queue_result = build_queue_result_payload(
            repo_root=checkout_info.work_dir,
            expected_outputs=active_expected_outputs,
            command_results=command_results,
            success=False,
        )
        notes = list(queue_result.notes)
        notes.append(f"failure_category={failure['category']}")
        if failure["failed_command_name"]:
            notes.append(f"failed_command={failure['failed_command_name']}")
        if worker_error is not None:
            notes.append(f"worker_error={worker_error}")
        if failure["requeue"]:
            notes.append(
                f"retry_scheduled=attempt_{failure['attempt'] + 1}_of_{failure['max_retry_attempts']}"
            )
        result_payload["queue_result"] = {
            "status": queue_result.status,
            "metrics_rows": queue_result.metrics_rows,
            "notes": notes,
        }

    with session_factory() as session:
        if failure["requeue"]:
            append_run_event(
                session,
                run_key=run_key,
                event_type="run_requeued",
                event_payload={"failure_classification": failure},
            )
        completed = complete_run(
            session,
            run_key=run_key,
            status=_terminal_run_status(success=success, failure_category=failure["category"]),
            result_summary=worker_error or summarize_command_results(command_results),
            result_payload=result_payload,
            artifacts=[
                {
                    "kind": artifact.kind,
                    "storage_mode": artifact.storage_mode,
                    "path": artifact.path,
                    "sha256": artifact.sha256,
                    "metadata": artifact.metadata,
                }
                for artifact in artifacts
            ],
        )

    if completed.status == "succeeded":
        _sync_expected_outputs_to_repo(
            checkout_root=checkout_info.work_dir,
            repo_root=config.repo_root,
            expected_outputs=active_expected_outputs,
        )

    continue_trials, ready_for_completion = _promote_post_run_state(
        session_factory=session_factory,
        work_item_id=work_item.id,
        run_key=run_key,
    )
    if ready_for_completion:
        if str(work_item.task_type) == "l1_sweep" and _trial_policy(work_item)["trial_count"] > 1:
            _sync_expected_outputs_to_repo(
                checkout_root=config.repo_root,
                repo_root=checkout_info.work_dir,
                expected_outputs=[str(path) for path in (work_item.expected_outputs or [])],
            )
        _process_completed_work_item(
            session_factory,
            config=config,
            work_item=work_item,
            run_key=run_key,
            completion_repo_root=checkout_info.work_dir,
        )

    cleanup_checkout(checkout_info)

    return WorkerLoopResult(
        status=completed.status,
        item_id=work_item.item_id,
        run_key=run_key,
        command_count=len(command_results),
        summary=summarize_command_results(command_results),
    )


def _record_command_result(
    *,
    session_factory: sessionmaker,
    run_key: str,
    item_id: str,
    result,
    heartbeat: LeaseHeartbeatPump,
) -> None:
    heartbeat.update_progress(
        {
            "phase": "command_finished",
            "item_id": item_id,
            "command_name": result.name,
            "returncode": result.returncode,
        }
    )
    with session_factory() as session:
        append_run_event(
            session,
            run_key=run_key,
            event_type="command_finished",
            event_payload={
                "command_name": result.name,
                "command": result.command,
                "returncode": result.returncode,
                "duration_seconds": result.duration_seconds,
                "stdout_log": result.stdout_log,
                "stderr_log": result.stderr_log,
                "timed_out": result.timed_out,
                "stalled": result.stalled,
                "canceled": result.canceled,
            },
        )


def _record_command_started(
    *,
    session_factory: sessionmaker,
    run_key: str,
    item_id: str,
    payload: dict[str, Any],
    heartbeat: LeaseHeartbeatPump,
) -> None:
    progress = {
        "phase": "command_running",
        "item_id": item_id,
        "command_name": payload["command_name"],
        "stdout_log": payload["stdout_log"],
        "stderr_log": payload["stderr_log"],
    }
    heartbeat.update_progress(progress)
    with session_factory() as session:
        append_run_event(
            session,
            run_key=run_key,
            event_type="command_started",
            event_payload=payload,
        )


def _record_command_progress(
    *,
    session_factory: sessionmaker,
    run_key: str,
    item_id: str,
    payload: dict[str, Any],
    heartbeat: LeaseHeartbeatPump,
) -> None:
    progress = {
        "phase": "command_running",
        "item_id": item_id,
        **payload,
    }
    heartbeat.update_progress(progress)
    with session_factory() as session:
        append_run_event(
            session,
            run_key=run_key,
            event_type="command_progress",
            event_payload=progress,
        )


def _is_cancel_requested(*, session_factory: sessionmaker, run_key: str) -> bool:
    with session_factory() as session:
        return is_run_cancel_requested(session, run_key=run_key)


def _terminal_run_status(*, success: bool, failure_category: str) -> str:
    if success:
        return "succeeded"
    if failure_category == "command_canceled":
        return "canceled"
    if failure_category in {"command_timeout", "command_stall"}:
        return "timed_out"
    return "failed"


def execute_worker_loop(
    session_factory: sessionmaker,
    *,
    config: WorkerConfig,
    max_items: int = 1,
) -> list[WorkerLoopResult]:
    results: list[WorkerLoopResult] = []
    for _ in range(max_items):
        result = execute_one_work_item(session_factory, config=config)
        results.append(result)
        if result.status == "no_work":
            break
    return results
