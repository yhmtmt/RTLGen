"""Layer 1 task generation helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timezone
from hashlib import sha256
import json
import os
import subprocess
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from control_plane.clock import utcnow
from control_plane.models.enums import FlowName, LayerName, WorkItemState
from control_plane.models.task_requests import TaskRequest
from control_plane.models.work_items import WorkItem
from control_plane.services.docs_paths import canonicalize_proposal_path, resolve_proposal_file


class Layer1TaskGenerationError(RuntimeError):
    pass


@dataclass(frozen=True)
class Layer1SweepGenerateRequest:
    repo_root: str
    sweep_path: str
    config_paths: list[str]
    platform: str
    out_root: str
    requested_by: str = "control_plane"
    priority: int = 1
    item_id: str | None = None
    title: str | None = None
    objective: str | None = None
    source_commit: str | None = None
    mode: str = "upsert"
    proposal_id: str | None = None
    proposal_path: str | None = None
    make_target: str | None = None
    evaluation_mode: str | None = None
    abstraction_layer: str | None = None
    trial_count: int = 1
    seed_start: int = 0
    stop_after_failures: int | None = None


@dataclass(frozen=True)
class Layer1TaskGenerateResult:
    item_id: str
    status: str
    work_item_id: str
    task_request_id: str


@dataclass(frozen=True)
class Layer1ConfigTarget:
    design_kind: str
    design_name: str
    expected_metrics_path: str
    commands: list[dict[str, str]]


def _with_oss_cad_path(command: str) -> str:
    return f"export PATH=/oss-cad-suite/bin:$PATH && {command}"


def _repo_rel(path_text: str, repo_root: Path) -> str:
    path = Path(path_text)
    if path.is_absolute():
        try:
            return str(path.resolve().relative_to(repo_root.resolve()))
        except ValueError as exc:
            raise Layer1TaskGenerationError(f"path is outside repo_root: {path_text}") from exc
    return str(path)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_proposal_abstraction_layer(repo_root: Path, proposal_path: str | None, abstraction_layer: str | None) -> str | None:
    layer = str(abstraction_layer or "").strip()
    if layer:
        return layer
    proposal_path_text = str(proposal_path or "").strip()
    if not proposal_path_text:
        return None
    proposal_file = resolve_proposal_file(repo_root, proposal_path=proposal_path_text)
    if proposal_file is None:
        return None
    if not proposal_file.exists():
        return None
    try:
        proposal = _load_json(proposal_file)
    except Exception:
        return None
    resolved = str(proposal.get("abstraction_layer", "")).strip()
    return resolved or None


def _image_provided_l1_runtime_deps_available() -> bool:
    cacti_root = Path(os.environ.get("RTLGEN_CACTI_ROOT", "/opt/rtlcp-deps/cacti"))
    json_root = Path(os.environ.get("RTLGEN_NLOHMANN_JSON_ROOT", "/opt/rtlcp-deps/nlohmann_json"))
    cacti_bin = cacti_root / "cacti"
    json_candidates = [
        json_root / "include" / "nlohmann" / "json.hpp",
        json_root / "nlohmann" / "json.hpp",
    ]
    return cacti_bin.exists() and any(path.exists() for path in json_candidates)


def _required_l1_runtime_submodules() -> list[str]:
    if _image_provided_l1_runtime_deps_available():
        return []
    return [
        "third_party/nlohmann_json",
        "third_party/cacti",
    ]


def _resolve_source_commit(repo_root: Path, source_commit: str | None) -> str:
    resolved = str(source_commit or "").strip()
    if resolved:
        return resolved
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        detail = f": {stderr}" if stderr else ""
        raise Layer1TaskGenerationError(f"failed to resolve source commit from repo_root {repo_root}{detail}") from exc
    resolved = result.stdout.strip()
    if not resolved:
        raise Layer1TaskGenerationError(f"failed to resolve source commit from repo_root {repo_root}: empty git rev-parse output")
    return resolved


def _contains_disabled_hierarchy(value: object) -> bool:
    if isinstance(value, list):
        return any(_contains_disabled_hierarchy(entry) for entry in value)
    if isinstance(value, bool):
        return not value
    if isinstance(value, (int, float)):
        return int(value) == 0
    token = str(value).strip().lower()
    return token in {"0", "false", "no", "off", "disable", "disabled"}


def _validate_architecture_block_sweep_policy(
    *,
    sweep_path: Path,
    abstraction_layer: str | None,
) -> None:
    if str(abstraction_layer or "").strip() != "architecture_block":
        return
    sweep = _load_json(sweep_path)
    flow_params = sweep.get("flow_params") or {}
    if not isinstance(flow_params, dict):
        raise Layer1TaskGenerationError(f"flow_params must be an object in {sweep_path}")
    hier_value = flow_params.get("SYNTH_HIERARCHICAL")
    if hier_value is not None and _contains_disabled_hierarchy(hier_value):
        raise Layer1TaskGenerationError(
            "architecture_block sweeps must keep hierarchy in early-stage evaluation; "
            f"found non-hierarchical SYNTH_HIERARCHICAL setting in {sweep_path}"
        )
    if sweep.get("mode_compare") is not None:
        raise Layer1TaskGenerationError(
            "architecture_block sweeps must not use mode_compare/flat_nomacro in early-stage evaluation; "
            f"use a hierarchy-preserving sweep instead: {sweep_path}"
        )


def _read_config_target(
    config_path: Path,
    *,
    repo_root: Path,
    config_rel: str,
    out_root: str,
    make_target: str | None,
) -> Layer1ConfigTarget:
    cfg = _load_json(config_path)
    if "multiplier" in cfg:
        module_name = cfg["multiplier"]["module_name"]
        wrapper = f"{module_name}_wrapper"
        return Layer1ConfigTarget(
            design_kind="wrapper",
            design_name=wrapper,
            expected_metrics_path=f"{out_root}/{wrapper}/metrics.csv",
            commands=[
                {
                    "name": "build_generator",
                    "run": _with_oss_cad_path("cmake -S . -B build && cmake --build build --target rtlgen"),
                },
                {
                    "name": "run_sweep",
                    "run": _with_oss_cad_path(
                        (
                        "python3 scripts/run_sweep.py "
                        f"--configs {config_rel} "
                        "--platform {platform} "
                        f"--sweep {{sweep_path}} "
                        f"--out_root {out_root} "
                        "--skip_existing"
                        )
                    ),
                },
            ],
        )
    elif "multiplier_yosys" in cfg:
        module_name = cfg["multiplier_yosys"]["module_name"]
        wrapper = f"{module_name}_wrapper"
        return Layer1ConfigTarget(
            design_kind="wrapper",
            design_name=wrapper,
            expected_metrics_path=f"{out_root}/{wrapper}/metrics.csv",
            commands=[
                {
                    "name": "build_generator",
                    "run": _with_oss_cad_path("cmake -S . -B build && cmake --build build --target rtlgen"),
                },
                {
                    "name": "run_sweep",
                    "run": _with_oss_cad_path(
                        (
                        "python3 scripts/run_sweep.py "
                        f"--configs {config_rel} "
                        "--platform {platform} "
                        f"--sweep {{sweep_path}} "
                        f"--out_root {out_root} "
                        "--skip_existing"
                        )
                    ),
                },
            ],
        )
    elif "adder" in cfg:
        module_name = cfg["adder"]["module_name"]
        wrapper = f"{module_name}_wrapper"
        return Layer1ConfigTarget(
            design_kind="wrapper",
            design_name=wrapper,
            expected_metrics_path=f"{out_root}/{wrapper}/metrics.csv",
            commands=[
                {
                    "name": "build_generator",
                    "run": _with_oss_cad_path("cmake -S . -B build && cmake --build build --target rtlgen"),
                },
                {
                    "name": "run_sweep",
                    "run": _with_oss_cad_path(
                        (
                        "python3 scripts/run_sweep.py "
                        f"--configs {config_rel} "
                        "--platform {platform} "
                        f"--sweep {{sweep_path}} "
                        f"--out_root {out_root} "
                        "--skip_existing"
                        )
                    ),
                },
            ],
        )
    elif "operations" in cfg and len(cfg["operations"]) == 1:
        entry = cfg["operations"][0]
        op_type = entry.get("type")
        if op_type not in {"activation", "softmax_rowwise"}:
            raise Layer1TaskGenerationError(f"unsupported single-operation design type in {config_path}: {op_type}")
        module_name = entry["module_name"]
        wrapper = f"{module_name}_wrapper"
        return Layer1ConfigTarget(
            design_kind="wrapper",
            design_name=wrapper,
            expected_metrics_path=f"{out_root}/{wrapper}/metrics.csv",
            commands=[
                {
                    "name": "build_generator",
                    "run": _with_oss_cad_path("cmake -S . -B build && cmake --build build --target rtlgen"),
                },
                {
                    "name": "run_sweep",
                    "run": _with_oss_cad_path(
                        (
                        "python3 scripts/run_sweep.py "
                        f"--configs {config_rel} "
                        "--platform {platform} "
                        f"--sweep {{sweep_path}} "
                        f"--out_root {out_root} "
                        "--skip_existing"
                        )
                    ),
                },
            ],
        )
    elif "top_name" in cfg and "compute" in cfg:
        top_name = str(cfg["top_name"]).strip()
        if not top_name:
            raise Layer1TaskGenerationError(f"top_name must not be empty in {config_path}")
        try:
            design_dir = str(config_path.parent.resolve().relative_to(repo_root.resolve()))
        except ValueError as exc:
            raise Layer1TaskGenerationError(
                f"integrated NPU block config must live under repo_root/runs/designs/...: {config_path}"
            ) from exc
        design_name = config_path.parent.name
        return Layer1ConfigTarget(
            design_kind="block",
            design_name=design_name,
            expected_metrics_path=f"{design_dir}/metrics.csv",
            commands=[
                {
                    "name": "build_generator",
                    "run": _with_oss_cad_path("cmake -S . -B build && cmake --build build --target rtlgen"),
                },
                {
                    "name": "generate_block_rtl",
                    "run": _with_oss_cad_path(
                        (
                        "python3 npu/rtlgen/gen.py "
                        f"--config {config_rel} "
                        f"--out {design_dir}/verilog"
                        )
                    ),
                },
                {
                    "name": "run_block_sweep",
                    "run": _with_oss_cad_path(
                        (
                        "python3 npu/synth/run_block_sweep.py "
                        f"--design_dir {design_dir} "
                        "--platform {platform} "
                        f"--top {top_name} "
                        f"--sweep {{sweep_path}} "
                        + (f"--make_target {make_target} " if make_target else "")
                        + "--skip_existing"
                        )
                    ),
                },
            ],
        )
    else:
        raise Layer1TaskGenerationError(f"unsupported config format for sweep generation: {config_path}")


def _default_item_id(*, sweep_path: str, platform: str, config_paths: list[str]) -> str:
    stem = Path(sweep_path).stem
    digest = sha256(json.dumps([sweep_path, platform, config_paths], sort_keys=True).encode("utf-8")).hexdigest()[:8]
    return f"l1_sweep_{stem}_{platform}_{digest}"


def _default_title(*, sweep_path: str, platform: str) -> str:
    return f"Layer1 sweep from {Path(sweep_path).stem} on {platform}"


def _default_objective(*, platform: str, config_paths: list[str], sweep_path: str) -> str:
    return (
        f"Run a Layer1 {platform} OpenROAD sweep for {len(config_paths)} configs using "
        f"{Path(sweep_path).name} and record lightweight design metrics for comparison."
    )


def _effective_trial_policy(*, trial_count: int, seed_start: int, stop_after_failures: int | None) -> dict[str, int]:
    effective_trial_count = max(int(trial_count), 1)
    effective_seed_start = int(seed_start)
    effective_stop_after_failures = stop_after_failures
    if effective_stop_after_failures is None:
        effective_stop_after_failures = effective_trial_count
    effective_stop_after_failures = max(1, min(int(effective_stop_after_failures), effective_trial_count))
    return {
        "trial_count": effective_trial_count,
        "seed_start": effective_seed_start,
        "stop_after_failures": effective_stop_after_failures,
    }


def _effective_evaluation_mode(*, evaluation_mode: str | None, make_target: str | None) -> str:
    mode = str(evaluation_mode or "").strip()
    if mode:
        return mode
    if str(make_target or "").strip():
        return "synth_prefilter"
    return "measurement_only"


def _build_payload(
    *,
    item_id: str,
    title: str,
    objective: str,
    requested_by: str,
    priority: int,
    platform: str,
    sweep_path: str,
    config_paths: list[str],
    out_root: str,
    expected_outputs: list[str],
    command_manifest: list[dict[str, str]],
    proposal_id: str | None,
    proposal_path: str | None,
    evaluation_mode: str,
    abstraction_layer: str | None,
    trial_policy: dict[str, int],
) -> dict[str, Any]:
    payload = {
        "version": 0.1,
        "item_id": item_id,
        "title": title,
        "layer": "layer1",
        "flow": "openroad",
        "state": "queued",
        "priority": priority,
        "created_utc": utcnow().astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "requested_by": requested_by,
        "platform": platform,
        "task": {
            "objective": objective,
            "source_mode": "config",
            "inputs": {
                "configs": config_paths,
                "design_dirs": [],
                "sweeps": [sweep_path],
                "macro_manifests": [],
                "candidate_manifests": [],
                "required_submodules": _required_l1_runtime_submodules(),
                "out_root": out_root,
            },
            "commands": [
                *command_manifest,
                {
                    "name": "build_runs_index",
                    "run": "python3 scripts/build_runs_index.py",
                },
                {
                    "name": "validate",
                    "run": "python3 scripts/validate_runs.py --skip_eval_queue",
                },
            ],
            "expected_outputs": expected_outputs,
            "acceptance": [
                "Each generated wrapper metrics.csv contains at least one status=ok row for the queued sweep",
                "Committed outputs stay lightweight (metrics.csv and runs/index.csv only)",
                "python3 scripts/build_runs_index.py and python3 scripts/validate_runs.py --skip_eval_queue pass",
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
                "Commit only lightweight metrics and regenerated runs/index.csv",
                "Include metrics row references for each completed design",
                "Run python3 scripts/build_runs_index.py and python3 scripts/validate_runs.py --skip_eval_queue before pushing",
            ],
        },
        "result": None,
    }
    if proposal_id or proposal_path or evaluation_mode or abstraction_layer:
        payload["developer_loop"] = {
            "proposal_id": proposal_id or "",
            "proposal_path": proposal_path or "",
            "evaluation": {
                "mode": evaluation_mode,
                "trial_policy": trial_policy,
            },
        }
        if abstraction_layer:
            payload["developer_loop"]["abstraction"] = {
                "layer": abstraction_layer,
            }
    return payload


def generate_l1_sweep_task(session: Session, request: Layer1SweepGenerateRequest) -> Layer1TaskGenerateResult:
    if not request.config_paths:
        raise Layer1TaskGenerationError("config_paths must not be empty")

    repo_root = Path(request.repo_root).resolve()
    sweep_path = _repo_rel(request.sweep_path, repo_root)
    config_paths = [_repo_rel(path, repo_root) for path in request.config_paths]
    out_root = _repo_rel(request.out_root, repo_root)
    proposal_path = _repo_rel(request.proposal_path, repo_root) if request.proposal_path else None
    proposal_path = canonicalize_proposal_path(repo_root, proposal_path=proposal_path, proposal_id=request.proposal_id)
    effective_abstraction_layer = _resolve_proposal_abstraction_layer(repo_root, proposal_path, request.abstraction_layer)
    _validate_architecture_block_sweep_policy(
        sweep_path=(repo_root / sweep_path).resolve(),
        abstraction_layer=effective_abstraction_layer,
    )
    source_commit = _resolve_source_commit(repo_root, request.source_commit)

    targets = [
        _read_config_target(
            (repo_root / config_path).resolve(),
            repo_root=repo_root,
            config_rel=config_path,
            out_root=out_root,
            make_target=request.make_target,
        )
        for config_path in config_paths
    ]
    if not targets:
        raise Layer1TaskGenerationError("config_paths must not be empty")
    design_kinds = {target.design_kind for target in targets}
    if len(design_kinds) != 1:
        raise Layer1TaskGenerationError(
            f"mixed Layer1 config kinds are not supported in one sweep item: {sorted(design_kinds)}"
        )
    command_manifest = list(targets[0].commands)
    for command in command_manifest:
        command["run"] = command["run"].format(platform=request.platform, sweep_path=sweep_path)
    expected_outputs = [target.expected_metrics_path for target in targets]
    expected_outputs.append("runs/index.csv")

    item_id = request.item_id or _default_item_id(
        sweep_path=sweep_path,
        platform=request.platform,
        config_paths=config_paths,
    )
    title = request.title or _default_title(sweep_path=sweep_path, platform=request.platform)
    objective = request.objective or _default_objective(
        platform=request.platform,
        config_paths=config_paths,
        sweep_path=sweep_path,
    )
    payload = _build_payload(
        item_id=item_id,
        title=title,
        objective=objective,
        requested_by=request.requested_by,
        priority=request.priority,
        platform=request.platform,
        sweep_path=sweep_path,
        config_paths=config_paths,
        out_root=out_root,
        expected_outputs=expected_outputs,
        command_manifest=command_manifest,
        proposal_id=request.proposal_id,
        proposal_path=proposal_path,
        evaluation_mode=_effective_evaluation_mode(
            evaluation_mode=request.evaluation_mode,
            make_target=request.make_target,
        ),
        abstraction_layer=effective_abstraction_layer,
        trial_policy=_effective_trial_policy(
            trial_count=request.trial_count,
            seed_start=request.seed_start,
            stop_after_failures=request.stop_after_failures,
        ),
    )

    existing = session.query(WorkItem).filter(WorkItem.item_id == item_id).one_or_none()
    if existing is None:
        task_request = TaskRequest(
            request_key=f"l1_sweep:{item_id}",
            source="l1_task_generator",
            requested_by=request.requested_by,
            title=title,
            description=objective,
            layer=LayerName.LAYER1,
            flow=FlowName.OPENROAD,
            priority=request.priority,
            request_payload=payload,
            source_commit=source_commit,
        )
        session.add(task_request)
        session.flush()

        work_item = WorkItem(
            work_item_key=f"l1_sweep:{item_id}",
            task_request_id=task_request.id,
            item_id=item_id,
            layer=LayerName.LAYER1,
            flow=FlowName.OPENROAD,
            platform=request.platform,
            task_type="l1_sweep",
            state=WorkItemState.DISPATCH_PENDING,
            priority=request.priority,
            source_mode="config",
            input_manifest=payload["task"]["inputs"],
            command_manifest=payload["task"]["commands"],
            expected_outputs=payload["task"]["expected_outputs"],
            acceptance_rules=payload["task"]["acceptance"],
            source_commit=source_commit,
            trial_policy_json=((payload.get("developer_loop") or {}).get("evaluation") or {}).get("trial_policy") or {},
        )
        session.add(work_item)
        session.commit()
        return Layer1TaskGenerateResult(
            item_id=item_id,
            status="applied",
            work_item_id=work_item.id,
            task_request_id=task_request.id,
        )

    if request.mode == "error":
        raise Layer1TaskGenerationError(f"work item already exists: {item_id}")

    existing_payload = dict(existing.task_request.request_payload or {})
    status = "skipped" if existing_payload == payload else "applied"

    existing.task_request.requested_by = request.requested_by
    existing.task_request.title = title
    existing.task_request.description = objective
    existing.task_request.priority = request.priority
    existing.task_request.request_payload = payload
    existing.task_request.source_commit = source_commit

    existing.priority = request.priority
    existing.platform = request.platform
    existing.source_mode = "config"
    existing.input_manifest = payload["task"]["inputs"]
    existing.command_manifest = payload["task"]["commands"]
    existing.expected_outputs = payload["task"]["expected_outputs"]
    existing.acceptance_rules = payload["task"]["acceptance"]
    existing.source_commit = source_commit
    existing.trial_policy_json = ((payload.get("developer_loop") or {}).get("evaluation") or {}).get("trial_policy") or {}
    session.commit()
    return Layer1TaskGenerateResult(
        item_id=item_id,
        status=status,
        work_item_id=existing.id,
        task_request_id=existing.task_request_id,
    )
