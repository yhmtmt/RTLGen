"""Layer 1 result consumption helpers."""

from __future__ import annotations

import csv
from collections import Counter
from dataclasses import dataclass
from datetime import timezone
import hashlib
import json
from pathlib import Path
import re
import statistics
from typing import Any

from sqlalchemy.orm import Session

from control_plane.clock import utcnow
from control_plane.models.artifacts import Artifact
from control_plane.models.enums import ArtifactStorageMode, RunStatus, WorkItemState
from control_plane.models.run_events import RunEvent
from control_plane.models.runs import Run
from control_plane.models.work_items import WorkItem
from control_plane.services.docs_paths import resolve_proposal_file


class Layer1ResultConsumerError(RuntimeError):
    pass


@dataclass(frozen=True)
class Layer1ConsumeRequest:
    repo_root: str
    item_id: str | None = None
    run_key: str | None = None
    target_path: str | None = None


@dataclass(frozen=True)
class Layer1ConsumeResult:
    item_id: str
    run_key: str
    target_path: str
    proposal_count: int
    work_item_state: str


def _default_target_path(*, item_id: str) -> str:
    return f"control_plane/shadow_exports/l1_promotions/{item_id}.json"


def _resolve_path(*, repo_root: Path, path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return repo_root / path


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_run(session: Session, request: Layer1ConsumeRequest) -> tuple[WorkItem, Run]:
    if request.run_key:
        run = session.query(Run).filter(Run.run_key == request.run_key).one_or_none()
        if run is None:
            raise Layer1ResultConsumerError(f"run not found: {request.run_key}")
        return run.work_item, run
    if not request.item_id:
        raise Layer1ResultConsumerError("item_id or run_key is required")
    work_item = session.query(WorkItem).filter(WorkItem.item_id == request.item_id).one_or_none()
    if work_item is None:
        raise Layer1ResultConsumerError(f"work item not found: {request.item_id}")
    if not work_item.runs:
        raise Layer1ResultConsumerError(f"work item has no runs: {request.item_id}")
    successful_runs = [row for row in work_item.runs if row.status == RunStatus.SUCCEEDED]
    if successful_runs:
        run = sorted(successful_runs, key=lambda row: (row.attempt, row.created_at or utcnow()))[-1]
    else:
        run = sorted(work_item.runs, key=lambda row: (row.attempt, row.created_at or utcnow()))[-1]
    return work_item, run


def _safe_float(value: str | None) -> float | None:
    if value in ("", None):
        return None
    try:
        return float(str(value).strip())
    except ValueError:
        return None


def _row_sort_key(row: dict[str, Any]) -> tuple[float, float, float, str, str]:
    cp = _safe_float(row.get("critical_path_ns"))
    area = _safe_float(row.get("die_area"))
    power = _safe_float(row.get("total_power_mw"))
    return (
        cp if cp is not None else float("inf"),
        area if area is not None else float("inf"),
        power if power is not None else float("inf"),
        str(row.get("param_hash", "")),
        str(row.get("tag", "")),
    )


def _objective_name(work_item: WorkItem) -> str:
    payload = dict(work_item.task_request.request_payload or {})
    objective = str(payload.get("objective", "")).strip()
    if objective:
        return objective
    return str(work_item.task_request.description or "").strip()


def _load_metrics_rows(path: Path) -> list[dict[str, str]]:
    # Match the tolerant parsing used by scripts/build_runs_index.py because
    # historical metrics.csv rows may carry unquoted JSON in params_json.
    text = path.read_text(encoding="utf-8", errors="ignore")
    text = re.sub(r"result\.json(?=[A-Za-z0-9_])", "result.json\n", text)
    lines = text.splitlines()
    if not lines:
        return []

    csv_reader = csv.DictReader(lines)
    csv_rows = list(csv_reader)
    good_csv_rows = [row for row in csv_rows if None not in row]
    if csv_reader.fieldnames and good_csv_rows and len(good_csv_rows) == len(csv_rows):
        return [{str(key): str(value or "") for key, value in row.items()} for row in good_csv_rows]

    header = lines[0].split(",")
    rows: list[dict[str, str]] = [{str(key): str(value or "") for key, value in row.items()} for row in good_csv_rows]
    prefix_len = max(len(header) - 2, 0)
    for line in lines[1:]:
        if not line.strip():
            continue
        parts = line.split(",", prefix_len)
        if len(parts) < prefix_len + 1:
            continue
        front = parts[:prefix_len]
        rest = parts[prefix_len]
        if "," in rest:
            params_json, result_path = rest.rsplit(",", 1)
        else:
            params_json, result_path = rest, ""
        params_json = params_json.strip()
        if len(params_json) >= 2 and params_json[0] == '"' and params_json[-1] == '"':
            params_json = params_json[1:-1].replace('""', '"')
        values = front + [params_json, result_path]
        if len(values) != len(header):
            continue
        rows.append(dict(zip(header, values)))
    return rows


def _work_item_make_target(work_item: WorkItem) -> str:
    for command in work_item.command_manifest or []:
        if str(command.get("name", "")).strip() != "run_block_sweep":
            continue
        run_text = str(command.get("run", ""))
        match = re.search(r"--make_target\s+(\S+)", run_text)
        if match:
            return match.group(1).strip()
    return ""


def _row_has_physical_metrics(row: dict[str, Any]) -> bool:
    return any(_safe_float(row.get(key)) is not None for key in ("critical_path_ns", "die_area", "total_power_mw"))


def _developer_loop_payload(work_item: WorkItem) -> dict[str, Any]:
    payload = dict(work_item.task_request.request_payload or {})
    developer_loop = payload.get("developer_loop")
    return dict(developer_loop) if isinstance(developer_loop, dict) else {}


def _load_proposal(repo_root: Path, work_item: WorkItem) -> dict[str, Any] | None:
    developer_loop = _developer_loop_payload(work_item)
    if not isinstance(developer_loop, dict):
        return None
    proposal_path_text = str(developer_loop.get("proposal_path", "")).strip()
    if not proposal_path_text:
        return None
    proposal_file = resolve_proposal_file(repo_root, proposal_path=proposal_path_text)
    if proposal_file is None:
        return None
    if not proposal_file.exists():
        return None
    try:
        return _load_json(proposal_file)
    except Exception:
        return None


def _inferred_l1_abstraction_layer(repo_root: Path, work_item: WorkItem) -> str:
    input_manifest = dict(work_item.input_manifest or {})
    configs = input_manifest.get("configs")
    if isinstance(configs, list):
        for config_text in configs:
            config_path = _resolve_path(repo_root=repo_root, path_text=str(config_text))
            if not config_path.exists():
                continue
            try:
                cfg = _load_json(config_path)
            except Exception:
                continue
            if "top_name" in cfg and "compute" in cfg:
                return "architecture_block"
            if any(key in cfg for key in ("multiplier", "multiplier_yosys", "adder")):
                return "circuit_block"
            operations = cfg.get("operations")
            if isinstance(operations, list) and len(operations) == 1:
                op_type = str((operations[0] or {}).get("type", "")).strip()
                if op_type in {"activation", "softmax_rowwise"}:
                    return "circuit_block"
    expected_outputs = [str(path_text) for path_text in (work_item.expected_outputs or [])]
    joined = "\n".join(expected_outputs)
    if "runs/designs/npu_blocks/" in joined:
        return "architecture_block"
    if any(
        marker in joined
        for marker in (
            "runs/designs/activations/",
            "runs/designs/prefix_adders/",
            "runs/designs/multipliers/",
            "runs/designs/adders/",
            "runs/designs/trials/",
        )
    ):
        return "circuit_block"
    return ""


def _developer_loop_abstraction_layer(repo_root: Path, work_item: WorkItem) -> str:
    developer_loop = _developer_loop_payload(work_item)
    abstraction = developer_loop.get("abstraction")
    if isinstance(abstraction, dict):
        layer = str(abstraction.get("layer", "")).strip()
        if layer:
            return layer
    evaluation = developer_loop.get("evaluation")
    if isinstance(evaluation, dict):
        layer = str(evaluation.get("abstraction_layer", "")).strip()
        if layer:
            return layer
    proposal = _load_proposal(repo_root, work_item)
    if isinstance(proposal, dict):
        layer = str(proposal.get("abstraction_layer", "")).strip()
        if layer:
            return layer
    payload = dict(work_item.task_request.request_payload or {})
    layer = str(payload.get("abstraction_layer", "")).strip()
    if layer:
        return layer
    return _inferred_l1_abstraction_layer(repo_root, work_item)


def _effective_evaluation_record(*, repo_root: Path, work_item: WorkItem, best_row: dict[str, Any]) -> dict[str, Any]:
    payload = dict(work_item.task_request.request_payload or {})
    developer_loop = payload.get("developer_loop") if isinstance(payload.get("developer_loop"), dict) else {}
    evaluation = developer_loop.get("evaluation") if isinstance(developer_loop.get("evaluation"), dict) else {}
    mode = str(evaluation.get("mode", "")).strip()
    make_target = _work_item_make_target(work_item)
    has_physical_metrics = _row_has_physical_metrics(best_row)
    if not mode:
        if make_target and not has_physical_metrics:
            mode = "synth_prefilter"
        else:
            mode = "measurement_only"
    summary = ""
    result_kind = "physical_metrics"
    if mode == "synth_prefilter":
        result_kind = "synth_prefilter"
        target_text = make_target or str(best_row.get("result_path", "")).strip()
        summary = (
            "Synth-stage prefilter passed"
            + (f" at `{target_text}`" if target_text else "")
            + "; no physical metrics are recorded yet."
        )
    else:
        summary = "Physical metrics recorded from an accepted status=ok Layer 1 row."
    return {
        "evaluation_mode": mode,
        "abstraction_layer": _developer_loop_abstraction_layer(repo_root, work_item),
        "result_kind": result_kind,
        "physical_metrics_present": has_physical_metrics,
        "summary": summary,
    }


def _best_metrics_row(*, repo_root: Path, metrics_csv: str) -> dict[str, Any] | None:
    path = _resolve_path(repo_root=repo_root, path_text=metrics_csv)
    if not path.exists():
        return None
    rows: list[dict[str, Any]] = []
    for row in _load_metrics_rows(path):
        if str(row.get("status", "")).strip() != "ok":
            continue
        rows.append(dict(row))
    if not rows:
        return None
    return sorted(rows, key=_row_sort_key)[0]


def _proposal_entry(*, metrics_csv: str, best_row: dict[str, Any], evaluation_record: dict[str, Any]) -> dict[str, Any]:
    proposal: dict[str, Any] = {
        "metrics_ref": {
            "metrics_csv": metrics_csv,
            "platform": str(best_row.get("platform", "")).strip(),
            "status": str(best_row.get("status", "")).strip(),
            "result_kind": str(evaluation_record.get("result_kind", "physical_metrics")).strip(),
        },
        "selection_reason": (
            "lowest critical_path_ns, then die_area, then total_power_mw among status=ok rows"
            if str(evaluation_record.get("result_kind", "")) != "synth_prefilter"
            else "first status=ok synth-stage prefilter row; no physical metrics are recorded yet"
        ),
    }
    for key in ("param_hash", "tag", "run_id", "sample_id", "batch_id", "result_path", "work_result_json"):
        value = str(best_row.get(key, "")).strip()
        if value:
            proposal["metrics_ref"][key] = value

    summary: dict[str, Any] = {}
    for key in ("critical_path_ns", "die_area", "total_power_mw"):
        value = _safe_float(best_row.get(key))
        if value is not None:
            summary[key] = value
    if summary:
        proposal["metric_summary"] = summary
    return proposal


def _completed_trial_runs(work_item: WorkItem) -> list[Run]:
    completed: list[Run] = []
    for run in sorted(work_item.runs, key=lambda row: (row.attempt, row.created_at or utcnow())):
        if run.status not in {RunStatus.SUCCEEDED, RunStatus.FAILED, RunStatus.CANCELED, RunStatus.TIMED_OUT}:
            continue
        payload = dict(run.result_payload or {}) if isinstance(run.result_payload, dict) else {}
        if bool((payload.get("retry_decision") or {}).get("requeue")):
            continue
        completed.append(run)
    return completed


def _metrics_csvs_from_run(run: Run, *, work_item: WorkItem | None = None) -> list[str]:
    payload = dict(run.result_payload or {}) if isinstance(run.result_payload, dict) else {}
    queue_result = dict(payload.get("queue_result") or {})
    result: list[str] = []
    for ref in queue_result.get("metrics_rows") or []:
        rel_path = str(ref).split(":", 1)[0].strip()
        if not rel_path or rel_path == "runs/index.csv" or not rel_path.endswith("metrics.csv"):
            continue
        if rel_path not in result:
            result.append(rel_path)
    if not result and work_item is not None:
        for rel_path in work_item.expected_outputs or []:
            rel_path = str(rel_path).strip()
            if not rel_path or rel_path == "runs/index.csv" or not rel_path.endswith("metrics.csv"):
                continue
            if rel_path not in result:
                result.append(rel_path)
    if run.trial_index:
        trial_marker = f"/trial_{int(run.trial_index):03d}/"
        trial_scoped = [rel_path for rel_path in result if trial_marker in rel_path]
        if trial_scoped:
            return trial_scoped
    return result


def _best_trial_row(repo_root: Path, run: Run) -> tuple[str, dict[str, Any]] | None:
    candidates: list[tuple[str, dict[str, Any]]] = []
    for metrics_csv in _metrics_csvs_from_run(run, work_item=run.work_item):
        best_row = _best_metrics_row(repo_root=repo_root, metrics_csv=metrics_csv)
        if best_row is None:
            continue
        candidates.append((metrics_csv, best_row))
    if not candidates:
        return None
    candidates.sort(key=lambda item: _row_sort_key(item[1]))
    return candidates[0]


def _ok_trial_rows(repo_root: Path, run: Run) -> list[tuple[str, dict[str, Any]]]:
    candidates: list[tuple[str, dict[str, Any]]] = []
    for metrics_csv in _metrics_csvs_from_run(run, work_item=run.work_item):
        metrics_path = _resolve_path(repo_root=repo_root, path_text=metrics_csv)
        if not metrics_path.exists():
            continue
        for row in _load_metrics_rows(metrics_path):
            if str(row.get("status", "")).strip() != "ok":
                continue
            candidates.append((metrics_csv, dict(row)))
    return candidates


def _metric_summary(values: list[float]) -> dict[str, float] | None:
    if not values:
        return None
    stddev = 0.0 if len(values) == 1 else float(statistics.pstdev(values))
    return {
        "best": min(values),
        "mean": float(statistics.fmean(values)),
        "median": float(statistics.median(values)),
        "max": max(values),
        "range": max(values) - min(values),
        "stddev": stddev,
    }


def _trial_artifact_paths(item_id: str) -> dict[str, str]:
    base = f"control_plane/shadow_exports/l1_trials/{item_id}"
    return {
        "summary_stats": f"{base}/summary_stats.json",
        "failure_stats": f"{base}/failure_stats.json",
        "trial_table": f"{base}/trial_table.csv",
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _write_trial_table(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "run_key", "attempt", "trial_index", "seed", "status", "metrics_csv",
        "critical_path_ns", "die_area", "total_power_mw",
        "failure_category", "failure_stage", "failure_signature",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def _upsert_repo_artifact(session: Session, *, run: Run, kind: str, path: str, metadata: dict[str, Any], repo_root: Path) -> None:
    artifact = session.query(Artifact).filter(Artifact.run_id == run.id, Artifact.kind == kind).one_or_none()
    rel_path = str(path)
    abs_path = repo_root / rel_path
    sha = hashlib.sha256(abs_path.read_bytes()).hexdigest() if abs_path.exists() else None
    if artifact is None:
        artifact = Artifact(
            run_id=run.id,
            kind=kind,
            storage_mode=ArtifactStorageMode.REPO,
            path=rel_path,
            sha256=sha,
            metadata_=metadata,
        )
        session.add(artifact)
    else:
        artifact.storage_mode = ArtifactStorageMode.REPO
        artifact.path = rel_path
        artifact.sha256 = sha
        artifact.metadata_ = metadata


def _normalized_seed_variance_params(row: dict[str, Any]) -> str | None:
    params_text = str(row.get("params_json", "")).strip()
    if not params_text:
        return None
    try:
        params = json.loads(params_text)
    except Exception:
        return None
    if not isinstance(params, dict):
        return None
    comparable = {
        str(key): value
        for key, value in params.items()
        if str(key) not in {"FLOW_RANDOM_SEED", "TAG"}
    }
    return json.dumps(comparable, sort_keys=True, separators=(",", ":"))


def _seed_variance_match_key(metrics_csv: str, row: dict[str, Any]) -> str:
    design = str(row.get("design", "")).strip()
    platform = str(row.get("platform", "")).strip()
    config_hash = str(row.get("config_hash", "")).strip()
    normalized_params = _normalized_seed_variance_params(row)
    if normalized_params:
        return "|".join((design, platform, config_hash, normalized_params))
    metrics_key = re.sub(r"/trials/trial_\d+/", "/trials/*/", metrics_csv)
    fallback = str(row.get("tag", "")).strip() or str(row.get("param_hash", "")).strip()
    return "|".join((metrics_key, platform, config_hash, fallback))


def _select_seed_variance_rows(
    repo_root: Path,
    work_item: WorkItem,
    completed: list[Run],
) -> tuple[dict[str, tuple[str, dict[str, Any]]], dict[str, Any] | None]:
    grouped: dict[str, list[tuple[Run, str, dict[str, Any]]]] = {}
    for run in completed:
        if run.status != RunStatus.SUCCEEDED:
            continue
        seen_keys: set[str] = set()
        for metrics_csv, row in _ok_trial_rows(repo_root, run):
            key = _seed_variance_match_key(metrics_csv, row)
            if key in seen_keys:
                continue
            seen_keys.add(key)
            grouped.setdefault(key, []).append((run, metrics_csv, row))

    candidates: list[tuple[tuple[Any, ...], dict[str, Any]]] = []
    for key, entries in grouped.items():
        distinct_runs = {entry[0].run_key for entry in entries}
        if len(distinct_runs) < 2:
            continue
        cp_values = [
            value
            for value in (_safe_float(entry[2].get("critical_path_ns")) for entry in entries)
            if value is not None
        ]
        area_values = [
            value
            for value in (_safe_float(entry[2].get("die_area")) for entry in entries)
            if value is not None
        ]
        power_values = [
            value
            for value in (_safe_float(entry[2].get("total_power_mw")) for entry in entries)
            if value is not None
        ]
        sort_key = (
            -len(distinct_runs),
            float(statistics.fmean(cp_values)) if cp_values else float("inf"),
            float(statistics.fmean(area_values)) if area_values else float("inf"),
            float(statistics.fmean(power_values)) if power_values else float("inf"),
            key,
        )
        representative = sorted(((metrics_csv, row) for _run, metrics_csv, row in entries), key=lambda item: _row_sort_key(item[1]))[0]
        candidates.append(
            (
                sort_key,
                {
                    "key": key,
                    "entries": entries,
                    "representative": representative,
                },
            )
        )

    if not candidates:
        return {}, None
    _sort_key, selected = sorted(candidates, key=lambda item: item[0])[0]
    matched = {
        run.run_key: (metrics_csv, row)
        for run, metrics_csv, row in selected["entries"]
    }
    representative_metrics_csv, representative_row = selected["representative"]
    metadata = {
        "match_key": selected["key"],
        "matched_run_count": len(matched),
        "representative_metrics_csv": representative_metrics_csv,
        "representative_row": representative_row,
        "comparison_mode": "same_non_seed_flow_params",
    }
    normalized_params = _normalized_seed_variance_params(representative_row)
    if normalized_params:
        metadata["comparison_params"] = json.loads(normalized_params)
    return matched, metadata


def _trial_aggregate_payloads(repo_root: Path, work_item: WorkItem) -> tuple[list[str], dict[str, Any], dict[str, Any], list[dict[str, Any]], dict[str, Any] | None]:
    completed = _completed_trial_runs(work_item)
    metrics_csvs: list[str] = []
    trial_rows: list[dict[str, Any]] = []
    success_metric_values = {"critical_path_ns": [], "die_area": [], "total_power_mw": []}
    failure_category = Counter()
    failure_stage = Counter()
    success_count = 0
    seed_variance_selected_rows: dict[str, tuple[str, dict[str, Any]]] = {}
    selected_group_metadata: dict[str, Any] | None = None
    if _objective_name(work_item) == "measure_seed_variance":
        seed_variance_selected_rows, selected_group_metadata = _select_seed_variance_rows(repo_root, work_item, completed)
    for run in completed:
        payload = dict(run.result_payload or {}) if isinstance(run.result_payload, dict) else {}
        trial = dict(payload.get("trial") or {})
        failure = dict(payload.get("failure_classification") or {})
        run_metrics_csvs = _metrics_csvs_from_run(run, work_item=work_item) if run.status == RunStatus.SUCCEEDED else []
        for metrics_csv in run_metrics_csvs:
            if metrics_csv not in metrics_csvs:
                metrics_csvs.append(metrics_csv)
        if run.status == RunStatus.SUCCEEDED and seed_variance_selected_rows:
            best = seed_variance_selected_rows.get(run.run_key)
        else:
            best = _best_trial_row(repo_root, run) if run.status == RunStatus.SUCCEEDED else None
        metrics_csv = ""
        best_row = None
        if best is not None:
            metrics_csv, best_row = best
            success_count += 1
            for key in success_metric_values:
                value = _safe_float(best_row.get(key))
                if value is not None:
                    success_metric_values[key].append(value)
        else:
            category = str(failure.get("category", "") or run.failure_category or "unknown").strip() or "unknown"
            stage = str(failure.get("stage", "") or run.failure_stage or "unknown").strip() or "unknown"
            failure_category[category] += 1
            failure_stage[stage] += 1
        trial_rows.append({
            "run_key": run.run_key,
            "attempt": run.attempt,
            "trial_index": trial.get("trial_index", run.trial_index or ""),
            "seed": trial.get("seed", run.seed or ""),
            "status": run.status.value,
            "metrics_csv": metrics_csv,
            "critical_path_ns": _safe_float(best_row.get("critical_path_ns")) if best_row else "",
            "die_area": _safe_float(best_row.get("die_area")) if best_row else "",
            "total_power_mw": _safe_float(best_row.get("total_power_mw")) if best_row else "",
            "failure_category": str(failure.get("category", "") or run.failure_category or "").strip(),
            "failure_stage": str(failure.get("stage", "") or run.failure_stage or "").strip(),
            "failure_signature": str(failure.get("signature", "") or run.failure_signature or "").strip(),
        })

    completed_trials = len(completed)
    failure_count = completed_trials - success_count
    summary_stats = {
        "item_id": work_item.item_id,
        "completed_trials": completed_trials,
        "success_count": success_count,
        "failure_count": failure_count,
        "success_rate": (float(success_count) / float(completed_trials)) if completed_trials else 0.0,
        "metrics": {key: value for key, value in {metric: _metric_summary(values) for metric, values in success_metric_values.items()}.items() if value is not None},
    }
    if selected_group_metadata is not None:
        summary_stats["comparison_mode"] = selected_group_metadata["comparison_mode"]
        if "comparison_params" in selected_group_metadata:
            summary_stats["comparison_params"] = selected_group_metadata["comparison_params"]
    failure_stats = {
        "item_id": work_item.item_id,
        "completed_trials": completed_trials,
        "success_count": success_count,
        "failure_count": failure_count,
        "by_category": dict(failure_category),
        "by_stage": dict(failure_stage),
    }
    if selected_group_metadata is not None:
        failure_stats["comparison_mode"] = selected_group_metadata["comparison_mode"]
    return metrics_csvs, summary_stats, failure_stats, trial_rows, selected_group_metadata


def _build_payload(*, work_item: WorkItem, run: Run, proposals: list[dict[str, Any]], evaluation_record: dict[str, Any], source_refs: dict[str, Any] | None = None) -> dict[str, Any]:
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
        "objective": work_item.task_request.description,
        "input_manifest": work_item.input_manifest,
        "proposal_count": len(proposals),
        "evaluation_record": evaluation_record,
        "proposal_assessment": None,
        "proposals": proposals,
        "trial_summary": None,
        "source_refs": source_refs or {},
    }


def _upsert_artifact(session: Session, *, run: Run, target_path: str, payload: dict[str, Any]) -> None:
    artifact = (
        session.query(Artifact)
        .filter(Artifact.run_id == run.id, Artifact.kind == "promotion_proposal")
        .one_or_none()
    )
    sha256 = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    if artifact is None:
        artifact = Artifact(
            run_id=run.id,
            kind="promotion_proposal",
            storage_mode=ArtifactStorageMode.REPO,
            path=target_path,
            sha256=sha256,
            metadata_={"proposal_count": len(payload.get("proposals") or [])},
        )
        session.add(artifact)
    else:
        artifact.storage_mode = ArtifactStorageMode.REPO
        artifact.path = target_path
        artifact.sha256 = sha256
        artifact.metadata_ = {"proposal_count": len(payload.get("proposals") or [])}


def consume_l1_result(session: Session, request: Layer1ConsumeRequest) -> Layer1ConsumeResult:
    repo_root = Path(request.repo_root).resolve()
    work_item, run = _resolve_run(session, request)
    if work_item.task_type != "l1_sweep":
        raise Layer1ResultConsumerError(f"work item is not l1_sweep: {work_item.item_id}")
    if run.status != RunStatus.SUCCEEDED:
        raise Layer1ResultConsumerError(f"run is not succeeded: {run.run_key} status={run.status.value}")

    metrics_csvs, summary_stats, failure_stats, trial_rows, selected_group_metadata = _trial_aggregate_payloads(repo_root, work_item)
    proposals: list[dict[str, Any]] = []
    evaluation_record: dict[str, Any] | None = None
    if selected_group_metadata and selected_group_metadata.get("representative_row"):
        metrics_csv = str(selected_group_metadata["representative_metrics_csv"])
        best_row = dict(selected_group_metadata["representative_row"])
        row_evaluation = _effective_evaluation_record(repo_root=repo_root, work_item=work_item, best_row=best_row)
        evaluation_record = row_evaluation
        proposals.append(
            _proposal_entry(
                metrics_csv=metrics_csv,
                best_row=best_row,
                evaluation_record=row_evaluation,
            )
        )
    else:
        for metrics_csv in metrics_csvs:
            best_row = _best_metrics_row(repo_root=repo_root, metrics_csv=metrics_csv)
            if best_row is None:
                continue
            row_evaluation = _effective_evaluation_record(repo_root=repo_root, work_item=work_item, best_row=best_row)
            if evaluation_record is None:
                evaluation_record = row_evaluation
            proposals.append(
                _proposal_entry(
                    metrics_csv=metrics_csv,
                    best_row=best_row,
                    evaluation_record=row_evaluation,
                )
            )

    if not proposals or evaluation_record is None:
        raise Layer1ResultConsumerError(f"no status=ok metrics rows found for work item: {work_item.item_id}")

    trial_paths = _trial_artifact_paths(work_item.item_id)
    source_refs = {
        "trial_metrics_csvs": metrics_csvs,
        "summary_stats_json": trial_paths["summary_stats"],
        "failure_stats_json": trial_paths["failure_stats"],
        "trial_table_csv": trial_paths["trial_table"],
    }
    payload = _build_payload(
        work_item=work_item,
        run=run,
        proposals=proposals,
        evaluation_record=evaluation_record,
        source_refs=source_refs,
    )
    payload["trial_summary"] = summary_stats
    target_rel = request.target_path or _default_target_path(item_id=work_item.item_id)
    target_path = _resolve_path(repo_root=repo_root, path_text=target_rel)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    summary_path = _resolve_path(repo_root=repo_root, path_text=trial_paths["summary_stats"])
    failure_path = _resolve_path(repo_root=repo_root, path_text=trial_paths["failure_stats"])
    trial_table_path = _resolve_path(repo_root=repo_root, path_text=trial_paths["trial_table"])
    _write_json(summary_path, summary_stats)
    _write_json(failure_path, failure_stats)
    _write_trial_table(trial_table_path, trial_rows)

    _upsert_artifact(session, run=run, target_path=str(target_path.relative_to(repo_root)), payload=payload)
    _upsert_repo_artifact(session, run=run, kind="summary_stats", path=str(summary_path.relative_to(repo_root)), metadata={"completed_trials": summary_stats["completed_trials"]}, repo_root=repo_root)
    _upsert_repo_artifact(session, run=run, kind="failure_stats", path=str(failure_path.relative_to(repo_root)), metadata={"failure_count": failure_stats["failure_count"]}, repo_root=repo_root)
    _upsert_repo_artifact(session, run=run, kind="trial_table", path=str(trial_table_path.relative_to(repo_root)), metadata={"row_count": len(trial_rows)}, repo_root=repo_root)
    work_item.state = WorkItemState.ARTIFACT_SYNC
    session.add(
        RunEvent(
            run_id=run.id,
            event_time=utcnow(),
            event_type="l1_promotion_proposed",
            event_payload={
                "target_path": str(target_path.relative_to(repo_root)),
                "proposal_count": len(proposals),
                "completed_trials": summary_stats["completed_trials"],
                "success_count": summary_stats["success_count"],
            },
        )
    )
    session.commit()
    return Layer1ConsumeResult(
        item_id=work_item.item_id,
        run_key=run.run_key,
        target_path=str(target_path),
        proposal_count=len(proposals),
        work_item_state=work_item.state.value,
    )
