"""Layer 1 task generation helpers."""

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


@dataclass(frozen=True)
class Layer1TaskGenerateResult:
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
            raise Layer1TaskGenerationError(f"path is outside repo_root: {path_text}") from exc
    return str(path)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_wrapper_name(config_path: Path) -> str:
    cfg = _load_json(config_path)
    if "multiplier" in cfg:
        module_name = cfg["multiplier"]["module_name"]
    elif "multiplier_yosys" in cfg:
        module_name = cfg["multiplier_yosys"]["module_name"]
    elif "adder" in cfg:
        module_name = cfg["adder"]["module_name"]
    elif "operations" in cfg and len(cfg["operations"]) == 1:
        entry = cfg["operations"][0]
        op_type = entry.get("type")
        if op_type not in {"activation", "softmax_rowwise"}:
            raise Layer1TaskGenerationError(f"unsupported single-operation design type in {config_path}: {op_type}")
        module_name = entry["module_name"]
    else:
        raise Layer1TaskGenerationError(f"unsupported config format for sweep generation: {config_path}")
    return f"{module_name}_wrapper"


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
) -> dict[str, Any]:
    return {
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
                "required_submodules": [
                    "third_party/nlohmann_json",
                    "third_party/cacti",
                ],
            },
            "commands": [
                {
                    "name": "build_generator",
                    "run": "cmake -S . -B build && cmake --build build --target rtlgen",
                },
                {
                    "name": "run_sweep",
                    "run": (
                        "python3 scripts/run_sweep.py "
                        f"--configs {' '.join(config_paths)} "
                        f"--platform {platform} "
                        f"--sweep {sweep_path} "
                        f"--out_root {out_root} "
                        "--skip_existing"
                    ),
                },
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


def generate_l1_sweep_task(session: Session, request: Layer1SweepGenerateRequest) -> Layer1TaskGenerateResult:
    if not request.config_paths:
        raise Layer1TaskGenerationError("config_paths must not be empty")

    repo_root = Path(request.repo_root).resolve()
    sweep_path = _repo_rel(request.sweep_path, repo_root)
    config_paths = [_repo_rel(path, repo_root) for path in request.config_paths]
    out_root = _repo_rel(request.out_root, repo_root)

    wrappers = [_read_wrapper_name((repo_root / config_path).resolve()) for config_path in config_paths]
    expected_outputs = [f"{out_root}/{wrapper}/metrics.csv" for wrapper in wrappers]
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
            source_commit=request.source_commit,
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
            state=WorkItemState.READY,
            priority=request.priority,
            source_mode="config",
            input_manifest=payload["task"]["inputs"],
            command_manifest=payload["task"]["commands"],
            expected_outputs=payload["task"]["expected_outputs"],
            acceptance_rules=payload["task"]["acceptance"],
            source_commit=request.source_commit,
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
    existing.task_request.source_commit = request.source_commit

    existing.priority = request.priority
    existing.platform = request.platform
    existing.source_mode = "config"
    existing.input_manifest = payload["task"]["inputs"]
    existing.command_manifest = payload["task"]["commands"]
    existing.expected_outputs = payload["task"]["expected_outputs"]
    existing.acceptance_rules = payload["task"]["acceptance"]
    existing.source_commit = request.source_commit
    session.commit()
    return Layer1TaskGenerateResult(
        item_id=item_id,
        status=status,
        work_item_id=existing.id,
        task_request_id=existing.task_request_id,
    )
