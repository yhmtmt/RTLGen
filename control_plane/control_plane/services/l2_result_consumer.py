"""Layer 2 result consumption helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timezone
import csv
import re
import hashlib
import json
from pathlib import Path
import math
import subprocess
from typing import Any

from sqlalchemy.orm import Session

from control_plane.clock import utcnow
from control_plane.models.artifacts import Artifact
from control_plane.models.enums import ArtifactStorageMode, RunStatus, WorkItemState
from control_plane.models.run_events import RunEvent
from control_plane.models.runs import Run
from control_plane.models.work_items import WorkItem
from control_plane.services.docs_paths import resolve_proposal_file


class Layer2ResultConsumerError(RuntimeError):
    pass


_RETRY_SUFFIX_RE = re.compile(r"_r\d+$")


def _repo_head(repo_root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip() or None
    except Exception:
        return None


@dataclass(frozen=True)
class Layer2ConsumeRequest:
    repo_root: str
    item_id: str | None = None
    run_key: str | None = None
    target_path: str | None = None


@dataclass(frozen=True)
class Layer2ConsumeResult:
    item_id: str
    run_key: str
    target_path: str
    recommended_arch_id: str
    recommended_macro_mode: str
    profile_count: int
    work_item_state: str


def _default_target_path(*, item_id: str) -> str:
    return f"control_plane/shadow_exports/l2_decisions/{item_id}.json"


def _resolve_path(*, repo_root: Path, path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return repo_root / path


def _resolve_run(session: Session, request: Layer2ConsumeRequest) -> tuple[WorkItem, Run]:
    if request.run_key:
        run = session.query(Run).filter(Run.run_key == request.run_key).one_or_none()
        if run is None:
            raise Layer2ResultConsumerError(f"run not found: {request.run_key}")
        return run.work_item, run
    if not request.item_id:
        raise Layer2ResultConsumerError("item_id or run_key is required")
    work_item = session.query(WorkItem).filter(WorkItem.item_id == request.item_id).one_or_none()
    if work_item is None:
        raise Layer2ResultConsumerError(f"work item not found: {request.item_id}")
    if not work_item.runs:
        raise Layer2ResultConsumerError(f"work item has no runs: {request.item_id}")
    run = sorted(work_item.runs, key=lambda row: (row.attempt, row.created_at or utcnow()))[-1]
    return work_item, run


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _find_output_path(work_item: WorkItem, suffix: str) -> str:
    for path in work_item.expected_outputs or []:
        if str(path).endswith(suffix):
            return str(path)
    raise Layer2ResultConsumerError(f"expected output not found for suffix {suffix}: {work_item.item_id}")


def _find_output_path_optional(work_item: WorkItem, suffix: str) -> str | None:
    for path in work_item.expected_outputs or []:
        if str(path).endswith(suffix):
            return str(path)
    return None


def _summary_best_row(rows: list[dict[str, str]]) -> dict[str, str]:
    aggregate_rows = [row for row in rows if str(row.get("scope", "")).strip() == "aggregate"]
    if not aggregate_rows:
        aggregate_rows = [row for row in rows if str(row.get("scope", "")).strip() == "model"]
    ranked = [row for row in aggregate_rows if str(row.get("objective_rank", "")).strip()]
    if ranked:
        ranked.sort(key=lambda row: int(str(row.get("objective_rank", "999999")).strip() or "999999"))
        return ranked[0]

    def as_float(value: str | None) -> float:
        try:
            return float(str(value).strip())
        except Exception:
            return float("inf")

    aggregate_rows.sort(
        key=lambda row: (
            as_float(row.get("latency_ms_mean")),
            as_float(row.get("energy_mj_mean")),
            as_float(row.get("critical_path_ns_mean")),
        )
    )
    if not aggregate_rows:
        raise Layer2ResultConsumerError("summary.csv has no aggregate/model rows")
    return aggregate_rows[0]


def _profile_recommendations(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for row in rows:
        result.append(
            {
                "profile": str(row.get("profile", "")).strip(),
                "best_arch_id": str(row.get("best_arch_id", "")).strip(),
                "best_macro_mode": str(row.get("best_macro_mode", "")).strip(),
                "objective_score": str(row.get("objective_score", "")).strip(),
                "latency_ms_mean": str(row.get("latency_ms_mean", "")).strip(),
                "energy_mj_mean": str(row.get("energy_mj_mean", "")).strip(),
                "flow_elapsed_s_mean": str(row.get("flow_elapsed_s_mean", "")).strip(),
                "best_json": str(row.get("best_json", "")).strip(),
                "report_md": str(row.get("report_md", "")).strip(),
                "pareto_csv": str(row.get("pareto_csv", "")).strip(),
            }
        )
    return result


def _select_focused_result_row(
    rows: list[dict[str, str]],
    *,
    arch_id: str,
    macro_mode: str,
) -> dict[str, str] | None:
    selected_rows = _select_focused_result_rows(rows, arch_id=arch_id, macro_mode=macro_mode)
    return selected_rows[0] if selected_rows else None


def _select_focused_result_rows(
    rows: list[dict[str, str]],
    *,
    arch_id: str,
    macro_mode: str,
) -> list[dict[str, str]]:
    ok_rows = [row for row in rows if str(row.get("status", "")).strip() == "ok"]
    if not ok_rows:
        return []

    matching_rows = [
        row
        for row in ok_rows
        if str(row.get("arch_id", "")).strip() == arch_id and str(row.get("macro_mode", "")).strip() == macro_mode
    ]
    if not matching_rows:
        matching_rows = [row for row in ok_rows if str(row.get("arch_id", "")).strip() == arch_id]
    if not matching_rows:
        matching_rows = ok_rows

    selected: list[dict[str, str]] = []
    seen_keys: set[tuple[str, str, str]] = set()
    for row in matching_rows:
        key = (
            str(row.get("arch_id", "")).strip(),
            str(row.get("macro_mode", "")).strip(),
            str(row.get("model_id", "")).strip(),
        )
        if key in seen_keys:
            continue
        seen_keys.add(key)
        selected.append(row)
    return selected


def _focused_artifact_refs(result_row: dict[str, str] | None) -> dict[str, str]:
    if result_row is None:
        return {}
    artifact_fields = {
        "focused_candidate_schedule_yml": "artifact_schedule_yml",
        "focused_candidate_descriptors_bin": "artifact_descriptors_bin",
        "focused_candidate_perf_trace_json": "artifact_perf_trace_json",
    }
    refs: dict[str, str] = {}
    for out_key, row_key in artifact_fields.items():
        value = str(result_row.get(row_key, "")).strip()
        if value:
            refs[out_key] = value
    return refs


def _focused_model_artifact_refs(result_rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    focused_models: list[dict[str, str]] = []
    for row in result_rows:
        model_id = str(row.get("model_id", "")).strip()
        if not model_id:
            continue
        schedule_yml = str(row.get("artifact_schedule_yml", "")).strip()
        descriptors_bin = str(row.get("artifact_descriptors_bin", "")).strip()
        perf_trace_json = str(row.get("artifact_perf_trace_json", "")).strip()
        if not any((schedule_yml, descriptors_bin, perf_trace_json)):
            continue
        focused_models.append(
            {
                "model_id": model_id,
                "schedule_yml": schedule_yml,
                "descriptors_bin": descriptors_bin,
                "perf_trace_json": perf_trace_json,
            }
        )
    return {"focused_model_artifacts": focused_models} if focused_models else {}


def _retry_base(item_id: str) -> str:
    return _RETRY_SUFFIX_RE.sub("", item_id.strip())


def _developer_loop_payload(work_item: WorkItem) -> dict[str, Any]:
    payload = dict(work_item.task_request.request_payload or {})
    developer_loop = payload.get("developer_loop")
    return dict(developer_loop) if isinstance(developer_loop, dict) else {}


def _proposal_file(repo_root: Path, work_item: WorkItem) -> Path | None:
    developer_loop = _developer_loop_payload(work_item)
    if not isinstance(developer_loop, dict):
        return None
    proposal_path_text = str(developer_loop.get("proposal_path", "")).strip()
    if not proposal_path_text:
        return None
    return resolve_proposal_file(repo_root, proposal_path=proposal_path_text)


def _load_proposal(repo_root: Path, work_item: WorkItem) -> dict[str, Any] | None:
    proposal_file = _proposal_file(repo_root, work_item)
    if proposal_file is None or not proposal_file.exists():
        return None
    try:
        return _load_json(proposal_file)
    except Exception:
        return None


def _load_requested_item_entry(repo_root: Path, work_item: WorkItem) -> dict[str, Any] | None:
    proposal_file = _proposal_file(repo_root, work_item)
    if proposal_file is None:
        return None
    evaluation_requests_path = proposal_file.parent / "evaluation_requests.json"
    if not evaluation_requests_path.exists():
        return None
    try:
        payload = _load_json(evaluation_requests_path)
    except Exception:
        return None
    requested_items = payload.get("requested_items")
    if not isinstance(requested_items, list):
        return None
    for entry in requested_items:
        if isinstance(entry, dict) and str(entry.get("item_id", "")).strip() == work_item.item_id:
            return entry
    work_retry_base = _retry_base(work_item.item_id)
    retry_matches = [
        entry
        for entry in requested_items
        if isinstance(entry, dict) and _retry_base(str(entry.get("item_id", "")).strip()) == work_retry_base
    ]
    if len(retry_matches) == 1:
        return retry_matches[0]
    return None


def _requested_entry_text(repo_root: Path, work_item: WorkItem, *, key: str) -> str:
    entry = _load_requested_item_entry(repo_root, work_item)
    if not isinstance(entry, dict):
        return ""
    return str(entry.get(key, "")).strip()


def _developer_loop_comparison(repo_root: Path, work_item: WorkItem) -> dict[str, Any]:
    developer_loop = _developer_loop_payload(work_item)
    comparison = developer_loop.get("comparison")
    result = dict(comparison) if isinstance(comparison, dict) else {}
    if not str(result.get("paired_baseline_item_id", "")).strip():
        fallback_baseline = _requested_entry_text(repo_root, work_item, key="paired_baseline_item_id")
        if fallback_baseline:
            result["paired_baseline_item_id"] = fallback_baseline
    if not str(result.get("role", "")).strip():
        fallback_role = _requested_entry_text(repo_root, work_item, key="comparison_role")
        if fallback_role:
            result["role"] = fallback_role
    return result


def _developer_loop_evaluation(repo_root: Path, work_item: WorkItem) -> dict[str, Any]:
    developer_loop = _developer_loop_payload(work_item)
    evaluation = developer_loop.get("evaluation")
    result = dict(evaluation) if isinstance(evaluation, dict) else {}
    if not str(result.get("mode", "")).strip():
        fallback_mode = _requested_entry_text(repo_root, work_item, key="evaluation_mode")
        if fallback_mode:
            result["mode"] = fallback_mode
    return result


def _developer_loop_abstraction_layer(repo_root: Path, work_item: WorkItem) -> str:
    developer_loop = _developer_loop_payload(work_item)
    abstraction = developer_loop.get("abstraction")
    if isinstance(abstraction, dict):
        layer = str(abstraction.get("layer", "")).strip()
        if layer:
            return layer
    fallback_layer = _requested_entry_text(repo_root, work_item, key="abstraction_layer")
    if fallback_layer:
        return fallback_layer
    proposal = _load_proposal(repo_root, work_item)
    if isinstance(proposal, dict):
        return str(proposal.get("abstraction_layer", "")).strip()
    return ""


def _proposal_context(work_item: WorkItem, proposal: dict[str, Any] | None) -> dict[str, Any]:
    developer_loop = _developer_loop_payload(work_item)
    direct_comparison = (proposal or {}).get("direct_comparison") if isinstance(proposal, dict) else {}
    if not isinstance(direct_comparison, dict):
        direct_comparison = {}
    return {
        "proposal_id": str((proposal or {}).get("proposal_id", "")).strip() or str(developer_loop.get("proposal_id", "")).strip(),
        "title": str((proposal or {}).get("title", "")).strip(),
        "kind": str((proposal or {}).get("kind", "")).strip(),
        "primary_question": str(direct_comparison.get("primary_question", "")).strip(),
        "baseline_refs": list((proposal or {}).get("baseline_refs") or []),
    }


def _effective_evaluation_mode(repo_root: Path, work_item: WorkItem) -> str:
    evaluation = _developer_loop_evaluation(repo_root, work_item)
    mode = str(evaluation.get("mode", "")).strip()
    if mode:
        return mode
    comparison = _developer_loop_comparison(repo_root, work_item)
    role = str(comparison.get("role", "")).strip()
    mapping = {
        "refreshed_baseline": "baseline_refresh",
        "candidate": "paired_comparison",
        "ranking": "broad_ranking",
        "measurement_only": "measurement_only",
    }
    return mapping.get(role, "paired_comparison" if role else "paired_comparison")


def _effective_comparison_role(repo_root: Path, work_item: WorkItem) -> str:
    comparison = _developer_loop_comparison(repo_root, work_item)
    role = str(comparison.get("role", "")).strip()
    if role:
        return role
    return {
        "baseline_refresh": "refreshed_baseline",
        "paired_comparison": "candidate",
        "broad_ranking": "ranking",
        "measurement_only": "measurement_only",
    }.get(_effective_evaluation_mode(repo_root, work_item), "standalone")


def _resolve_baseline_summary_from_decision_payload(
    *,
    repo_root: Path,
    item_id: str,
) -> tuple[str, list[dict[str, str]], str | None, dict[str, Any], dict[str, str]] | tuple[None, None, None, None, None]:
    decision_path = repo_root / "control_plane" / "shadow_exports" / "l2_decisions" / f"{item_id}.json"
    if not decision_path.exists():
        return None, None, None, None, None
    try:
        payload = _load_json(decision_path)
    except Exception:
        return None, None, None, None, None
    source_refs = payload.get("source_refs")
    if not isinstance(source_refs, dict):
        return None, None, None, None, None
    summary_rel = str(source_refs.get("summary_csv", "")).strip()
    if not summary_rel:
        return None, None, None, None, None
    summary_path = _resolve_path(repo_root=repo_root, path_text=summary_rel)
    if not summary_path.exists():
        return None, None, None, None, None
    report_rel = str(source_refs.get("report_md", "")).strip() or None
    report_path = _resolve_path(repo_root=repo_root, path_text=report_rel) if report_rel else None
    baseline_ref = str(Path(summary_rel).parent.as_posix())
    resolved_source_refs = {
        "baseline_summary_csv": summary_rel,
    }
    report_rel_value: str | None = None
    if report_path is not None and report_path.exists():
        report_rel_value = str(report_path.relative_to(repo_root))
        resolved_source_refs["baseline_report_md"] = report_rel_value
    assessment_meta = {
        "baseline_item_id": item_id,
    }
    return baseline_ref, _load_csv(summary_path), report_rel_value, assessment_meta, resolved_source_refs


def _resolve_baseline_summary_from_work_item(
    session: Session,
    *,
    repo_root: Path,
    item_id: str,
) -> tuple[str, list[dict[str, str]], str | None, dict[str, Any], dict[str, str]] | tuple[None, None, None, None, None]:
    baseline_item = session.query(WorkItem).filter(WorkItem.item_id == item_id).one_or_none()
    if baseline_item is None:
        return _resolve_baseline_summary_from_decision_payload(repo_root=repo_root, item_id=item_id)
    summary_rel = _find_output_path_optional(baseline_item, "/summary.csv")
    if not summary_rel:
        return _resolve_baseline_summary_from_decision_payload(repo_root=repo_root, item_id=item_id)
    summary_path = _resolve_path(repo_root=repo_root, path_text=summary_rel)
    if not summary_path.exists():
        return _resolve_baseline_summary_from_decision_payload(repo_root=repo_root, item_id=item_id)
    report_rel = _find_output_path_optional(baseline_item, "/report.md")
    report_path = _resolve_path(repo_root=repo_root, path_text=report_rel) if report_rel else None
    baseline_ref = str(Path(summary_rel).parent.as_posix())
    source_refs = {
        "baseline_summary_csv": summary_rel,
    }
    report_rel_value: str | None = None
    if report_path is not None and report_path.exists():
        report_rel_value = str(report_path.relative_to(repo_root))
        source_refs["baseline_report_md"] = report_rel_value
    assessment_meta = {
        "baseline_item_id": baseline_item.item_id,
    }
    return baseline_ref, _load_csv(summary_path), report_rel_value, assessment_meta, source_refs


def _resolve_baseline_summary(
    session: Session,
    *,
    repo_root: Path,
    work_item: WorkItem,
    proposal: dict[str, Any] | None,
) -> tuple[str, list[dict[str, str]], str | None, dict[str, Any], dict[str, str]] | tuple[None, None, None, None, None]:
    comparison = _developer_loop_comparison(repo_root, work_item)
    paired_baseline_item_id = str(comparison.get("paired_baseline_item_id", "")).strip()
    if paired_baseline_item_id:
        resolved = _resolve_baseline_summary_from_work_item(
            session,
            repo_root=repo_root,
            item_id=paired_baseline_item_id,
        )
        if resolved[0] is not None:
            return resolved
        return None, None, None, None, None
    for ref in (proposal or {}).get("baseline_refs") or []:
        ref_text = str(ref).strip()
        if not ref_text:
            continue
        candidate = _resolve_path(repo_root=repo_root, path_text=ref_text)
        if candidate.is_dir():
            summary_path = candidate / "summary.csv"
            if summary_path.exists():
                report_path = candidate / "report.md"
                report_rel = str(report_path.relative_to(repo_root)) if report_path.exists() else None
                source_refs = {
                    "baseline_summary_csv": f"{ref_text}/summary.csv",
                }
                if report_rel:
                    source_refs["baseline_report_md"] = report_rel
                return ref_text, _load_csv(summary_path), report_rel, {}, source_refs
    return None, None, None, None, None


def _comparable_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    for row in rows:
        scope = str(row.get("scope", "")).strip()
        if scope not in {"aggregate", "model"}:
            continue
        if not str(row.get("arch_id", "")).strip():
            continue
        if not str(row.get("macro_mode", "")).strip():
            continue
        result.append(row)
    return result


def _row_key(row: dict[str, str]) -> tuple[str, str, str, str]:
    scope = str(row.get("scope", "")).strip()
    model_id = str(row.get("model_id", "")).strip() if scope == "model" else ""
    return (
        scope,
        str(row.get("arch_id", "")).strip(),
        str(row.get("macro_mode", "")).strip(),
        model_id,
    )


def _parse_float(value: Any) -> float | None:
    try:
        parsed = float(str(value).strip())
    except Exception:
        return None
    if math.isnan(parsed) or math.isinf(parsed):
        return None
    return parsed


def _metric_triplet(candidate: dict[str, str], baseline: dict[str, str], field: str) -> dict[str, float | None]:
    candidate_value = _parse_float(candidate.get(field))
    baseline_value = _parse_float(baseline.get(field))
    delta = None
    if candidate_value is not None and baseline_value is not None:
        delta = candidate_value - baseline_value
    return {
        "baseline": baseline_value,
        "candidate": candidate_value,
        "delta": delta,
    }


def _comparison_outcome(comparisons: list[dict[str, Any]]) -> tuple[str, str]:
    if not comparisons:
        return "unavailable", "Focused comparison baseline could not be matched to any candidate rows."
    tol = 1e-15
    any_change = False
    all_non_worse = True
    all_non_better = True
    latency_energy_improved = False
    latency_energy_regressed = False
    for comparison in comparisons:
        latency_delta = comparison["metrics"]["latency_ms_mean"]["delta"]
        energy_delta = comparison["metrics"]["energy_mj_mean"]["delta"]
        for delta in (latency_delta, energy_delta):
            if delta is None:
                continue
            if abs(delta) > tol:
                any_change = True
            if delta > tol:
                all_non_worse = False
            if delta < -tol:
                all_non_better = False
        if (latency_delta is not None and latency_delta < -tol) or (energy_delta is not None and energy_delta < -tol):
            latency_energy_improved = True
        if (latency_delta is not None and latency_delta > tol) or (energy_delta is not None and energy_delta > tol):
            latency_energy_regressed = True
    if not any_change:
        return "no_measurable_change", "Focused comparison matched the baseline with no measurable latency or energy delta."
    if latency_energy_improved and not latency_energy_regressed and all_non_worse:
        return "improved", "Focused comparison improved latency and/or energy without regressing matched rows."
    if latency_energy_regressed and not latency_energy_improved and all_non_better:
        return "regressed", "Focused comparison regressed latency and/or energy versus the matched baseline rows."
    return "mixed", "Focused comparison changed matched rows, but the deltas are mixed across latency and energy."


def _expectation_status(*, expected_direction: str, outcome: str) -> str:
    if not expected_direction or expected_direction == "unknown":
        return "unspecified"
    if expected_direction == "same_as_historical":
        return "as_expected" if outcome == "no_measurable_change" else "unexpected"
    if expected_direction == "better_than_historical":
        return "as_expected" if outcome == "improved" else "unexpected"
    if expected_direction == "worse_than_historical":
        return "as_expected" if outcome == "regressed" else "unexpected"
    return "unspecified"


def _build_evaluation_record(
    *,
    work_item: WorkItem,
    proposal: dict[str, Any] | None,
    repo_root: Path,
    evaluation_mode: str,
    comparison_role: str,
    baseline_ref: str | None,
    baseline_item_id: str | None,
    outcome: str | None,
    expectation_outcome: str | None,
    summary: str,
) -> dict[str, Any] | None:
    context = _proposal_context(work_item, proposal)
    if not any((context.get("proposal_id"), context.get("title"), context.get("primary_question"))):
        return None
    evaluation = _developer_loop_evaluation(repo_root, work_item)
    expected_direction = str(evaluation.get("expected_direction", "")).strip() or "unknown"
    expected_reason = str(evaluation.get("expected_reason", "")).strip()
    record = {
        "proposal_id": str(context.get("proposal_id", "")).strip(),
        "title": str(context.get("title", "")).strip(),
        "primary_question": str(context.get("primary_question", "")).strip(),
        "evaluation_mode": evaluation_mode,
        "comparison_role": comparison_role,
        "abstraction_layer": _developer_loop_abstraction_layer(repo_root, work_item),
        "expected_direction": expected_direction,
        "expected_reason": expected_reason,
        "summary": summary,
    }
    if baseline_ref:
        record["baseline_ref"] = baseline_ref
    if baseline_item_id:
        record["baseline_item_id"] = baseline_item_id
    if outcome:
        record["outcome"] = outcome
        record["expectation_status"] = _expectation_status(
            expected_direction=expected_direction,
            outcome=expectation_outcome or outcome,
        )
    else:
        record["expectation_status"] = "not_applicable"
    return record


def _build_proposal_assessment(
    *,
    session: Session,
    work_item: WorkItem,
    repo_root: Path,
    proposal: dict[str, Any] | None,
    summary_rows: list[dict[str, str]],
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, dict[str, str]]:
    context = _proposal_context(work_item, proposal)
    if proposal is None and not context.get("proposal_id"):
        return None, None, {}
    evaluation_mode = _effective_evaluation_mode(repo_root, work_item)
    comparison_role = _effective_comparison_role(repo_root, work_item)
    if evaluation_mode == "measurement_only":
        summary = "This item records metrics for the requested architecture point and does not emit a proposal judgment."
        return (
            None,
            _build_evaluation_record(
                work_item=work_item,
                proposal=proposal,
                repo_root=repo_root,
                evaluation_mode=evaluation_mode,
                comparison_role=comparison_role,
                baseline_ref=None,
                baseline_item_id=None,
                outcome=None,
                expectation_outcome=None,
                summary=summary,
            ),
            {},
        )
    if evaluation_mode == "broad_ranking":
        summary = (
            "Broad ranking evidence was recorded for this proposal; focused baseline comparison is not required "
            "for this evaluation mode."
        )
        assessment = {
            "proposal_id": str(context.get("proposal_id", "")).strip(),
            "title": str(context.get("title", "")).strip(),
            "kind": str(context.get("kind", "")).strip(),
            "primary_question": str(context.get("primary_question", "")).strip(),
            "evaluation_mode": evaluation_mode,
            "comparison_role": comparison_role,
            "outcome": "ranking_recorded",
            "summary": summary,
            "baseline_ref": None,
            "baseline_item_id": None,
            "matched_row_count": 0,
            "matched_rows": [],
        }
        return (
            assessment,
            _build_evaluation_record(
                work_item=work_item,
                proposal=proposal,
                repo_root=repo_root,
                evaluation_mode=evaluation_mode,
                comparison_role=comparison_role,
                baseline_ref=None,
                baseline_item_id=None,
                outcome="ranking_recorded",
                expectation_outcome="ranking_recorded",
                summary=summary,
            ),
            {},
        )
    comparison = _developer_loop_comparison(repo_root, work_item)
    baseline_ref, baseline_rows, baseline_report, assessment_meta, source_refs = _resolve_baseline_summary(
        session,
        repo_root=repo_root,
        work_item=work_item,
        proposal=proposal,
    )
    baseline_item_id = None
    if isinstance(assessment_meta, dict):
        baseline_item_id = str(assessment_meta.get("baseline_item_id", "")).strip() or None
    if baseline_ref is None or baseline_rows is None:
        if comparison_role == "candidate" and str(comparison.get("paired_baseline_item_id", "")).strip():
            missing_summary = "Paired baseline item could not be resolved for focused candidate comparison."
        else:
            missing_summary = "Focused comparison baseline could not be resolved from proposal baseline_refs."
        assessment = {
                "proposal_id": str(context.get("proposal_id", "")).strip(),
                "title": str(context.get("title", "")).strip(),
                "primary_question": str(context.get("primary_question", "")).strip(),
                "evaluation_mode": evaluation_mode,
                "comparison_role": comparison_role,
                "outcome": "unavailable",
                "summary": missing_summary,
                "baseline_ref": None,
                "baseline_item_id": str(comparison.get("paired_baseline_item_id", "")).strip() or None,
                "matched_row_count": 0,
                "matched_rows": [],
            }
        return (
            assessment,
            _build_evaluation_record(
                work_item=work_item,
                proposal=proposal,
                repo_root=repo_root,
                evaluation_mode=evaluation_mode,
                comparison_role=comparison_role,
                baseline_ref=None,
                baseline_item_id=assessment.get("baseline_item_id"),
                outcome="unavailable",
                expectation_outcome="unavailable",
                summary=missing_summary,
            ),
            {},
        )

    baseline_by_key = {_row_key(row): row for row in _comparable_rows(baseline_rows)}
    comparisons: list[dict[str, Any]] = []
    for candidate_row in _comparable_rows(summary_rows):
        key = _row_key(candidate_row)
        baseline_row = baseline_by_key.get(key)
        if baseline_row is None:
            continue
        comparisons.append(
            {
                "scope": key[0],
                "arch_id": key[1],
                "macro_mode": key[2],
                "model_id": key[3] or None,
                "metrics": {
                    "latency_ms_mean": _metric_triplet(candidate_row, baseline_row, "latency_ms_mean"),
                    "energy_mj_mean": _metric_triplet(candidate_row, baseline_row, "energy_mj_mean"),
                    "critical_path_ns_mean": _metric_triplet(candidate_row, baseline_row, "critical_path_ns_mean"),
                    "total_power_mw_mean": _metric_triplet(candidate_row, baseline_row, "total_power_mw_mean"),
                    "flow_elapsed_s_mean": _metric_triplet(candidate_row, baseline_row, "flow_elapsed_s_mean"),
                    "throughput_infer_per_s_mean": _metric_triplet(
                        candidate_row, baseline_row, "throughput_infer_per_s_mean"
                    ),
                },
            }
        )

    raw_outcome, summary = _comparison_outcome(comparisons)
    outcome = raw_outcome
    if comparison_role == "refreshed_baseline":
        outcome = "baseline_refreshed"
        summary = (
            "This run refreshes the focused comparison baseline under the corrected contract; "
            "proposal judgment is deferred until the paired candidate run is reviewed."
        )
    extra_refs = dict(source_refs or {})
    assessment = {
            "proposal_id": str(context.get("proposal_id", "")).strip(),
            "title": str(context.get("title", "")).strip(),
            "kind": str(context.get("kind", "")).strip(),
            "primary_question": str(context.get("primary_question", "")).strip(),
            "evaluation_mode": evaluation_mode,
            "comparison_role": comparison_role,
            "outcome": outcome,
            "summary": summary,
            "baseline_ref": baseline_ref,
            **(assessment_meta or {}),
            "matched_row_count": len(comparisons),
            "matched_rows": comparisons,
        }
    return (
        assessment,
        _build_evaluation_record(
            work_item=work_item,
            proposal=proposal,
            repo_root=repo_root,
            evaluation_mode=evaluation_mode,
            comparison_role=comparison_role,
            baseline_ref=baseline_ref,
            baseline_item_id=baseline_item_id,
            outcome=outcome,
            expectation_outcome=raw_outcome,
            summary=summary,
        ),
        extra_refs,
    )


def _build_payload(
    *,
    repo_root: Path,
    work_item: WorkItem,
    run: Run,
    best_point: dict[str, Any],
    summary_best: dict[str, str],
    objective_profiles: list[dict[str, Any]],
    source_refs: dict[str, str],
    evaluation_record: dict[str, Any] | None,
    proposal_assessment: dict[str, Any] | None,
) -> dict[str, Any]:
    best = best_point.get("best") or {}
    return {
        "version": 0.1,
        "generated_utc": utcnow().astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "item_id": work_item.item_id,
        "run_key": run.run_key,
        "layer": work_item.layer.value,
        "flow": work_item.flow.value,
        "platform": work_item.platform,
        "task_type": work_item.task_type,
        "source_commit": run.checkout_commit or work_item.source_commit,
        "review_metadata_source_commit": _repo_head(repo_root) or run.checkout_commit or work_item.source_commit,
        "objective": work_item.task_request.description,
        "input_manifest": work_item.input_manifest,
        "recommendation": {
            "arch_id": best.get("arch_id") or summary_best.get("arch_id"),
            "macro_mode": best.get("macro_mode") or summary_best.get("macro_mode"),
            "objective_rank": best.get("objective_rank") or summary_best.get("objective_rank"),
            "objective_score": best.get("objective_score") or summary_best.get("objective_score"),
            "latency_ms_mean": best.get("latency_ms_mean") or summary_best.get("latency_ms_mean"),
            "energy_mj_mean": best.get("energy_mj_mean") or summary_best.get("energy_mj_mean"),
            "critical_path_ns_mean": best.get("critical_path_ns_mean") or summary_best.get("critical_path_ns_mean"),
            "die_area_um2_mean": best.get("die_area_um2_mean") or summary_best.get("die_area_um2_mean"),
            "total_power_mw_mean": best.get("total_power_mw_mean") or summary_best.get("total_power_mw_mean"),
            "flow_elapsed_s_mean": best.get("flow_elapsed_s_mean") or summary_best.get("flow_elapsed_s_mean"),
        },
        "objective_profiles": objective_profiles,
        "evaluation_record": evaluation_record,
        "proposal_assessment": proposal_assessment,
        "source_refs": source_refs,
    }


def _upsert_artifact(session: Session, *, run: Run, target_path: str, payload: dict[str, Any]) -> None:
    artifact = (
        session.query(Artifact)
        .filter(Artifact.run_id == run.id, Artifact.kind == "decision_proposal")
        .one_or_none()
    )
    sha256 = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    if artifact is None:
        artifact = Artifact(
            run_id=run.id,
            kind="decision_proposal",
            storage_mode=ArtifactStorageMode.REPO,
            path=target_path,
            sha256=sha256,
            metadata_={"profile_count": len(payload.get("objective_profiles") or [])},
        )
        session.add(artifact)
    else:
        artifact.storage_mode = ArtifactStorageMode.REPO
        artifact.path = target_path
        artifact.sha256 = sha256
        artifact.metadata_ = {"profile_count": len(payload.get("objective_profiles") or [])}


def consume_l2_result(session: Session, request: Layer2ConsumeRequest) -> Layer2ConsumeResult:
    repo_root = Path(request.repo_root).resolve()
    work_item, run = _resolve_run(session, request)
    if work_item.task_type != "l2_campaign":
        raise Layer2ResultConsumerError(f"work item is not l2_campaign: {work_item.item_id}")
    if run.status != RunStatus.SUCCEEDED:
        raise Layer2ResultConsumerError(f"run is not succeeded: {run.run_key} status={run.status.value}")

    best_point_rel = _find_output_path(work_item, "/best_point.json")
    summary_rel = _find_output_path(work_item, "/summary.csv")
    results_rel = _find_output_path(work_item, "/results.csv")
    report_rel = _find_output_path(work_item, "/report.md")
    objective_sweep_rel = _find_output_path_optional(work_item, "/objective_sweep.csv")

    best_point = _load_json(_resolve_path(repo_root=repo_root, path_text=best_point_rel))
    summary_rows = _load_csv(_resolve_path(repo_root=repo_root, path_text=summary_rel))
    results_rows = _load_csv(_resolve_path(repo_root=repo_root, path_text=results_rel))
    summary_best = _summary_best_row(summary_rows)
    proposal = _load_proposal(repo_root, work_item)
    evaluation_mode = _effective_evaluation_mode(repo_root, work_item)
    comparison_role = _effective_comparison_role(repo_root, work_item)
    proposal_assessment, evaluation_record, proposal_source_refs = _build_proposal_assessment(
        session=session,
        work_item=work_item,
        repo_root=repo_root,
        proposal=proposal,
        summary_rows=summary_rows,
    )
    if evaluation_mode == "paired_comparison" and comparison_role == "candidate":
        if proposal_assessment is None or evaluation_record is None:
            raise Layer2ResultConsumerError(
                "paired comparison candidate did not serialize proposal assessment/evaluation record"
            )
        if str((proposal_assessment or {}).get("outcome", "")).strip() == "unavailable":
            raise Layer2ResultConsumerError(
                "paired comparison candidate baseline could not be resolved"
            )
        if not str((proposal_assessment or {}).get("baseline_item_id", "")).strip():
            raise Layer2ResultConsumerError(
                "paired comparison candidate did not serialize baseline_item_id"
            )
        if not str((evaluation_record or {}).get("abstraction_layer", "")).strip():
            raise Layer2ResultConsumerError(
                "paired comparison candidate did not serialize abstraction_layer"
            )
    focused_result_rows = _select_focused_result_rows(
        results_rows,
        arch_id=str((best_point.get("best") or {}).get("arch_id") or summary_best.get("arch_id") or "").strip(),
        macro_mode=str((best_point.get("best") or {}).get("macro_mode") or summary_best.get("macro_mode") or "").strip(),
    )
    objective_profiles: list[dict[str, Any]] = []
    objective_sweep_exists = False
    if objective_sweep_rel:
        objective_sweep_path = _resolve_path(repo_root=repo_root, path_text=objective_sweep_rel)
        if objective_sweep_path.exists():
            objective_sweep_exists = True
            objective_profiles = _profile_recommendations(_load_csv(objective_sweep_path))

    payload = _build_payload(
        repo_root=repo_root,
        work_item=work_item,
        run=run,
        best_point=best_point,
        summary_best=summary_best,
        objective_profiles=objective_profiles,
        evaluation_record=evaluation_record,
        proposal_assessment=proposal_assessment,
        source_refs={
            "best_point_json": best_point_rel,
            "summary_csv": summary_rel,
            "results_csv": results_rel,
            "report_md": report_rel,
            **_focused_artifact_refs(focused_result_rows[0] if focused_result_rows else None),
            **_focused_model_artifact_refs(focused_result_rows),
            **proposal_source_refs,
            **({"objective_sweep_csv": objective_sweep_rel} if objective_sweep_exists else {}),
        },
    )

    recommended_arch_id = str(payload["recommendation"].get("arch_id", "")).strip()
    recommended_macro_mode = str(payload["recommendation"].get("macro_mode", "")).strip()
    if not recommended_arch_id or not recommended_macro_mode:
        raise Layer2ResultConsumerError(f"could not derive recommended point for work item: {work_item.item_id}")

    target_rel = request.target_path or _default_target_path(item_id=work_item.item_id)
    target_path = _resolve_path(repo_root=repo_root, path_text=target_rel)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    _upsert_artifact(session, run=run, target_path=str(target_path.relative_to(repo_root)), payload=payload)
    work_item.state = WorkItemState.ARTIFACT_SYNC
    session.add(
        RunEvent(
            run_id=run.id,
            event_time=utcnow(),
            event_type="l2_decision_proposed",
            event_payload={
                "target_path": str(target_path.relative_to(repo_root)),
                "recommended_arch_id": recommended_arch_id,
                "recommended_macro_mode": recommended_macro_mode,
                "profile_count": len(objective_profiles),
            },
        )
    )
    session.commit()
    return Layer2ConsumeResult(
        item_id=work_item.item_id,
        run_key=run.run_key,
        target_path=str(target_path),
        recommended_arch_id=recommended_arch_id,
        recommended_macro_mode=recommended_macro_mode,
        profile_count=len(objective_profiles),
        work_item_state=work_item.state.value,
    )
