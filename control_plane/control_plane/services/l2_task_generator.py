"""Layer 2 task generation helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timezone
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from control_plane.clock import utcnow
from control_plane.models.enums import FlowName, LayerName, WorkItemState
from control_plane.models.task_requests import TaskRequest
from control_plane.models.work_items import WorkItem


class Layer2TaskGenerationError(RuntimeError):
    pass


@dataclass(frozen=True)
class Layer2CampaignGenerateRequest:
    repo_root: str
    campaign_path: str
    platform: str | None = None
    requested_by: str = "control_plane"
    priority: int = 1
    item_id: str | None = None
    title: str | None = None
    objective: str | None = None
    source_commit: str | None = None
    mode: str = "upsert"
    run_physical: bool = True
    jobs: int = 2
    batch_id: str | None = None
    objective_profiles_json: str | None = None


@dataclass(frozen=True)
class Layer2TaskGenerateResult:
    item_id: str
    status: str
    work_item_id: str
    task_request_id: str


def _repo_rel(path_text: str, repo_root: Path) -> str:
    path = Path(path_text)
    if path.is_absolute():
        try:
            return str(path.resolve().relative_to(repo_root.resolve()))
        except ValueError as exc:
            raise Layer2TaskGenerationError(f"path is outside repo_root: {path_text}") from exc
    return str(path)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _uniq(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered


def _default_item_id(*, campaign_path: str, platform: str) -> str:
    stem = Path(campaign_path).stem
    digest = sha256(json.dumps([campaign_path, platform], sort_keys=True).encode("utf-8")).hexdigest()[:8]
    return f"l2_campaign_{stem}_{platform}_{digest}"


def _default_title(*, campaign_id: str, platform: str) -> str:
    return f"Layer2 campaign {campaign_id} on {platform}"


def _default_objective(*, campaign: dict[str, Any]) -> str:
    description = str(campaign.get("description", "")).strip()
    if description:
        return description
    return f"Execute Layer2 campaign {campaign.get('campaign_id', 'unknown_campaign')}."


def _build_inputs(*, campaign: dict[str, Any]) -> dict[str, list[str]]:
    arch_points = campaign.get("architecture_points") or []
    configs = _uniq([str(point.get("rtlgen_config", "")).strip() for point in arch_points if point.get("rtlgen_config")])
    design_dirs = _uniq([str(point.get("synth_design_dir", "")).strip() for point in arch_points if point.get("synth_design_dir")])
    sweeps = _uniq([str(point.get("sweep_file", "")).strip() for point in arch_points if point.get("sweep_file")])
    macro_manifests = _uniq([str(point.get("macro_manifest", "")).strip() for point in arch_points if point.get("macro_manifest")])
    candidate_manifests = _uniq(
        [
            str((point.get("layer1_modules") or {}).get("manifest", "")).strip()
            for point in arch_points
            if (point.get("layer1_modules") or {}).get("manifest")
        ]
    )
    return {
        "configs": configs,
        "design_dirs": design_dirs,
        "sweeps": sweeps,
        "macro_manifests": macro_manifests,
        "candidate_manifests": candidate_manifests,
    }


def _build_expected_outputs(
    *,
    campaign: dict[str, Any],
    generated_campaign_path: str,
    include_objective_sweep: bool,
) -> list[str]:
    outputs = campaign.get("outputs") or {}
    campaign_dir = str(outputs.get("campaign_dir", "")).strip()
    expected: list[str] = [generated_campaign_path]
    for key in ("results_csv", "report_md"):
        value = str(outputs.get(key, "")).strip()
        if value:
            expected.append(value)
    if campaign_dir:
        expected.extend(
            [
                f"{campaign_dir}/summary.csv",
                f"{campaign_dir}/pareto.csv",
                f"{campaign_dir}/best_point.json",
            ]
        )
        if include_objective_sweep:
            expected.extend(
                [
                    f"{campaign_dir}/objective_sweep.csv",
                    f"{campaign_dir}/objective_sweep.md",
                ]
            )

    for point in campaign.get("architecture_points") or []:
        design_dir = str(point.get("synth_design_dir", "")).strip()
        if design_dir:
            expected.append(f"{design_dir}/metrics.csv")
    return _uniq(expected)


def _with_fresh_outputs(*, campaign: dict[str, Any], item_id: str) -> dict[str, Any]:
    cloned = json.loads(json.dumps(campaign))
    outputs = dict(cloned.get("outputs") or {})
    campaign_dir = str(outputs.get("campaign_dir", "")).strip()
    if not campaign_dir:
        raise Layer2TaskGenerationError("campaign outputs.campaign_dir is required")
    base_dir = Path(campaign_dir)
    fresh_dir = base_dir.parent / f"{base_dir.name}__{item_id}"
    outputs["campaign_dir"] = str(fresh_dir)
    outputs["results_csv"] = str(fresh_dir / "results.csv")
    outputs["report_md"] = str(fresh_dir / "report.md")
    cloned["outputs"] = outputs
    return cloned


def _build_payload(
    *,
    item_id: str,
    title: str,
    objective: str,
    requested_by: str,
    priority: int,
    platform: str,
    campaign_path: str,
    generated_campaign_path: str,
    generated_outputs: dict[str, Any],
    model_manifest: str | None,
    inputs: dict[str, list[str]],
    expected_outputs: list[str],
    run_physical: bool,
    jobs: int,
    batch_id: str,
    objective_profiles_json: str | None,
) -> dict[str, Any]:
    commands: list[dict[str, str]] = []
    if model_manifest:
        commands.append(
            {
                "name": "fetch_models",
                "run": f"python3 npu/eval/fetch_models.py --manifest {model_manifest}",
            }
        )
    commands.extend(
        [
            {
                "name": "validate_campaign",
                "run": f"python3 npu/eval/validate.py --campaign {generated_campaign_path} --check_paths",
            },
            {
                "name": "run_campaign",
                "run": (
                    f"python3 npu/eval/run_campaign.py --campaign {generated_campaign_path} "
                    + ("--run_physical " if run_physical else "")
                    + f"--jobs {jobs} --batch_id {batch_id}"
                ).strip(),
            },
            {
                "name": "report_campaign",
                "run": f"python3 npu/eval/report_campaign.py --campaign {generated_campaign_path}",
            },
        ]
    )
    if objective_profiles_json:
        commands.append(
            {
                "name": "objective_sweep",
                "run": f"python3 npu/eval/optimize_campaign.py --campaign {generated_campaign_path} --profiles_json {objective_profiles_json}",
            }
        )
    commands.append(
        {
            "name": "validate_runs",
            "run": "python3 scripts/validate_runs.py --skip_eval_queue",
        }
    )

    return {
        "version": 0.1,
        "item_id": item_id,
        "title": title,
        "layer": "layer2",
        "flow": "openroad",
        "state": "queued",
        "priority": priority,
        "created_utc": utcnow().astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "requested_by": requested_by,
        "platform": platform,
        "task": {
            "objective": objective,
            "source_mode": "src_verilog",
            "inputs": {
                **inputs,
                "generated_campaign": {
                    "base_campaign_path": campaign_path,
                    "path": generated_campaign_path,
                    "outputs": generated_outputs,
                },
            },
            "commands": commands,
            "expected_outputs": expected_outputs,
            "acceptance": [
                "Populate metrics.csv for all referenced design dirs",
                "Write campaign summary outputs under the campaign output directory",
                "Keep result_path/work_result_json fields repo-portable",
                "Run python3 scripts/validate_runs.py --skip_eval_queue before pushing",
            ],
        },
        "handoff": {
            "branch": f"eval/{item_id}/<session_id>",
            "pr_title": f"eval: run {title.lower()}",
            "identity_block_format": "[role:evaluator][account:<evaluator_id>][session:<session_id>][host:<host>][item:<queue_item_id>]",
            "pr_body_fields": {
                "evaluator_id": requested_by.lstrip("@") or "control_plane",
                "session_id": "<session_id>",
                "host": "<host>",
                "queue_item_id": item_id,
            },
            "checklist": [
                "Commit lightweight campaign artifacts only",
                "Include metrics row references in result.metrics_rows",
                "Keep committed result_path fields repo-portable",
                "Run python3 scripts/validate_runs.py --skip_eval_queue before pushing",
            ],
        },
        "result": None,
    }


def generate_l2_campaign_task(session: Session, request: Layer2CampaignGenerateRequest) -> Layer2TaskGenerateResult:
    repo_root = Path(request.repo_root).resolve()
    campaign_path = _repo_rel(request.campaign_path, repo_root)
    base_campaign = _load_json((repo_root / campaign_path).resolve())

    platform = request.platform or str(base_campaign.get("platform", "")).strip() or "unknown"
    campaign_id = str(base_campaign.get("campaign_id", Path(campaign_path).stem)).strip()
    item_id = request.item_id or _default_item_id(campaign_path=campaign_path, platform=platform)
    campaign = _with_fresh_outputs(campaign=base_campaign, item_id=item_id)
    generated_campaign_path = (Path(campaign_path).parent / f"{Path(campaign_path).stem}__{item_id}.json").as_posix()
    title = request.title or _default_title(campaign_id=campaign_id, platform=platform)
    objective = request.objective or _default_objective(campaign=campaign)
    inputs = _build_inputs(campaign=campaign)
    model_manifest = str(campaign.get("model_manifest", "")).strip() or None
    objective_profiles_json = (
        _repo_rel(request.objective_profiles_json, repo_root) if request.objective_profiles_json else None
    )
    expected_outputs = _build_expected_outputs(
        campaign=campaign,
        generated_campaign_path=generated_campaign_path,
        include_objective_sweep=bool(objective_profiles_json),
    )
    batch_id = request.batch_id or f"{item_id}_r1"
    payload = _build_payload(
        item_id=item_id,
        title=title,
        objective=objective,
        requested_by=request.requested_by,
        priority=request.priority,
        platform=platform,
        campaign_path=campaign_path,
        generated_campaign_path=generated_campaign_path,
        generated_outputs=dict(campaign.get("outputs") or {}),
        model_manifest=model_manifest,
        inputs=inputs,
        expected_outputs=expected_outputs,
        run_physical=request.run_physical,
        jobs=request.jobs,
        batch_id=batch_id,
        objective_profiles_json=objective_profiles_json,
    )

    existing = session.query(WorkItem).filter(WorkItem.item_id == item_id).one_or_none()
    if existing is None:
        task_request = TaskRequest(
            request_key=f"l2_campaign:{item_id}",
            source="l2_task_generator",
            requested_by=request.requested_by,
            title=title,
            description=objective,
            layer=LayerName.LAYER2,
            flow=FlowName.OPENROAD,
            priority=request.priority,
            request_payload=payload,
            source_commit=request.source_commit,
        )
        session.add(task_request)
        session.flush()

        work_item = WorkItem(
            work_item_key=f"l2_campaign:{item_id}",
            task_request_id=task_request.id,
            item_id=item_id,
            layer=LayerName.LAYER2,
            flow=FlowName.OPENROAD,
            platform=platform,
            task_type="l2_campaign",
            state=WorkItemState.READY,
            priority=request.priority,
            source_mode="src_verilog",
            input_manifest=payload["task"]["inputs"],
            command_manifest=payload["task"]["commands"],
            expected_outputs=payload["task"]["expected_outputs"],
            acceptance_rules=payload["task"]["acceptance"],
            source_commit=request.source_commit,
        )
        session.add(work_item)
        session.commit()
        return Layer2TaskGenerateResult(
            item_id=item_id,
            status="applied",
            work_item_id=work_item.id,
            task_request_id=task_request.id,
        )

    if request.mode == "error":
        raise Layer2TaskGenerationError(f"work item already exists: {item_id}")

    existing_payload = dict(existing.task_request.request_payload or {})
    status = "skipped" if existing_payload == payload else "applied"

    existing.task_request.requested_by = request.requested_by
    existing.task_request.title = title
    existing.task_request.description = objective
    existing.task_request.priority = request.priority
    existing.task_request.request_payload = payload
    existing.task_request.source_commit = request.source_commit

    existing.priority = request.priority
    existing.platform = platform
    existing.source_mode = "src_verilog"
    existing.input_manifest = payload["task"]["inputs"]
    existing.command_manifest = payload["task"]["commands"]
    existing.expected_outputs = payload["task"]["expected_outputs"]
    existing.acceptance_rules = payload["task"]["acceptance"]
    existing.source_commit = request.source_commit
    session.commit()
    return Layer2TaskGenerateResult(
        item_id=item_id,
        status=status,
        work_item_id=existing.id,
        task_request_id=existing.task_request_id,
    )
