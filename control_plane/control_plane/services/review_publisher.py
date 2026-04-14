"""Review package publishing for DB-native completed runs."""

from __future__ import annotations

import csv
from dataclasses import dataclass
import hashlib
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
from control_plane.services.reconciliation_service import ArtifactSyncRequest, sync_run_artifacts


class ReviewPublishError(RuntimeError):
    pass


@dataclass(frozen=True)
class ReviewPublishRequest:
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


@dataclass(frozen=True)
class ReviewPublishResult:
    item_id: str
    run_key: str
    snapshot_path: str
    package_path: str
    review_artifact_kind: str | None
    review_artifact_path: str | None
    branch_name: str
    pr_title: str


def _resolve_run(session: Session, request: ReviewPublishRequest) -> tuple[WorkItem, Run]:
    if request.run_key:
        run = session.query(Run).filter(Run.run_key == request.run_key).one_or_none()
        if run is None:
            raise ReviewPublishError(f"run not found: {request.run_key}")
        return run.work_item, run
    if not request.item_id:
        raise ReviewPublishError("item_id or run_key is required")
    work_item = session.query(WorkItem).filter(WorkItem.item_id == request.item_id).one_or_none()
    if work_item is None:
        raise ReviewPublishError(f"work item not found: {request.item_id}")
    if not work_item.runs:
        raise ReviewPublishError(f"work item has no runs: {request.item_id}")
    run = sorted(work_item.runs, key=lambda row: (row.attempt, row.created_at or utcnow()))[-1]
    return work_item, run


def _default_snapshot_path(*, item_id: str) -> str:
    return f"control_plane/shadow_exports/review/{item_id}/evaluated.json"


def _default_package_path(*, item_id: str) -> str:
    return f"control_plane/shadow_exports/review/{item_id}/review_package.json"


def _review_artifact_kind(task_type: str) -> str | None:
    if task_type == "l1_sweep":
        return "promotion_proposal"
    if task_type == "l2_campaign":
        return "decision_proposal"
    return None


def _find_artifact(session: Session, *, run_id: str, kind: str | None) -> Artifact | None:
    if not kind:
        return None
    return (
        session.query(Artifact)
        .filter(Artifact.run_id == run_id, Artifact.kind == kind)
        .order_by(Artifact.created_at.desc())
        .first()
    )


def _resolve_rel_path(path_text: str, repo_root: Path) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return repo_root / path


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _repo_head(repo_root: Path) -> str | None:
    completed = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return None
    value = completed.stdout.strip()
    return value or None


def _pr_title(work_item: WorkItem) -> str:
    payload = dict(work_item.task_request.request_payload or {})
    handoff = payload.get("handoff")
    if isinstance(handoff, dict):
        title = str(handoff.get("pr_title", "")).strip()
        if title:
            return title
    return f"review: {work_item.task_request.title}"


def _handoff_payload(work_item: WorkItem) -> dict[str, Any]:
    payload = dict(work_item.task_request.request_payload or {})
    handoff = payload.get("handoff")
    return dict(handoff) if isinstance(handoff, dict) else {}


def _developer_loop_payload(work_item: WorkItem) -> dict[str, Any]:
    payload = dict(work_item.task_request.request_payload or {})
    developer_loop = payload.get("developer_loop")
    if not isinstance(developer_loop, dict):
        return {}
    return {str(key): value for key, value in developer_loop.items() if str(value).strip()}


def _materialized_handoff(*, snapshot_payload: dict[str, Any], work_item: WorkItem) -> dict[str, Any]:
    handoff = snapshot_payload.get("handoff")
    if isinstance(handoff, dict):
        return dict(handoff)
    return _handoff_payload(work_item)


def _artifact_summary(*, repo_root: Path, artifact: Artifact | None) -> dict[str, Any] | None:
    if artifact is None:
        return None
    summary: dict[str, Any] = {
        "kind": artifact.kind,
        "path": artifact.path,
        "storage_mode": artifact.storage_mode.value,
        "sha256": artifact.sha256,
    }
    path = _resolve_rel_path(artifact.path, repo_root)
    if path.exists() and path.suffix.lower() == ".json":
        try:
            summary["payload"] = _load_json(path)
        except Exception:
            pass
    return summary


def _upsert_queue_snapshot_artifact(
    session: Session,
    *,
    run: Run,
    snapshot_path: str,
    payload: dict[str, Any],
) -> None:
    artifact = (
        session.query(Artifact)
        .filter(Artifact.run_id == run.id, Artifact.kind == "queue_snapshot")
        .one_or_none()
    )
    sha256 = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    if artifact is None:
        artifact = Artifact(
            run_id=run.id,
            kind="queue_snapshot",
            storage_mode=ArtifactStorageMode.REPO,
            path=snapshot_path,
            sha256=sha256,
            metadata_={},
        )
        session.add(artifact)
    else:
        artifact.storage_mode = ArtifactStorageMode.REPO
        artifact.path = snapshot_path
        artifact.sha256 = sha256


def _review_snapshot_override(
    *,
    repo_root: Path,
    snapshot_payload: dict[str, Any],
    review_payload: dict[str, Any],
) -> dict[str, Any]:
    if str(review_payload.get("objective", "")).strip() != "measure_seed_variance":
        return snapshot_payload
    source_refs = review_payload.get("source_refs")
    if not isinstance(source_refs, dict):
        return snapshot_payload
    trial_table_rel = str(source_refs.get("trial_table_csv", "")).strip()
    if not trial_table_rel:
        return snapshot_payload
    trial_table_path = _resolve_rel_path(trial_table_rel, repo_root)
    if not trial_table_path.exists():
        return snapshot_payload

    successful_rows: list[dict[str, Any]] = []
    with trial_table_path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if str(row.get("status", "")).strip() != "succeeded":
                continue
            metrics_csv = str(row.get("metrics_csv", "")).strip()
            if not metrics_csv:
                continue
            successful_rows.append(
                {
                    "metrics_csv": metrics_csv,
                    "platform": str(review_payload.get("platform", "")).strip(),
                    "status": "ok",
                    "trial_index": int(row["trial_index"]) if str(row.get("trial_index", "")).strip() else None,
                    "seed": int(row["seed"]) if str(row.get("seed", "")).strip() else None,
                    "critical_path_ns": float(row["critical_path_ns"]) if str(row.get("critical_path_ns", "")).strip() else None,
                    "die_area": float(row["die_area"]) if str(row.get("die_area", "")).strip() else None,
                    "total_power_mw": float(row["total_power_mw"]) if str(row.get("total_power_mw", "")).strip() else None,
                }
            )
    if not successful_rows:
        return snapshot_payload

    rewritten = json.loads(json.dumps(snapshot_payload))
    result = dict(rewritten.get("result") or {})
    final_attempt_rows = result.get("metrics_rows")
    if isinstance(final_attempt_rows, list):
        result["final_attempt_metrics_rows"] = final_attempt_rows
    result["metrics_rows"] = successful_rows
    result["metrics_rows_scope"] = "successful_seed_trials"
    trial_summary = review_payload.get("trial_summary")
    if isinstance(trial_summary, dict):
        success_count = trial_summary.get("success_count")
        completed_trials = trial_summary.get("completed_trials")
        failure_count = trial_summary.get("failure_count")
        result["summary"] = (
            f"{success_count}/{completed_trials} seed trials succeeded"
            + (f"; {failure_count} trial failures recorded" if failure_count not in (None, 0) else "")
        )
    result["trial_table_csv"] = trial_table_rel
    rewritten["result"] = result
    return rewritten


def _normalize_submission_error(raw: Any) -> str:
    text = " ".join(str(raw or "").split()).strip()
    if not text or text.lower() == "none":
        return ""
    if "gh pr create failed" in text and "gh auth login" in text:
        return "gh pr create failed: gh auth login required"
    if len(text) > 240:
        return text[:237] + "..."
    return text


def _submission_history_summary(*, session: Session, run: Run) -> dict[str, Any] | None:
    submission_events = (
        session.query(RunEvent)
        .filter(
            RunEvent.run_id == run.id,
            RunEvent.event_type.in_(
                [
                    "submission_failed",
                    "submission_retry_requested",
                    "submission_retry_started",
                    "submission_retry_processed",
                    "submission_retry_failed",
                    "submission_executed",
                ]
            ),
        )
        .order_by(RunEvent.event_time.asc(), RunEvent.id.asc())
        .all()
    )
    if not submission_events:
        return None

    history: dict[str, Any] = {
        "event_count": len(submission_events),
        "failure_count": 0,
        "retry_request_count": 0,
        "retry_processed_count": 0,
        "retry_failed_count": 0,
        "had_retry": False,
        "events": [],
    }
    last_failure: dict[str, Any] | None = None
    last_retry_request: dict[str, Any] | None = None
    final_submission: dict[str, Any] | None = None

    for event in submission_events:
        payload = dict(event.event_payload or {})
        event_summary = {
            "event_time": event.event_time.isoformat().replace("+00:00", "Z"),
            "event_type": event.event_type,
        }
        request_id = str(payload.get("request_id", "")).strip()
        if request_id:
            event_summary["request_id"] = request_id
        error = _normalize_submission_error(payload.get("error") or payload.get("submission_error"))
        if error:
            event_summary["error"] = error
        pr_url = str(payload.get("pr_url", "")).strip()
        if pr_url:
            event_summary["pr_url"] = pr_url
        submitted = payload.get("submitted")
        if isinstance(submitted, bool):
            event_summary["submitted"] = submitted
        history["events"].append(event_summary)

        if event.event_type in {"submission_failed", "submission_retry_failed"}:
            history["failure_count"] += 1
            last_failure = event_summary
        if event.event_type == "submission_retry_requested":
            history["retry_request_count"] += 1
            history["had_retry"] = True
            last_retry_request = event_summary
        if event.event_type == "submission_retry_processed":
            history["retry_processed_count"] += 1
            history["had_retry"] = True
            if bool(payload.get("submitted")):
                final_submission = event_summary
        if event.event_type == "submission_retry_failed":
            history["retry_failed_count"] += 1
            history["had_retry"] = True
        if event.event_type == "submission_executed":
            final_submission = event_summary

    if last_failure is not None:
        history["last_failure"] = last_failure
    if last_retry_request is not None:
        history["last_retry_request"] = last_retry_request
    if final_submission is not None:
        history["final_submission"] = final_submission
    return history


def _build_body_md(
    *,
    repo_root: Path,
    work_item: WorkItem,
    run: Run,
    snapshot_path: str,
    review_artifact: Artifact | None,
    snapshot_payload: dict[str, Any],
    handoff: dict[str, Any],
    developer_loop: dict[str, Any],
    submission_history: dict[str, Any] | None,
) -> str:
    result = dict(snapshot_payload.get("result") or {})
    review_payload: dict[str, Any] = {}
    if review_artifact is not None:
        try:
            review_payload = _load_json(_resolve_rel_path(review_artifact.path, repo_root))
        except Exception:
            review_payload = {}
    proposal_assessment = review_payload.get("proposal_assessment")
    evaluation_record = review_payload.get("evaluation_record")
    lines = [
        f"## Summary",
        f"- item_id: `{work_item.item_id}`",
        f"- run_key: `{run.run_key}`",
        f"- layer: `{work_item.layer.value}`",
        f"- task_type: `{work_item.task_type}`",
        f"- status: `{result.get('status', '')}`",
        f"- summary: `{result.get('summary', run.result_summary or '')}`",
        f"- queue_snapshot: `{snapshot_path}`",
    ]
    metrics_rows = result.get("metrics_rows")
    if isinstance(metrics_rows, list):
        lines.append(f"- metrics_rows_count: `{len(metrics_rows)}`")
    if review_artifact is not None:
        lines.append(f"- review_artifact: `{review_artifact.kind}` at `{review_artifact.path}`")
    proposal_id = str(developer_loop.get("proposal_id", "")).strip()
    proposal_path = str(developer_loop.get("proposal_path", "")).strip()
    if proposal_id or proposal_path:
        lines.extend(["", "## Developer Context"])
        if proposal_id:
            lines.append(f"- proposal_id: `{proposal_id}`")
        if proposal_path:
            lines.append(f"- proposal_path: `{proposal_path}`")
            lines.append(f"- reviewer_first_read: `{proposal_path}` plus `docs/developer_agent_review.md`")
    if isinstance(evaluation_record, dict):
        lines.extend(["", "## Evaluation Mode"])
        evaluation_mode = str(evaluation_record.get("evaluation_mode", "")).strip()
        if evaluation_mode:
            lines.append(f"- evaluation_mode: `{evaluation_mode}`")
        abstraction_layer = str(evaluation_record.get("abstraction_layer", "")).strip()
        if abstraction_layer:
            lines.append(f"- abstraction_layer: `{abstraction_layer}`")
        comparison_role = str(evaluation_record.get("comparison_role", "")).strip()
        if comparison_role:
            lines.append(f"- comparison_role: `{comparison_role}`")
        expected_direction = str(evaluation_record.get("expected_direction", "")).strip()
        if expected_direction:
            lines.append(f"- expected_direction: `{expected_direction}`")
        expected_reason = str(evaluation_record.get("expected_reason", "")).strip()
        if expected_reason:
            lines.append(f"- expected_reason: `{expected_reason}`")
        expectation_status = str(evaluation_record.get("expectation_status", "")).strip()
        if expectation_status:
            lines.append(f"- expectation_status: `{expectation_status}`")
        evaluation_summary = str(evaluation_record.get("summary", "")).strip()
        if evaluation_summary:
            lines.append(f"- evaluation_summary: `{evaluation_summary}`")
    if isinstance(proposal_assessment, dict):
        lines.extend(["", "## Focused Comparison"])
        primary_question = str(proposal_assessment.get("primary_question", "")).strip()
        if primary_question:
            lines.append(f"- primary_question: `{primary_question}`")
        comparison_role = str(proposal_assessment.get("comparison_role", "")).strip()
        if comparison_role:
            lines.append(f"- comparison_role: `{comparison_role}`")
        outcome = str(proposal_assessment.get("outcome", "")).strip()
        if outcome:
            lines.append(f"- proposal_outcome: `{outcome}`")
        summary_text = str(proposal_assessment.get("summary", "")).strip()
        if summary_text:
            lines.append(f"- comparison_summary: `{summary_text}`")
        baseline_ref = str(proposal_assessment.get("baseline_ref", "")).strip()
        if baseline_ref:
            lines.append(f"- baseline_ref: `{baseline_ref}`")
        baseline_item_id = str(proposal_assessment.get("baseline_item_id", "")).strip()
        if baseline_item_id:
            lines.append(f"- baseline_item_id: `{baseline_item_id}`")
        matched_rows = proposal_assessment.get("matched_rows")
        if isinstance(matched_rows, list):
            for row in _summary_rows_for_body(matched_rows):
                arch_id = str(row.get("arch_id", "")).strip()
                macro_mode = str(row.get("macro_mode", "")).strip()
                model_id = str(row.get("model_id", "")).strip()
                metrics = row.get("metrics")
                if not arch_id or not macro_mode or not isinstance(metrics, dict):
                    continue
                label = f"{arch_id}/{macro_mode}"
                if model_id:
                    label = f"{label}/{model_id}"
                latency = metrics.get("latency_ms_mean")
                energy = metrics.get("energy_mj_mean")
                if isinstance(latency, dict):
                    lines.append(
                        f"- latency_delta {label}: `{latency.get('baseline')}` -> `{latency.get('candidate')}` ms"
                    )
                if isinstance(energy, dict):
                    lines.append(
                        f"- energy_delta {label}: `{energy.get('baseline')}` -> `{energy.get('candidate')}` mJ"
                    )
    if isinstance(submission_history, dict):
        lines.extend(["", "## Submission Recovery"])
        if submission_history.get("had_retry"):
            lines.append("- resolver_retry_path: `true`")
        failure_count = submission_history.get("failure_count")
        if failure_count is not None:
            lines.append(f"- submission_failure_count: `{failure_count}`")
        retry_request_count = submission_history.get("retry_request_count")
        if retry_request_count is not None:
            lines.append(f"- retry_request_count: `{retry_request_count}`")
        last_failure = submission_history.get("last_failure")
        if isinstance(last_failure, dict):
            error = str(last_failure.get("error", "")).strip()
            if error:
                lines.append(f"- last_submission_failure: `{error}`")
        last_retry_request = submission_history.get("last_retry_request")
        if isinstance(last_retry_request, dict):
            request_id = str(last_retry_request.get("request_id", "")).strip()
            if request_id:
                lines.append(f"- retry_request_id: `{request_id}`")
        final_submission = submission_history.get("final_submission")
        if isinstance(final_submission, dict):
            submitted = final_submission.get("submitted")
            if isinstance(submitted, bool):
                lines.append(f"- final_submission_submitted: `{str(submitted).lower()}`")
            pr_url = str(final_submission.get("pr_url", "")).strip()
            if pr_url:
                lines.append(f"- final_submission_pr: `{pr_url}`")
    checklist = handoff.get("checklist")
    if isinstance(checklist, list) and checklist:
        lines.extend(["", "## Checklist"])
        for item in checklist:
            lines.append(f"- [ ] {item}")
    return "\n".join(lines) + "\n"


def _summary_rows_for_body(matched_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    model_rows = [row for row in matched_rows if str(row.get("scope", "")).strip() == "model"]
    if not model_rows:
        return matched_rows[:2]

    unique_model_ids = {
        str(row.get("model_id", "")).strip()
        for row in model_rows
        if str(row.get("model_id", "")).strip()
    }
    if 0 < len(unique_model_ids) <= 4:
        selected: list[dict[str, Any]] = []
        seen_model_ids: set[str] = set()
        preferred_rows = sorted(
            model_rows,
            key=lambda row: (
                0 if str(row.get("macro_mode", "")).strip() == "flat_nomacro" else 1,
                str(row.get("model_id", "")).strip(),
                str(row.get("arch_id", "")).strip(),
            ),
        )
        for row in preferred_rows:
            model_id = str(row.get("model_id", "")).strip()
            if not model_id or model_id in seen_model_ids:
                continue
            seen_model_ids.add(model_id)
            selected.append(row)
        if selected:
            return selected
    return model_rows[:2]


def _upsert_review_package_artifact(
    session: Session,
    *,
    run: Run,
    package_path: str,
    payload: dict[str, Any],
) -> None:
    artifact = (
        session.query(Artifact)
        .filter(Artifact.run_id == run.id, Artifact.kind == "review_package")
        .one_or_none()
    )
    sha256 = __import__("hashlib").sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    if artifact is None:
        artifact = Artifact(
            run_id=run.id,
            kind="review_package",
            storage_mode=ArtifactStorageMode.REPO,
            path=package_path,
            sha256=sha256,
            metadata_={},
        )
        session.add(artifact)
    else:
        artifact.storage_mode = ArtifactStorageMode.REPO
        artifact.path = package_path
        artifact.sha256 = sha256
        artifact.metadata_ = {}


def publish_review_package(session: Session, request: ReviewPublishRequest) -> ReviewPublishResult:
    repo_root = Path(request.repo_root).resolve()
    work_item, run = _resolve_run(session, request)

    sync_result = sync_run_artifacts(
        session,
        ArtifactSyncRequest(
            repo_root=str(repo_root),
            item_id=work_item.item_id,
            run_key=run.run_key,
            evaluator_id=request.evaluator_id,
            session_id=request.session_id,
            host=request.host,
            executor=request.executor,
            branch_name=request.branch_name,
            target_path=request.snapshot_target_path or _default_snapshot_path(item_id=work_item.item_id),
        ),
    )

    session.refresh(run)
    session.refresh(work_item)

    snapshot_rel = str(Path(sync_result.target_path).resolve().relative_to(repo_root.resolve()))
    snapshot_payload = _load_json(Path(sync_result.target_path))
    review_kind = _review_artifact_kind(work_item.task_type)
    review_artifact = _find_artifact(session, run_id=run.id, kind=review_kind)
    review_payload: dict[str, Any] = {}
    if review_artifact is not None:
        try:
            review_payload = _load_json(_resolve_rel_path(review_artifact.path, repo_root))
        except Exception:
            review_payload = {}
    snapshot_payload = _review_snapshot_override(
        repo_root=repo_root,
        snapshot_payload=snapshot_payload,
        review_payload=review_payload,
    )
    Path(sync_result.target_path).write_text(json.dumps(snapshot_payload, indent=2) + "\n", encoding="utf-8")
    _upsert_queue_snapshot_artifact(
        session,
        run=run,
        snapshot_path=snapshot_rel,
        payload=snapshot_payload,
    )
    handoff = _materialized_handoff(snapshot_payload=snapshot_payload, work_item=work_item)
    developer_loop = _developer_loop_payload(work_item)
    submission_history = _submission_history_summary(session=session, run=run)
    branch_name = str((snapshot_payload.get("result") or {}).get("branch", run.branch_name or "")).strip()
    pr_title = _pr_title(work_item)

    package_rel = request.package_target_path or _default_package_path(item_id=work_item.item_id)
    package_path = _resolve_rel_path(package_rel, repo_root)
    package_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "version": 0.1,
        "generated_utc": utcnow().isoformat().replace("+00:00", "Z"),
        "control_plane_source_commit": _repo_head(repo_root),
        "item_id": work_item.item_id,
        "run_key": run.run_key,
        "layer": work_item.layer.value,
        "flow": work_item.flow.value,
        "task_type": work_item.task_type,
        "source_commit": run.checkout_commit or work_item.source_commit,
        "queue_snapshot": {
            "path": snapshot_rel,
            "result": snapshot_payload.get("result"),
        },
        "review_artifact": _artifact_summary(repo_root=repo_root, artifact=review_artifact),
        "developer_loop": developer_loop or None,
        "submission_history": submission_history,
        "pr_payload": {
            "branch": branch_name,
            "title": pr_title,
            "body_fields": handoff.get("pr_body_fields"),
            "body_md": _build_body_md(
                repo_root=repo_root,
                work_item=work_item,
                run=run,
                snapshot_path=snapshot_rel,
                review_artifact=review_artifact,
                snapshot_payload=snapshot_payload,
                handoff=handoff,
                developer_loop=developer_loop,
                submission_history=submission_history,
            ),
            "checklist": handoff.get("checklist"),
        },
    }
    package_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    _upsert_review_package_artifact(
        session,
        run=run,
        package_path=str(package_path.relative_to(repo_root)),
        payload=payload,
    )
    session.add(
        RunEvent(
            run_id=run.id,
            event_time=utcnow(),
            event_type="review_package_published",
            event_payload={
                "target_path": str(package_path.relative_to(repo_root)),
                "snapshot_path": snapshot_rel,
                "review_artifact_kind": review_kind,
            },
        )
    )
    session.commit()
    return ReviewPublishResult(
        item_id=work_item.item_id,
        run_key=run.run_key,
        snapshot_path=str(sync_result.target_path),
        package_path=str(package_path),
        review_artifact_kind=review_artifact.kind if review_artifact is not None else None,
        review_artifact_path=review_artifact.path if review_artifact is not None else None,
        branch_name=branch_name,
        pr_title=pr_title,
    )
