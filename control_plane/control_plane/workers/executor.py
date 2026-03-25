"""Deterministic internal worker execution loop."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import shutil
from typing import Any

from sqlalchemy.orm import Session, sessionmaker

from control_plane.ids import make_id
from control_plane.models.runs import Run
from control_plane.models.work_items import WorkItem
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

    requeue = retryable and attempt < max_retry_attempts
    return {
        "category": category,
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


def _log_dir(config: WorkerConfig, item_id: str, run_key: str) -> str:
    root = Path(config.log_root or (Path(config.repo_root) / "control_plane" / "logs")).resolve()
    path = root / item_id / run_key
    path.mkdir(parents=True, exist_ok=True)
    return str(path)


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
            )
        except NoEligibleWorkItem:
            return WorkerLoopResult(status="no_work", summary="no eligible work item")

    with session_factory() as session:
        work_item = _load_work_item(session, acquired.work_item_id)
        attempt = _next_attempt(session, work_item.id)
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
        command_results = run_command_manifest(
            command_manifest=work_item.command_manifest or [],
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
        expected_outputs=work_item.expected_outputs or [],
    ) + collect_linked_results_artifacts(
        repo_root=checkout_info.work_dir,
        expected_outputs=work_item.expected_outputs or [],
    ) + collect_log_artifacts(
        repo_root=checkout_info.work_dir,
        command_results=command_results,
    )
    queue_result = build_queue_result_payload(
        repo_root=checkout_info.work_dir,
        expected_outputs=work_item.expected_outputs or [],
        command_results=command_results,
        success=success,
    )
    result_payload = {
        "queue_result": {
            "status": queue_result.status,
            "metrics_rows": queue_result.metrics_rows,
            "notes": queue_result.notes,
        },
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
            expected_outputs=work_item.expected_outputs or [],
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
