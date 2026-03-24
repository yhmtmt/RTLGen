"""Automatic proposal finalization after an evaluation PR is merged."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
from typing import Any

from sqlalchemy.orm import Session

from control_plane.clock import utcnow
from control_plane.models.artifacts import Artifact
from control_plane.models.github_links import GitHubLink
from control_plane.models.runs import Run
from control_plane.models.work_items import WorkItem


class ProposalFinalizationError(RuntimeError):
    pass


@dataclass(frozen=True)
class ProposalFinalizeRequest:
    repo_root: str
    item_id: str | None = None
    run_key: str | None = None
    pr_number: int | None = None
    pr_url: str | None = None
    merge_commit: str | None = None
    merged_utc: str | None = None
    git_publish: bool = True


@dataclass(frozen=True)
class ProposalFinalizeResult:
    item_id: str
    proposal_id: str | None
    decision: str | None
    next_item_id: str | None
    commit_sha: str | None
    skipped: bool
    skip_reason: str | None


def _resolve_run(session: Session, request: ProposalFinalizeRequest) -> tuple[WorkItem, Run]:
    if request.run_key:
        run = session.query(Run).filter(Run.run_key == request.run_key).one_or_none()
        if run is None:
            raise ProposalFinalizationError(f"run not found: {request.run_key}")
        return run.work_item, run
    if not request.item_id:
        raise ProposalFinalizationError("item_id or run_key is required")
    work_item = session.query(WorkItem).filter(WorkItem.item_id == request.item_id).one_or_none()
    if work_item is None:
        raise ProposalFinalizationError(f"work item not found: {request.item_id}")
    if not work_item.runs:
        raise ProposalFinalizationError(f"work item has no runs: {request.item_id}")
    run = sorted(work_item.runs, key=lambda row: (row.attempt, row.created_at or utcnow()))[-1]
    return work_item, run


def _developer_loop_payload(work_item: WorkItem) -> dict[str, Any]:
    payload = (work_item.task_request.request_payload or {}) if work_item.task_request is not None else {}
    developer_loop = payload.get("developer_loop")
    return dict(developer_loop) if isinstance(developer_loop, dict) else {}


def _evaluation_payload(work_item: WorkItem) -> dict[str, Any]:
    developer_loop = _developer_loop_payload(work_item)
    evaluation = developer_loop.get("evaluation")
    return dict(evaluation) if isinstance(evaluation, dict) else {}


def _comparison_payload(work_item: WorkItem) -> dict[str, Any]:
    developer_loop = _developer_loop_payload(work_item)
    comparison = developer_loop.get("comparison")
    return dict(comparison) if isinstance(comparison, dict) else {}


def _proposal_path(repo_root: Path, work_item: WorkItem) -> Path | None:
    developer_loop = _developer_loop_payload(work_item)
    proposal_path = str(developer_loop.get("proposal_path", "")).strip()
    proposal_id = str(developer_loop.get("proposal_id", "")).strip()
    if proposal_path:
        return (repo_root / proposal_path).resolve()
    if proposal_id:
        return (repo_root / "docs" / "developer_loop" / proposal_id / "proposal.json").resolve()
    return None


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ProposalFinalizationError(f"required proposal artifact is missing: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ProposalFinalizationError(f"expected JSON object at: {path}")
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _find_review_artifact_path(session: Session, *, run_id: str, kind: str) -> str:
    artifact = session.query(Artifact).filter(Artifact.run_id == run_id, Artifact.kind == kind).one_or_none()
    if artifact is None:
        raise ProposalFinalizationError(f"missing {kind} artifact for run {run_id}")
    return str(artifact.path).strip()


def _load_review_payload(session: Session, *, repo_root: Path, run: Run, task_type: str) -> tuple[dict[str, Any], str]:
    kind = {
        "l1_sweep": "promotion_proposal",
        "l2_campaign": "decision_proposal",
    }.get(task_type)
    if not kind:
        raise ProposalFinalizationError(f"unsupported task_type for finalization: {task_type}")
    rel_path = _find_review_artifact_path(session, run_id=run.id, kind=kind)
    payload = _load_json((repo_root / rel_path).resolve())
    return payload, rel_path


def _latest_merged_link(session: Session, *, work_item: WorkItem, pr_number: int | None) -> GitHubLink | None:
    query = session.query(GitHubLink).filter(GitHubLink.work_item_id == work_item.id)
    if pr_number is not None:
        link = query.filter(GitHubLink.pr_number == pr_number).one_or_none()
        if link is not None:
            return link
    return query.order_by(GitHubLink.updated_at.desc(), GitHubLink.created_at.desc()).first()


def _is_merged_status(status: str) -> bool:
    return status.startswith("merged")


def _mark_merged_requested_item(
    entry: dict[str, Any],
    *,
    pr_number: int | None,
    merge_commit: str | None,
    merged_utc: str,
) -> None:
    entry["status"] = "merged"
    notes = str(entry.get("notes", "")).strip()
    details: list[str] = []
    if pr_number is not None:
        entry["merged_pr_number"] = pr_number
        details.append(f"PR #{pr_number}")
    if merge_commit:
        entry["merge_commit"] = merge_commit
        details.append(f"merge {merge_commit}")
    entry["merged_utc"] = merged_utc
    suffix = " and ".join(details) if details else "merged review evidence"
    update = f"Merged via {suffix} at {merged_utc}."
    entry["notes"] = f"{notes} {update}".strip() if notes else update


def _refresh_ready_items(requested_items: list[dict[str, Any]]) -> list[str]:
    merged_items = {
        str(entry.get("item_id", "")).strip()
        for entry in requested_items
        if _is_merged_status(str(entry.get("status", "")).strip())
    }
    ready: list[str] = []
    for entry in requested_items:
        item_id = str(entry.get("item_id", "")).strip()
        if not item_id:
            continue
        status = str(entry.get("status", "")).strip()
        if status in {"merged", "ready_to_queue"}:
            if status == "ready_to_queue":
                ready.append(item_id)
            continue
        dependency_ids = [str(value).strip() for value in (entry.get("depends_on_item_ids") or []) if str(value).strip()]
        baseline_item_id = str(entry.get("paired_baseline_item_id", "")).strip()
        if baseline_item_id:
            dependency_ids.append(baseline_item_id)
        if dependency_ids and any(dep not in merged_items for dep in dependency_ids):
            continue
        if status.startswith("blocked") or status == "pending":
            entry["status"] = "ready_to_queue"
            notes = str(entry.get("notes", "")).strip()
            update = "Prerequisites are merged; item is ready to queue."
            entry["notes"] = f"{notes} {update}".strip() if notes else update
            ready.append(item_id)
    return ready


def _reason_for_l1(*, payload: dict[str, Any], pr_number: int | None) -> tuple[str, str]:
    proposals = payload.get("proposals") or []
    if not proposals:
        return (
            "iterate",
            "Accepted Layer 1 evidence merged, but no concrete promotion proposal entries were present.",
        )
    first = proposals[0] if isinstance(proposals[0], dict) else {}
    metric_summary = first.get("metric_summary")
    if isinstance(metric_summary, dict) and metric_summary:
        pr_text = f" in PR #{pr_number}" if pr_number is not None else ""
        return (
            "promote",
            f"Accepted Layer 1 physical metrics were merged{pr_text} for the current candidate.",
        )
    return (
        "iterate",
        "Accepted Layer 1 checkpoint evidence was merged, but physical metric summaries are still pending.",
    )


def _reason_for_l2(
    *,
    work_item: WorkItem,
    payload: dict[str, Any],
    ready_items: list[str],
) -> tuple[str, str, str]:
    evaluation_mode = str(_evaluation_payload(work_item).get("mode", "")).strip()
    comparison_role = str(_comparison_payload(work_item).get("role", "")).strip()
    if evaluation_mode == "measurement_only":
        next_action = f"queue {ready_items[0]}" if ready_items else "queue the paired comparison item"
        return (
            "iterate",
            "Accepted measurement-only baseline evidence was merged; proposal judgment remains deferred until the paired comparison is reviewed.",
            next_action,
        )
    assessment = payload.get("proposal_assessment")
    if isinstance(assessment, dict):
        outcome = str(assessment.get("outcome", "")).strip()
        summary = str(assessment.get("summary", "")).strip()
        if comparison_role == "candidate" and outcome == "improved":
            return (
                "promote",
                summary or "Paired comparison improved against the merged baseline.",
                "close the proposal as promoted",
            )
        return (
            "iterate",
            summary or "Merged paired evidence does not yet justify promotion.",
            f"inspect follow-on work after {work_item.item_id}",
        )
    return (
        "iterate",
        "Merged Layer 2 evidence was accepted, but no proposal assessment payload was available for promotion.",
        f"inspect follow-on work after {work_item.item_id}",
    )


def _build_analysis_report(
    *,
    proposal_id: str,
    item_id: str,
    run: Run,
    pr_number: int | None,
    payload: dict[str, Any],
    decision: str,
    reason: str,
    next_action: str,
) -> str:
    evaluation_record = payload.get("evaluation_record") if isinstance(payload, dict) else None
    proposal_assessment = payload.get("proposal_assessment") if isinstance(payload, dict) else None
    baseline_lines: list[str] = []
    if isinstance(proposal_assessment, dict):
        baseline_ref = str(proposal_assessment.get("baseline_ref", "")).strip()
        baseline_item_id = str(proposal_assessment.get("baseline_item_id", "")).strip()
        outcome = str(proposal_assessment.get("outcome", "")).strip()
        summary = str(proposal_assessment.get("summary", "")).strip()
        if baseline_ref:
            baseline_lines.append(f"- baseline_ref: `{baseline_ref}`")
        if baseline_item_id:
            baseline_lines.append(f"- baseline_item_id: `{baseline_item_id}`")
        if outcome:
            baseline_lines.append(f"- outcome: `{outcome}`")
        if summary:
            baseline_lines.append(f"- summary: {summary}")
    if not baseline_lines:
        baseline_lines.append("- not applicable")

    result_summary = ""
    if isinstance(evaluation_record, dict):
        result_summary = str(evaluation_record.get("summary", "")).strip()
    elif isinstance(proposal_assessment, dict):
        result_summary = str(proposal_assessment.get("summary", "")).strip()

    review_ref = f"PR #{pr_number}" if pr_number is not None else "merged review PR"
    consumed_lines = [
        f"- `{item_id}`",
        f"- `{run.run_key}`",
        f"- source commit: `{run.checkout_commit or run.work_item.source_commit or 'unknown'}`",
        f"- review: {review_ref}",
    ]
    result_lines = [
        f"- result: `{decision}`",
        f"- confidence level: merged accepted evidence",
        f"- estimated optimization room: {'pending follow-on comparison' if decision == 'iterate' else 'accepted at current stage'}",
        f"- architecture conclusion robustness: {'staged evidence' if decision == 'iterate' else 'accepted for the current proposal scope'}",
    ]
    caveat_lines = ["- no additional caveats recorded during automatic finalization"]
    if isinstance(proposal_assessment, dict) and str(proposal_assessment.get("outcome", "")).strip() == "unavailable":
        caveat_lines = ["- paired baseline comparison payload was unavailable at consume time"]

    lines = [
        "# Analysis Report",
        "",
        "## Candidate",
        f"- `proposal_id`: `{proposal_id}`",
        f"- `candidate_id`: `{item_id}`",
        "",
        "## Evaluations Consumed",
        *consumed_lines,
        "",
        "## Baseline Comparison",
        *baseline_lines,
        "",
        "## Result",
        *result_lines,
        *(["- summary: " + result_summary] if result_summary else []),
        "",
        "## Failures and Caveats",
        *caveat_lines,
        "",
        "## Recommendation",
        f"- `{decision}`",
        f"- reason: {reason}",
        f"- next_action: {next_action}",
        "",
    ]
    return "\n".join(lines)


def _git_env() -> dict[str, str]:
    env = dict(**__import__("os").environ)
    env.setdefault("GIT_AUTHOR_NAME", "RTLGen Control Plane")
    env.setdefault("GIT_AUTHOR_EMAIL", "control-plane@rtlgen.local")
    env.setdefault("GIT_COMMITTER_NAME", env["GIT_AUTHOR_NAME"])
    env.setdefault("GIT_COMMITTER_EMAIL", env["GIT_AUTHOR_EMAIL"])
    return env


def _run_git(repo_root: Path, *args: str, env: dict[str, str] | None = None) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    return result.stdout.strip()


def _git_dirty(repo_root: Path) -> bool:
    return bool(_run_git(repo_root, "status", "--porcelain"))


def _prepare_repo(repo_root: Path) -> str:
    _run_git(repo_root, "fetch", "origin")
    _run_git(repo_root, "checkout", "master")
    _run_git(repo_root, "pull", "--ff-only", "origin", "master")
    return _run_git(repo_root, "rev-parse", "HEAD")


def finalize_after_merge(session: Session, request: ProposalFinalizeRequest) -> ProposalFinalizeResult:
    repo_root = Path(request.repo_root).resolve()
    work_item, run = _resolve_run(session, request)
    proposal_path = _proposal_path(repo_root, work_item)
    if proposal_path is None:
        return ProposalFinalizeResult(
            item_id=work_item.item_id,
            proposal_id=None,
            decision=None,
            next_item_id=None,
            commit_sha=None,
            skipped=True,
            skip_reason="work item has no developer_loop proposal metadata",
        )

    proposal_payload = _load_json(proposal_path)
    proposal_id = str(proposal_payload.get("proposal_id", "")).strip() or proposal_path.parent.name
    evaluation_requests_path = proposal_path.parent / "evaluation_requests.json"
    promotion_decision_path = proposal_path.parent / "promotion_decision.json"
    promotion_result_path = proposal_path.parent / "promotion_result.json"
    analysis_report_path = proposal_path.parent / "analysis_report.md"

    evaluation_requests = _load_json(evaluation_requests_path)
    promotion_decision = _load_json(promotion_decision_path)
    promotion_result = _load_json(promotion_result_path)

    existing_decision = str(promotion_result.get("decision", "")).strip().lower()
    if existing_decision and existing_decision != "pending":
        return ProposalFinalizeResult(
            item_id=work_item.item_id,
            proposal_id=proposal_id,
            decision=existing_decision,
            next_item_id=None,
            commit_sha=None,
            skipped=True,
            skip_reason=f"proposal already finalized with decision={existing_decision}",
        )

    payload, artifact_rel = _load_review_payload(session, repo_root=repo_root, run=run, task_type=work_item.task_type)
    merged_link = _latest_merged_link(session, work_item=work_item, pr_number=request.pr_number)
    pr_number = request.pr_number if request.pr_number is not None else (merged_link.pr_number if merged_link is not None else None)
    pr_url = request.pr_url or (merged_link.pr_url if merged_link is not None else None)
    merged_utc = request.merged_utc or utcnow().isoformat().replace("+00:00", "Z")

    merge_commit = request.merge_commit
    if request.git_publish:
        merge_commit = merge_commit or _prepare_repo(repo_root)
    elif not merge_commit and merged_link is not None:
        merge_commit = merged_link.head_sha

    requested_items = evaluation_requests.get("requested_items")
    if not isinstance(requested_items, list):
        raise ProposalFinalizationError(f"expected requested_items list in {evaluation_requests_path}")
    matched_entry = None
    for entry in requested_items:
        if isinstance(entry, dict) and str(entry.get("item_id", "")).strip() == work_item.item_id:
            matched_entry = entry
            break
    if matched_entry is None:
        raise ProposalFinalizationError(f"item {work_item.item_id} is not present in {evaluation_requests_path}")
    _mark_merged_requested_item(
        matched_entry,
        pr_number=pr_number,
        merge_commit=merge_commit,
        merged_utc=merged_utc,
    )
    evaluation_requests["source_commit"] = str(payload.get("source_commit") or run.checkout_commit or work_item.source_commit or "")
    ready_items = _refresh_ready_items([entry for entry in requested_items if isinstance(entry, dict)])

    if work_item.task_type == "l1_sweep":
        decision, reason = _reason_for_l1(payload=payload, pr_number=pr_number)
        next_action = f"queue {ready_items[0]}" if ready_items else "inspect the next dependent item"
    elif work_item.task_type == "l2_campaign":
        decision, reason, next_action = _reason_for_l2(work_item=work_item, payload=payload, ready_items=ready_items)
    else:
        raise ProposalFinalizationError(f"unsupported task_type for proposal finalization: {work_item.task_type}")

    evidence_refs = [
        f"item:{work_item.item_id}",
        f"run:{run.run_key}",
        f"artifact:{artifact_rel}",
    ]
    if pr_number is not None:
        evidence_refs.append(f"pr:#{pr_number}")
    if pr_url:
        evidence_refs.append(pr_url)

    promotion_decision.update(
        {
            "proposal_id": proposal_id,
            "candidate_id": work_item.item_id,
            "decision": decision,
            "reason": reason,
            "evidence_refs": evidence_refs,
            "next_action": next_action,
            "requires_human_approval": False,
        }
    )
    promotion_result.update(
        {
            "proposal_id": proposal_id,
            "decision": decision,
            "pr_number": pr_number,
            "merge_commit": merge_commit,
            "merged_utc": merged_utc,
        }
    )

    analysis_report = _build_analysis_report(
        proposal_id=proposal_id,
        item_id=work_item.item_id,
        run=run,
        pr_number=pr_number,
        payload=payload,
        decision=decision,
        reason=reason,
        next_action=next_action,
    )

    _write_json(evaluation_requests_path, evaluation_requests)
    _write_json(promotion_decision_path, promotion_decision)
    _write_json(promotion_result_path, promotion_result)
    analysis_report_path.write_text(analysis_report, encoding="utf-8")

    commit_sha: str | None = None
    if request.git_publish:
        if not _git_dirty(repo_root):
            raise ProposalFinalizationError("proposal finalization produced no repository changes")
        rel_paths = [
            str(evaluation_requests_path.relative_to(repo_root)),
            str(promotion_decision_path.relative_to(repo_root)),
            str(promotion_result_path.relative_to(repo_root)),
            str(analysis_report_path.relative_to(repo_root)),
        ]
        _run_git(repo_root, "add", *rel_paths)
        _run_git(
            repo_root,
            "commit",
            "-m",
            f"control_plane: finalize {proposal_id} after merge of {work_item.item_id}",
            env=_git_env(),
        )
        _run_git(repo_root, "push", "origin", "HEAD:master")
        commit_sha = _run_git(repo_root, "rev-parse", "HEAD")

    return ProposalFinalizeResult(
        item_id=work_item.item_id,
        proposal_id=proposal_id,
        decision=decision,
        next_item_id=ready_items[0] if ready_items else None,
        commit_sha=commit_sha,
        skipped=False,
        skip_reason=None,
    )
