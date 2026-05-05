"""Layer 2 task generation helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timezone
from hashlib import sha256
import json
import re
import shlex
import subprocess
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from control_plane.clock import utcnow
from control_plane.models.enums import FlowName, LayerName, WorkItemState
from control_plane.models.task_requests import TaskRequest
from control_plane.models.work_items import WorkItem
from control_plane.services.dependency_gate import evaluate_work_item_dependencies
from control_plane.services.docs_paths import canonicalize_proposal_path, resolve_proposal_dir
from control_plane.services.proposal_scaffold import ensure_proposal_scaffold


class Layer2TaskGenerationError(RuntimeError):
    pass


_RETRY_SUFFIX_RE = re.compile(r"_r\d+$")


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
    proposal_id: str | None = None
    proposal_path: str | None = None
    evaluation_mode: str | None = None
    abstraction_layer: str | None = None
    expected_direction: str | None = None
    expected_reason: str | None = None
    comparison_role: str | None = None
    paired_baseline_item_id: str | None = None
    depends_on_item_ids: list[str] | None = None
    requires_merged_inputs: bool = False
    requires_materialized_refs: bool = False


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


def _retry_base(item_id: str) -> str:
    return _RETRY_SUFFIX_RE.sub("", item_id.strip())


def _proposal_dir(repo_root: Path, proposal_path: str | None) -> Path | None:
    proposal_rel = str(proposal_path or "").strip()
    if not proposal_rel:
        return None
    return resolve_proposal_dir(repo_root, proposal_path=proposal_rel)


def _load_requested_item_entry(repo_root: Path, proposal_path: str | None, item_id: str) -> dict[str, Any] | None:
    proposal_dir = _proposal_dir(repo_root, proposal_path)
    if proposal_dir is None:
        return None
    evaluation_requests_path = proposal_dir / "evaluation_requests.json"
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
        if isinstance(entry, dict) and str(entry.get("item_id", "")).strip() == item_id:
            return entry
    item_retry_base = _retry_base(item_id)
    retry_matches = [
        entry
        for entry in requested_items
        if isinstance(entry, dict) and _retry_base(str(entry.get("item_id", "")).strip()) == item_retry_base
    ]
    if len(retry_matches) == 1:
        return retry_matches[0]
    return None


def _resolve_requested_entry_text(
    entry: dict[str, Any] | None,
    *,
    key: str,
    explicit: str | None,
) -> str | None:
    resolved = str(explicit or "").strip()
    if resolved:
        return resolved
    if not isinstance(entry, dict):
        return None
    candidate = str(entry.get(key, "")).strip()
    return candidate or None


def _resolve_requested_entry_list(
    entry: dict[str, Any] | None,
    *,
    key: str,
    explicit: list[str] | None,
) -> list[str] | None:
    if explicit is not None:
        return [str(value).strip() for value in explicit if str(value).strip()]
    if not isinstance(entry, dict):
        return None
    values = entry.get(key)
    if not isinstance(values, list):
        return None
    return [str(value).strip() for value in values if str(value).strip()]


def _resolve_requested_entry_bool(
    entry: dict[str, Any] | None,
    *,
    key: str,
    explicit: bool,
) -> bool:
    if explicit:
        return True
    if not isinstance(entry, dict):
        return False
    return bool(entry.get(key))


def _upsert_requested_item_entry(
    *,
    repo_root: Path,
    proposal_id: str | None,
    proposal_path: str | None,
    item_id: str,
    task_type: str,
    objective: str,
    evaluation_mode: str | None,
    abstraction_layer: str | None,
    comparison_role: str | None,
    paired_baseline_item_id: str | None,
    depends_on_item_ids: list[str] | None,
    requires_merged_inputs: bool,
    requires_materialized_refs: bool,
    expected_direction: str | None,
    expected_reason: str | None,
    source_commit: str,
) -> None:
    proposal_id_text = str(proposal_id or '').strip()
    proposal_dir = resolve_proposal_dir(
        repo_root,
        proposal_path=str(proposal_path or '').strip() or None,
        proposal_id=proposal_id_text or None,
    )
    if proposal_dir is None:
        return
    ensure_proposal_scaffold(
        repo_root=repo_root,
        proposal_dir=proposal_dir,
        proposal_id=proposal_id_text or proposal_dir.name,
        source_commit=source_commit,
        layer='layer2',
        kind='architecture',
    )
    evaluation_requests_path = proposal_dir / 'evaluation_requests.json'
    payload = _load_json(evaluation_requests_path)
    requested_items = payload.get('requested_items')
    if not isinstance(requested_items, list):
        requested_items = []
        payload['requested_items'] = requested_items

    entry = None
    for candidate in requested_items:
        if isinstance(candidate, dict) and str(candidate.get('item_id', '')).strip() == item_id:
            entry = candidate
            break
    if entry is None:
        retry_base = _retry_base(item_id)
        retry_matches = [
            candidate
            for candidate in requested_items
            if isinstance(candidate, dict) and _retry_base(str(candidate.get('item_id', '')).strip()) == retry_base
        ]
        if len(retry_matches) == 1:
            entry = retry_matches[0]
            previous_item_id = str(entry.get('item_id', '')).strip()
            if previous_item_id and previous_item_id != item_id:
                prior_item_ids = entry.get('prior_item_ids')
                prior_values = [str(value).strip() for value in prior_item_ids] if isinstance(prior_item_ids, list) else []
                if previous_item_id not in prior_values:
                    prior_values.append(previous_item_id)
                entry['prior_item_ids'] = prior_values
        else:
            entry = {}
            requested_items.append(entry)

    entry['item_id'] = item_id
    entry['task_type'] = task_type
    entry['objective'] = objective
    entry['evaluation_mode'] = str(evaluation_mode or '').strip()
    entry['abstraction_layer'] = str(abstraction_layer or '').strip()
    entry['comparison_role'] = str(comparison_role or '').strip()
    entry['paired_baseline_item_id'] = str(paired_baseline_item_id or '').strip()
    entry['depends_on_item_ids'] = [str(v).strip() for v in (depends_on_item_ids or []) if str(v).strip()]
    entry['requires_merged_inputs'] = bool(requires_merged_inputs)
    entry['requires_materialized_refs'] = bool(requires_materialized_refs)
    if str(expected_direction or '').strip() or str(expected_reason or '').strip():
        entry['expected_result'] = {
            'direction': str(expected_direction or '').strip(),
            'reason': str(expected_reason or '').strip(),
        }
    entry['status'] = 'pending'
    payload['proposal_id'] = str(payload.get('proposal_id') or proposal_id_text or proposal_dir.name).strip()
    payload['source_commit'] = source_commit
    evaluation_requests_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _resolve_source_commit(repo_root: Path, source_commit: str | None) -> str:
    resolved = str(source_commit or "").strip()
    if resolved:
        try:
            subprocess.run(
                ["git", "-C", str(repo_root), "cat-file", "-e", f"{resolved}^{{commit}}"],
                check=True,
                capture_output=True,
                text=True,
            )
            result = subprocess.run(
                ["git", "-C", str(repo_root), "rev-parse", f"{resolved}^{{commit}}"],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as exc:
            stderr = (exc.stderr or "").strip()
            detail = f": {stderr}" if stderr else ""
            raise Layer2TaskGenerationError(
                f"provided source_commit does not resolve to a commit in repo_root {repo_root}: {resolved}{detail}"
            ) from exc
        normalized = result.stdout.strip()
        if not normalized:
            raise Layer2TaskGenerationError(
                f"provided source_commit resolved to empty git rev-parse output in repo_root {repo_root}: {resolved}"
            )
        try:
            subprocess.run(
                ["git", "-C", str(repo_root), "fetch", "--quiet", "origin"],
                check=True,
                capture_output=True,
                text=True,
            )
            refs = subprocess.run(
                [
                    "git", "-C", str(repo_root), "for-each-ref", "refs/remotes/origin",
                    "--contains", normalized, "--format=%(refname)",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as exc:
            stderr = (exc.stderr or "").strip()
            detail = f": {stderr}" if stderr else ""
            raise Layer2TaskGenerationError(
                f"failed to verify source_commit against origin for repo_root {repo_root}: {normalized}{detail}"
            ) from exc
        if not refs.stdout.strip():
            raise Layer2TaskGenerationError(
                f"provided source_commit is not reachable from origin in repo_root {repo_root}: {normalized}"
            )
        return normalized
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
        raise Layer2TaskGenerationError(f"failed to resolve source commit from repo_root {repo_root}{detail}") from exc
    resolved = result.stdout.strip()
    if not resolved:
        raise Layer2TaskGenerationError(f"failed to resolve source commit from repo_root {repo_root}: empty git rev-parse output")
    return resolved


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


def _default_pr_title(*, title: str) -> str:
    normalized = str(title).strip()
    lowered = normalized.lower()
    if lowered.startswith("run "):
        return f"eval: {lowered}"
    return f"eval: run {lowered}"


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


def _decoder_probability_path_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_tiny_v1"
    validation_out = f"{base}/decoder_contract_validation__{item_id}.json"
    quality_out = f"{base}/decoder_quality_compare__{item_id}.json"
    missing_model_check_out = f"{base}/missing_model_check__{item_id}.json"
    missing_model_check_cmd = f"""python3 - <<'PY2'
import json
import subprocess
import sys
import tempfile
from pathlib import Path

out = Path('{missing_model_check_out}')
out.parent.mkdir(parents=True, exist_ok=True)
with tempfile.TemporaryDirectory() as td:
    td_path = Path(td)
    vocab_json = td_path / 'vocab.json'
    model_config = td_path / 'config.json'
    tokenizer_manifest = td_path / 'tokenizer_manifest.json'
    vocab_json.write_text(json.dumps({{'tokens': ['The', ' capital', ' of', ' France', ' is', ' Paris']}}), encoding='utf-8')
    model_config.write_text(json.dumps({{'n_layer': 2, 'n_head': 2, 'n_embd': 128}}), encoding='utf-8')
    tokenizer_manifest.write_text(json.dumps({{
        'tokenizer_id': 'llm_decoder_space_prefix_v1',
        'kind': 'space_prefix_words',
        'vocab_json': str(vocab_json),
    }}), encoding='utf-8')
    request = {{
        'role': 'reference',
        'backend_config': {{
            'backend_id': 'command_json_v1',
            'onnx_model_path': str(td_path / 'missing.onnx'),
            'model_config_path': str(model_config),
            'input_name': 'input_ids',
        }},
        'sample': {{
            'sample_id': 'geo_france_capital',
            'prompt': 'The capital of France is',
            'expected_continuation': ' Paris',
        }},
        'paths': {{'tokenizer_manifest_path': str(tokenizer_manifest)}},
    }}
    proc = subprocess.run(
        [sys.executable, 'npu/eval/run_llm_decoder_onnx_reference.py'],
        input=json.dumps(request),
        text=True,
        capture_output=True,
        check=False,
    )
    result = {{
        'ok': proc.returncode != 0 and 'NoSuchFile' in proc.stderr,
        'returncode': proc.returncode,
        'stderr_contains_NoSuchFile': 'NoSuchFile' in proc.stderr,
        'stderr_tail': proc.stderr[-1000:],
    }}
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + '\\n', encoding='utf-8')
    if not result['ok']:
        print(json.dumps(result, indent=2, sort_keys=True), file=sys.stderr)
        raise SystemExit(1)
PY2"""
    return {
        "inputs": {
            "dataset_manifest": f"{base}/manifest.json",
            "reference_manifest": f"{base}/reference_manifest.json",
            "candidate_manifest": f"{base}/candidate_manifest.json",
            "baseline_quality_out": f"{base}/decoder_quality_compare__l2_decoder_contract_eval_confirm_v1.json",
            "validation_out": validation_out,
            "quality_out": quality_out,
            "missing_model_check_out": missing_model_check_out,
        },
        "commands": [
            {
                "name": "validate_decoder_contract",
                "run": f"python3 npu/eval/validate_llm_decoder_contract.py --dataset-manifest {base}/manifest.json --out {validation_out}",
            },
            {
                "name": "compare_decoder_quality",
                "run": f"python3 npu/eval/compare_llm_decoder_quality.py --reference-manifest {base}/reference_manifest.json --candidate-manifest {base}/candidate_manifest.json --out {quality_out}",
            },
            {
                "name": "check_decoder_missing_model_error",
                "run": missing_model_check_cmd,
            },
        ],
        "expected_outputs": [validation_out, quality_out, missing_model_check_out],
    }


def _decoder_probability_sweep_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_tiny_v1"
    path_evidence = _decoder_probability_path_evidence(item_id=item_id)
    sweep_dir = f"{base}/candidate_sweeps/{item_id}"
    sweep_out = f"{base}/decoder_quality_sweep__{item_id}.json"
    sweep_command = {
        "name": "sweep_decoder_candidate_quality",
        "run": (
            "python3 npu/eval/sweep_llm_decoder_candidate_quality.py "
            f"--dataset-manifest {base}/manifest.json "
            "--template candidate_onnx_softmax_exact "
            "--template candidate_onnx_softmax_approx "
            f"--out-dir {sweep_dir} "
            f"--out {sweep_out}"
        ),
    }
    inputs = dict(path_evidence["inputs"])
    inputs.update(
        {
            "candidate_sweep_dir": sweep_dir,
            "candidate_sweep_out": sweep_out,
            "candidate_sweep_templates": [
                "candidate_onnx_softmax_exact",
                "candidate_onnx_softmax_approx",
            ],
        }
    )
    return {
        "inputs": inputs,
        "commands": [*path_evidence["commands"], sweep_command],
        "expected_outputs": [*path_evidence["expected_outputs"], sweep_out],
    }


def _decoder_probability_sensitivity_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_tiny_v1"
    path_evidence = _decoder_probability_path_evidence(item_id=item_id)
    sweep_dir = f"{base}/candidate_sweeps/{item_id}"
    sweep_out = f"{base}/decoder_quality_sweep__{item_id}.json"
    rough_grid = "decoder_probability_broad_v1"
    sweep_command = {
        "name": "sweep_decoder_candidate_quality",
        "run": (
            "python3 npu/eval/sweep_llm_decoder_candidate_quality.py "
            f"--dataset-manifest {base}/manifest.json "
            f"--rough-grid {rough_grid} "
            f"--out-dir {sweep_dir} "
            f"--out {sweep_out}"
        ),
    }
    inputs = dict(path_evidence["inputs"])
    inputs.update(
        {
            "candidate_sweep_dir": sweep_dir,
            "candidate_sweep_out": sweep_out,
            "candidate_sweep_grid": rough_grid,
            "candidate_sweep_scope": (
                "coarse distribution-dependent sensitivity map for the pinned tiny decoder "
                "benchmark; not general approximation acceptance evidence"
            ),
        }
    )
    return {
        "inputs": inputs,
        "commands": [*path_evidence["commands"], sweep_command],
        "expected_outputs": [*path_evidence["expected_outputs"], sweep_out],
    }


def _decoder_probability_fp_sensitivity_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_tiny_v1"
    path_evidence = _decoder_probability_path_evidence(item_id=item_id)
    sweep_dir = f"{base}/candidate_sweeps/{item_id}"
    sweep_out = f"{base}/decoder_quality_sweep__{item_id}.json"
    rough_grid = "decoder_probability_fp_formats_v1"
    sweep_command = {
        "name": "sweep_decoder_candidate_quality",
        "run": (
            "python3 npu/eval/sweep_llm_decoder_candidate_quality.py "
            f"--dataset-manifest {base}/manifest.json "
            f"--rough-grid {rough_grid} "
            f"--out-dir {sweep_dir} "
            f"--out {sweep_out}"
        ),
    }
    inputs = dict(path_evidence["inputs"])
    inputs.update(
        {
            "candidate_sweep_dir": sweep_dir,
            "candidate_sweep_out": sweep_out,
            "candidate_sweep_grid": rough_grid,
            "candidate_sweep_scope": (
                "coarse distribution-dependent fp-like format sensitivity map for logits, "
                "softmax intermediates, reciprocal normalization, and final probabilities"
            ),
        }
    )
    return {
        "inputs": inputs,
        "commands": [*path_evidence["commands"], sweep_command],
        "expected_outputs": [*path_evidence["expected_outputs"], sweep_out],
    }


def _decoder_distribution_robustness_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_tiny_v1"
    dataset_manifest = f"{base}/manifest_distribution_v1.json"
    reference_dir = f"{base}/reference_distribution_v1"
    reference_manifest = f"{base}/reference_distribution_v1_manifest.json"
    candidate_dir = f"{base}/candidate_distribution_v1"
    candidate_manifest = f"{base}/candidate_distribution_v1_manifest.json"
    validation_out = f"{base}/decoder_contract_validation__{item_id}.json"
    quality_out = f"{base}/decoder_quality_compare__{item_id}.json"
    sweep_dir = f"{base}/candidate_sweeps/{item_id}"
    sweep_out = f"{base}/decoder_quality_sweep__{item_id}.json"
    rough_grid = "decoder_distribution_robustness_v1"
    commands = [
        {
            "name": "generate_decoder_distribution_reference",
            "run": (
                "python3 npu/eval/gen_llm_decoder_reference_suite.py "
                f"--dataset-manifest {dataset_manifest} "
                f"--out-dir {reference_dir} "
                f"--out-manifest {reference_manifest}"
            ),
        },
        {
            "name": "generate_decoder_distribution_candidate",
            "run": (
                "python3 npu/eval/gen_llm_decoder_candidate_suite.py "
                f"--dataset-manifest {dataset_manifest} "
                f"--out-dir {candidate_dir} "
                f"--out-manifest {candidate_manifest}"
            ),
        },
        {
            "name": "validate_decoder_distribution_contract",
            "run": f"python3 npu/eval/validate_llm_decoder_contract.py --dataset-manifest {dataset_manifest} --out {validation_out}",
        },
        {
            "name": "compare_decoder_distribution_quality",
            "run": (
                "python3 npu/eval/compare_llm_decoder_quality.py "
                f"--reference-manifest {reference_manifest} "
                f"--candidate-manifest {candidate_manifest} "
                f"--out {quality_out}"
            ),
        },
        {
            "name": "sweep_decoder_distribution_quality",
            "run": (
                "python3 npu/eval/sweep_llm_decoder_candidate_quality.py "
                f"--dataset-manifest {dataset_manifest} "
                f"--rough-grid {rough_grid} "
                f"--out-dir {sweep_dir} "
                f"--out {sweep_out}"
            ),
        },
    ]
    return {
        "inputs": {
            "dataset_manifest": dataset_manifest,
            "sample_file": f"{base}/samples_distribution_v1.jsonl",
            "reference_manifest": reference_manifest,
            "candidate_manifest": candidate_manifest,
            "reference_dir": reference_dir,
            "candidate_dir": candidate_dir,
            "validation_out": validation_out,
            "quality_out": quality_out,
            "candidate_sweep_dir": sweep_dir,
            "candidate_sweep_out": sweep_out,
            "candidate_sweep_grid": rough_grid,
            "candidate_sweep_scope": (
                "broader rough decoder distribution map across prompt categories, logit "
                "entropy/margin regimes, and integer versus fp-like probability formats"
            ),
        },
        "commands": commands,
        "expected_outputs": [
            reference_manifest,
            candidate_manifest,
            validation_out,
            quality_out,
            sweep_out,
        ],
    }


def _decoder_survivor_prompt_stress_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_tiny_v1"
    dataset_manifest = f"{base}/manifest_prompt_stress_v1.json"
    reference_dir = f"{base}/reference_prompt_stress_v1"
    reference_manifest = f"{base}/reference_prompt_stress_v1_manifest.json"
    candidate_dir = f"{base}/candidate_prompt_stress_v1"
    candidate_manifest = f"{base}/candidate_prompt_stress_v1_manifest.json"
    validation_out = f"{base}/decoder_contract_validation__{item_id}.json"
    quality_out = f"{base}/decoder_quality_compare__{item_id}.json"
    sweep_dir = f"{base}/candidate_sweeps/{item_id}"
    sweep_out = f"{base}/decoder_quality_sweep__{item_id}.json"
    rough_grid = "decoder_survivor_prompt_stress_v1"
    commands = [
        {
            "name": "generate_decoder_prompt_stress_reference",
            "run": (
                "python3 npu/eval/gen_llm_decoder_reference_suite.py "
                f"--dataset-manifest {dataset_manifest} "
                f"--out-dir {reference_dir} "
                f"--out-manifest {reference_manifest}"
            ),
        },
        {
            "name": "generate_decoder_prompt_stress_candidate",
            "run": (
                "python3 npu/eval/gen_llm_decoder_candidate_suite.py "
                f"--dataset-manifest {dataset_manifest} "
                f"--out-dir {candidate_dir} "
                f"--out-manifest {candidate_manifest}"
            ),
        },
        {
            "name": "validate_decoder_prompt_stress_contract",
            "run": f"python3 npu/eval/validate_llm_decoder_contract.py --dataset-manifest {dataset_manifest} --out {validation_out}",
        },
        {
            "name": "compare_decoder_prompt_stress_quality",
            "run": (
                "python3 npu/eval/compare_llm_decoder_quality.py "
                f"--reference-manifest {reference_manifest} "
                f"--candidate-manifest {candidate_manifest} "
                f"--out {quality_out}"
            ),
        },
        {
            "name": "sweep_decoder_prompt_stress_quality",
            "run": (
                "python3 npu/eval/sweep_llm_decoder_candidate_quality.py "
                f"--dataset-manifest {dataset_manifest} "
                f"--rough-grid {rough_grid} "
                f"--out-dir {sweep_dir} "
                f"--out {sweep_out}"
            ),
        },
    ]
    return {
        "inputs": {
            "dataset_manifest": dataset_manifest,
            "sample_file": f"{base}/samples_prompt_stress_v1.jsonl",
            "reference_manifest": reference_manifest,
            "candidate_manifest": candidate_manifest,
            "reference_dir": reference_dir,
            "candidate_dir": candidate_dir,
            "validation_out": validation_out,
            "quality_out": quality_out,
            "candidate_sweep_dir": sweep_dir,
            "candidate_sweep_out": sweep_out,
            "candidate_sweep_grid": rough_grid,
            "candidate_sweep_scope": (
                "focused survivor prompt-stress map across the decoder approximation paths "
                "that survived or bordered failure in the broader distribution sweep"
            ),
        },
        "commands": commands,
        "expected_outputs": [
            reference_manifest,
            candidate_manifest,
            validation_out,
            quality_out,
            sweep_out,
        ],
    }


def _decoder_survivor_cost_proxy_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_tiny_v1"
    sweep_in = f"{base}/decoder_quality_sweep__l2_decoder_survivor_prompt_stress_v1.json"
    cost_out = f"{base}/decoder_survivor_cost_proxy__{item_id}.json"
    cost_report = f"{base}/decoder_survivor_cost_proxy__{item_id}.md"
    commands = [
        {
            "name": "estimate_decoder_survivor_cost_proxy",
            "run": (
                "python3 npu/eval/estimate_llm_decoder_survivor_cost.py "
                f"--sweep {sweep_in} "
                f"--out {cost_out} "
                f"--out-md {cost_report}"
            ),
        },
    ]
    return {
        "inputs": {
            "source_sweep": sweep_in,
            "cost_proxy_out": cost_out,
            "cost_proxy_report": cost_report,
            "cost_proxy_scope": (
                "relative planning proxy over prompt-stress survivor rows; not RTL, "
                "OpenROAD PPA, or final hardware acceptance"
            ),
        },
        "commands": commands,
        "expected_outputs": [
            cost_out,
            cost_report,
        ],
    }


def _decoder_pwl_frontier_detail_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_tiny_v1"
    sweep_in = f"{base}/decoder_quality_sweep__l2_decoder_survivor_prompt_stress_v1.json"
    cost_proxy_in = f"{base}/decoder_survivor_cost_proxy__l2_decoder_survivor_cost_proxy_v1.json"
    frontier_out = f"{base}/decoder_pwl_frontier_detail__{item_id}.json"
    frontier_report = f"{base}/decoder_pwl_frontier_detail__{item_id}.md"
    commands = [
        {
            "name": "estimate_decoder_pwl_frontier_detail",
            "run": (
                "python3 npu/eval/estimate_llm_decoder_pwl_frontier.py "
                f"--sweep {sweep_in} "
                f"--cost-proxy {cost_proxy_in} "
                f"--out {frontier_out} "
                f"--out-md {frontier_report}"
            ),
        },
    ]
    return {
        "inputs": {
            "source_sweep": sweep_in,
            "source_cost_proxy": cost_proxy_in,
            "frontier_detail_out": frontier_out,
            "frontier_detail_report": frontier_report,
            "frontier_detail_scope": (
                "focused planning breakdown of the two exact-safe decoder PWL survivors; "
                "separates table footprint, interpolation width, normalization path, and integration risk"
            ),
        },
        "commands": commands,
        "expected_outputs": [
            frontier_out,
            frontier_report,
        ],
    }


def _decoder_q8_normalization_frontier_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_tiny_v1"
    dataset_manifest = f"{base}/manifest_prompt_stress_v1.json"
    reference_dir = f"{base}/reference_prompt_stress_v1"
    reference_manifest = f"{base}/reference_prompt_stress_v1_manifest.json"
    candidate_dir = f"{base}/candidate_prompt_stress_v1"
    candidate_manifest = f"{base}/candidate_prompt_stress_v1_manifest.json"
    validation_out = f"{base}/decoder_contract_validation__{item_id}.json"
    quality_out = f"{base}/decoder_quality_compare__{item_id}.json"
    sweep_dir = f"{base}/candidate_sweeps/{item_id}"
    sweep_out = f"{base}/decoder_quality_sweep__{item_id}.json"
    frontier_out = f"{base}/decoder_q8_norm_frontier__{item_id}.json"
    frontier_report = f"{base}/decoder_q8_norm_frontier__{item_id}.md"
    q8_recip_ppa = "control_plane/shadow_exports/l1_promotions/l1_decoder_q8_recip_norm_datapath_v1_r3.json"
    q8_exact_ppa = (
        "control_plane/shadow_exports/l1_promotions/"
        "l1_prop_l1_softmax_rowwise_int8_r8_acc24_block_v1_nangate45_r1.json"
    )
    bf16_recip_ppa = "control_plane/shadow_exports/l1_promotions/l1_decoder_bf16_recip_norm_datapath_v1_r2.json"
    rough_grid = "decoder_q8_normalization_frontier_v1"
    commands = [
        {
            "name": "generate_decoder_q8_norm_reference",
            "run": (
                "python3 npu/eval/gen_llm_decoder_reference_suite.py "
                f"--dataset-manifest {dataset_manifest} "
                f"--out-dir {reference_dir} "
                f"--out-manifest {reference_manifest}"
            ),
        },
        {
            "name": "generate_decoder_q8_norm_candidate",
            "run": (
                "python3 npu/eval/gen_llm_decoder_candidate_suite.py "
                f"--dataset-manifest {dataset_manifest} "
                f"--out-dir {candidate_dir} "
                f"--out-manifest {candidate_manifest}"
            ),
        },
        {
            "name": "validate_decoder_q8_norm_contract",
            "run": f"python3 npu/eval/validate_llm_decoder_contract.py --dataset-manifest {dataset_manifest} --out {validation_out}",
        },
        {
            "name": "compare_decoder_q8_norm_quality",
            "run": (
                "python3 npu/eval/compare_llm_decoder_quality.py "
                f"--reference-manifest {reference_manifest} "
                f"--candidate-manifest {candidate_manifest} "
                f"--out {quality_out}"
            ),
        },
        {
            "name": "sweep_decoder_q8_norm_frontier",
            "run": (
                "python3 npu/eval/sweep_llm_decoder_candidate_quality.py "
                f"--dataset-manifest {dataset_manifest} "
                f"--rough-grid {rough_grid} "
                f"--out-dir {sweep_dir} "
                f"--out {sweep_out}"
            ),
        },
        {
            "name": "estimate_decoder_q8_norm_frontier",
            "run": (
                "python3 npu/eval/estimate_llm_decoder_q8_norm_frontier.py "
                f"--sweep {sweep_out} "
                f"--q8-recip-ppa {q8_recip_ppa} "
                f"--q8-exact-ppa {q8_exact_ppa} "
                f"--bf16-recip-ppa {bf16_recip_ppa} "
                f"--out {frontier_out} "
                f"--out-md {frontier_report}"
            ),
        },
    ]
    return {
        "inputs": {
            "dataset_manifest": dataset_manifest,
            "sample_file": f"{base}/samples_prompt_stress_v1.jsonl",
            "reference_manifest": reference_manifest,
            "candidate_manifest": candidate_manifest,
            "reference_dir": reference_dir,
            "candidate_dir": candidate_dir,
            "validation_out": validation_out,
            "quality_out": quality_out,
            "candidate_sweep_dir": sweep_dir,
            "candidate_sweep_out": sweep_out,
            "candidate_sweep_grid": rough_grid,
            "frontier_out": frontier_out,
            "frontier_report": frontier_report,
            "q8_reciprocal_datapath_ppa": q8_recip_ppa,
            "q8_exact_datapath_ppa": q8_exact_ppa,
            "bf16_reciprocal_datapath_ppa": bf16_recip_ppa,
            "candidate_sweep_scope": (
                "focused q8 PWL normalization frontier over exact normalization and quantized reciprocal "
                "normalization bit widths on the prompt-stress dataset, with q8 exact and q8 reciprocal "
                "ranking backed by merged integrated datapath PPA when available"
            ),
        },
        "commands": commands,
        "expected_outputs": [
            reference_manifest,
            candidate_manifest,
            validation_out,
            quality_out,
            sweep_out,
            frontier_out,
            frontier_report,
        ],
    }


def _decoder_q8_normalization_distribution_evidence(*, item_id: str, distribution_version: str = "v1") -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_tiny_v1"
    version = str(distribution_version or "v1").strip()
    if version not in {"v1", "v2"}:
        raise Layer2TaskGenerationError(f"unsupported q8 normalization distribution version: {version}")
    dataset_manifest = f"{base}/manifest_distribution_{version}.json"
    sample_file = f"{base}/samples_distribution_{version}.jsonl"
    reference_dir = f"{base}/reference_distribution_{version}"
    reference_manifest = f"{base}/reference_distribution_{version}_manifest.json"
    candidate_dir = f"{base}/candidate_distribution_{version}"
    candidate_manifest = f"{base}/candidate_distribution_{version}_manifest.json"
    validation_out = f"{base}/decoder_contract_validation__{item_id}.json"
    quality_out = f"{base}/decoder_quality_compare__{item_id}.json"
    sweep_dir = f"{base}/candidate_sweeps/{item_id}"
    sweep_out = f"{base}/decoder_quality_sweep__{item_id}.json"
    frontier_out = f"{base}/decoder_q8_norm_frontier__{item_id}.json"
    frontier_report = f"{base}/decoder_q8_norm_frontier__{item_id}.md"
    q8_recip_ppa = "control_plane/shadow_exports/l1_promotions/l1_decoder_q8_recip_norm_datapath_v1_r3.json"
    q8_exact_ppa = (
        "control_plane/shadow_exports/l1_promotions/"
        "l1_prop_l1_softmax_rowwise_int8_r8_acc24_block_v1_nangate45_r1.json"
    )
    bf16_recip_ppa = "control_plane/shadow_exports/l1_promotions/l1_decoder_bf16_recip_norm_datapath_v1_r2.json"
    rough_grid = "decoder_q8_normalization_frontier_v1"
    command_suffix = "" if version == "v1" else f"_{version}"
    scope_note = "broader distribution" if version == "v1" else "expanded v2 broad distribution"
    commands = [
        {
            "name": f"generate_decoder_q8_norm_distribution{command_suffix}_reference",
            "run": (
                "python3 npu/eval/gen_llm_decoder_reference_suite.py "
                f"--dataset-manifest {dataset_manifest} "
                f"--out-dir {reference_dir} "
                f"--out-manifest {reference_manifest}"
            ),
        },
        {
            "name": f"generate_decoder_q8_norm_distribution{command_suffix}_candidate",
            "run": (
                "python3 npu/eval/gen_llm_decoder_candidate_suite.py "
                f"--dataset-manifest {dataset_manifest} "
                f"--out-dir {candidate_dir} "
                f"--out-manifest {candidate_manifest}"
            ),
        },
        {
            "name": f"validate_decoder_q8_norm_distribution{command_suffix}_contract",
            "run": f"python3 npu/eval/validate_llm_decoder_contract.py --dataset-manifest {dataset_manifest} --out {validation_out}",
        },
        {
            "name": f"compare_decoder_q8_norm_distribution{command_suffix}_quality",
            "run": (
                "python3 npu/eval/compare_llm_decoder_quality.py "
                f"--reference-manifest {reference_manifest} "
                f"--candidate-manifest {candidate_manifest} "
                f"--out {quality_out}"
            ),
        },
        {
            "name": f"sweep_decoder_q8_norm_distribution{command_suffix}_frontier",
            "run": (
                "python3 npu/eval/sweep_llm_decoder_candidate_quality.py "
                f"--dataset-manifest {dataset_manifest} "
                f"--rough-grid {rough_grid} "
                f"--out-dir {sweep_dir} "
                f"--out {sweep_out}"
            ),
        },
        {
            "name": f"estimate_decoder_q8_norm_distribution{command_suffix}_frontier",
            "run": (
                "python3 npu/eval/estimate_llm_decoder_q8_norm_frontier.py "
                f"--sweep {sweep_out} "
                f"--q8-recip-ppa {q8_recip_ppa} "
                f"--q8-exact-ppa {q8_exact_ppa} "
                f"--bf16-recip-ppa {bf16_recip_ppa} "
                f"--out {frontier_out} "
                f"--out-md {frontier_report}"
            ),
        },
    ]
    return {
        "inputs": {
            "dataset_manifest": dataset_manifest,
            "sample_file": sample_file,
            "reference_manifest": reference_manifest,
            "candidate_manifest": candidate_manifest,
            "reference_dir": reference_dir,
            "candidate_dir": candidate_dir,
            "validation_out": validation_out,
            "quality_out": quality_out,
            "candidate_sweep_dir": sweep_dir,
            "candidate_sweep_out": sweep_out,
            "candidate_sweep_grid": rough_grid,
            "frontier_out": frontier_out,
            "frontier_report": frontier_report,
            "q8_reciprocal_datapath_ppa": q8_recip_ppa,
            "q8_exact_datapath_ppa": q8_exact_ppa,
            "bf16_reciprocal_datapath_ppa": bf16_recip_ppa,
            "candidate_sweep_scope": (
                f"{scope_note} robustness check for the q8-vs-bf16 normalization frontier "
                "using the same q8 reciprocal bit-width grid and "
                "measured q8/bf16 normalization datapath PPA artifacts"
            ),
        },
        "commands": commands,
        "expected_outputs": [
            reference_manifest,
            candidate_manifest,
            validation_out,
            quality_out,
            sweep_out,
            frontier_out,
            frontier_report,
        ],
    }


def _decoder_quantization_outline_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_tiny_v1"
    fp_sweep = f"{base}/decoder_quality_sweep__l2_decoder_fp_probability_format_sweep_v1.json"
    distribution_sweep = f"{base}/decoder_quality_sweep__l2_decoder_distribution_robustness_v1.json"
    q8_norm_frontier = f"{base}/decoder_q8_norm_frontier__l2_decoder_q8_normalization_frontier_v1.json"
    outline_out = f"{base}/decoder_quantization_outline__{item_id}.json"
    outline_report = f"{base}/decoder_quantization_outline__{item_id}.md"
    commands = [
        {
            "name": "estimate_decoder_quantization_outline",
            "run": (
                "python3 npu/eval/estimate_llm_decoder_quantization_outline.py "
                f"--fp-sweep {fp_sweep} "
                f"--distribution-sweep {distribution_sweep} "
                f"--q8-norm-frontier {q8_norm_frontier} "
                f"--out {outline_out} "
                f"--out-md {outline_report}"
            ),
        },
    ]
    return {
        "inputs": {
            "fp_format_sweep": fp_sweep,
            "distribution_robustness_sweep": distribution_sweep,
            "q8_normalization_frontier": q8_norm_frontier,
            "quantization_outline_out": outline_out,
            "quantization_outline_report": outline_report,
            "quantization_outline_scope": (
                "multi-dimensional decoder quantization interpretation over existing fp-format, "
                "distribution robustness, and measured q8 normalization frontier evidence; dimensions "
                "are grouped to avoid cross-category ranking"
            ),
        },
        "commands": commands,
        "expected_outputs": [
            outline_out,
            outline_report,
        ],
    }


def _decoder_pwl_failure_diagnosis_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_tiny_v1"
    sweep = f"{base}/decoder_quality_sweep__l2_decoder_q8_norm_distribution_broad_v2.json"
    sample_file = f"{base}/samples_distribution_v2.jsonl"
    diagnosis_out = f"{base}/decoder_pwl_failure_diagnosis__{item_id}.json"
    diagnosis_report = f"{base}/decoder_pwl_failure_diagnosis__{item_id}.md"
    commands = [
        {
            "name": "diagnose_decoder_pwl_failures",
            "run": (
                "python3 npu/eval/diagnose_llm_decoder_pwl_failures.py "
                f"--sweep {sweep} "
                f"--sample-file {sample_file} "
                f"--out {diagnosis_out} "
                f"--out-md {diagnosis_report}"
            ),
        },
    ]
    return {
        "inputs": {
            "source_sweep": sweep,
            "sample_file": sample_file,
            "diagnosis_out": diagnosis_out,
            "diagnosis_report": diagnosis_report,
            "focus_samples": [
                "dist2_arith_three_plus_five",
                "dist2_sequence_months",
            ],
            "control_samples": [
                "dist2_arith_two_plus_two",
                "dist2_arith_six_times_two",
                "dist2_sequence_numbers",
                "dist2_sequence_weekdays",
            ],
            "diagnosis_scope": (
                "focused per-sample diagnosis for the shared PWL exact-token misses found "
                "in the broad v2 q8/bf16 normalization distribution result"
            ),
        },
        "commands": commands,
        "expected_outputs": [
            diagnosis_out,
            diagnosis_report,
        ],
    }


def _decoder_bf16_pwl_recoverability_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_tiny_v1"
    sweep = f"{base}/decoder_quality_sweep__l2_decoder_q8_norm_distribution_broad_v2.json"
    sample_file = f"{base}/samples_distribution_v2.jsonl"
    recoverability_out = f"{base}/decoder_bf16_pwl_recoverability__{item_id}.json"
    recoverability_report = f"{base}/decoder_bf16_pwl_recoverability__{item_id}.md"
    commands = [
        {
            "name": "estimate_decoder_bf16_pwl_recoverability",
            "run": (
                "python3 npu/eval/estimate_llm_decoder_bf16_recoverability.py "
                f"--sweep {sweep} "
                f"--sample-file {sample_file} "
                f"--out {recoverability_out} "
                f"--out-md {recoverability_report}"
            ),
        },
    ]
    return {
        "inputs": {
            "source_sweep": sweep,
            "sample_file": sample_file,
            "recoverability_out": recoverability_out,
            "recoverability_report": recoverability_report,
            "target_template": "grid_approx_pwl_bf16_path",
            "recoverability_scope": (
                "score-gap screen for whether bf16/PWL exact-next misses are small-margin "
                "top-k-contained cases that are worth testing with QAT or fine-tuning"
            ),
        },
        "commands": commands,
        "expected_outputs": [
            recoverability_out,
            recoverability_report,
        ],
    }


def _decoder_bf16_pwl_recovery_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_tiny_v1"
    dataset_manifest = f"{base}/manifest_distribution_v2.json"
    sample_file = f"{base}/samples_distribution_v2.jsonl"
    reference_dir = f"{base}/reference_distribution_v2"
    reference_manifest = f"{base}/reference_distribution_v2_manifest.json"
    candidate_dir = f"{base}/candidate_distribution_v2"
    candidate_manifest = f"{base}/candidate_distribution_v2_manifest.json"
    validation_out = f"{base}/decoder_contract_validation__{item_id}.json"
    quality_out = f"{base}/decoder_quality_compare__{item_id}.json"
    sweep_dir = f"{base}/candidate_sweeps/{item_id}"
    sweep_out = f"{base}/decoder_quality_sweep__{item_id}.json"
    recovery_out = f"{base}/decoder_bf16_pwl_recovery__{item_id}.json"
    recovery_report = f"{base}/decoder_bf16_pwl_recovery__{item_id}.md"
    rough_grid = "decoder_bf16_pwl_recovery_v1"
    commands = [
        {
            "name": "generate_decoder_bf16_pwl_recovery_reference",
            "run": (
                "python3 npu/eval/gen_llm_decoder_reference_suite.py "
                f"--dataset-manifest {dataset_manifest} "
                f"--out-dir {reference_dir} "
                f"--out-manifest {reference_manifest}"
            ),
        },
        {
            "name": "generate_decoder_bf16_pwl_recovery_candidate",
            "run": (
                "python3 npu/eval/gen_llm_decoder_candidate_suite.py "
                f"--dataset-manifest {dataset_manifest} "
                f"--out-dir {candidate_dir} "
                f"--out-manifest {candidate_manifest}"
            ),
        },
        {
            "name": "validate_decoder_bf16_pwl_recovery_contract",
            "run": f"python3 npu/eval/validate_llm_decoder_contract.py --dataset-manifest {dataset_manifest} --out {validation_out}",
        },
        {
            "name": "compare_decoder_bf16_pwl_recovery_quality",
            "run": (
                "python3 npu/eval/compare_llm_decoder_quality.py "
                f"--reference-manifest {reference_manifest} "
                f"--candidate-manifest {candidate_manifest} "
                f"--out {quality_out}"
            ),
        },
        {
            "name": "sweep_decoder_bf16_pwl_recovery",
            "run": (
                "python3 npu/eval/sweep_llm_decoder_candidate_quality.py "
                f"--dataset-manifest {dataset_manifest} "
                f"--rough-grid {rough_grid} "
                f"--out-dir {sweep_dir} "
                f"--out {sweep_out}"
            ),
        },
        {
            "name": "summarize_decoder_bf16_pwl_recovery",
            "run": (
                "python3 npu/eval/summarize_llm_decoder_bf16_pwl_recovery.py "
                f"--sweep {sweep_out} "
                f"--out {recovery_out} "
                f"--out-md {recovery_report}"
            ),
        },
    ]
    return {
        "inputs": {
            "dataset_manifest": dataset_manifest,
            "sample_file": sample_file,
            "reference_dir": reference_dir,
            "reference_manifest": reference_manifest,
            "candidate_dir": candidate_dir,
            "candidate_manifest": candidate_manifest,
            "validation_out": validation_out,
            "quality_out": quality_out,
            "candidate_sweep_dir": sweep_dir,
            "candidate_sweep_out": sweep_out,
            "candidate_sweep_grid": rough_grid,
            "recovery_out": recovery_out,
            "recovery_report": recovery_report,
            "recovery_scope": (
                "narrow bf16/PWL calibration proxy that preserves the same score arithmetic and "
                "tests whether logit tie-breaking recovers equal-score exact-next losses"
            ),
        },
        "commands": commands,
        "expected_outputs": [
            reference_manifest,
            candidate_manifest,
            validation_out,
            quality_out,
            sweep_out,
            recovery_out,
            recovery_report,
        ],
    }


def _decoder_bf16_pwl_scale_probe_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_tiny_v1"
    dataset_manifest = f"{base}/manifest_scale_proxy_v1.json"
    sample_file = f"{base}/samples_scale_proxy_v1.jsonl"
    reference_dir = f"{base}/reference_scale_proxy_v1"
    reference_manifest = f"{base}/reference_scale_proxy_v1_manifest.json"
    candidate_dir = f"{base}/candidate_scale_proxy_v1"
    candidate_manifest = f"{base}/candidate_scale_proxy_v1_manifest.json"
    validation_out = f"{base}/decoder_contract_validation__{item_id}.json"
    quality_out = f"{base}/decoder_quality_compare__{item_id}.json"
    sweep_dir = f"{base}/candidate_sweeps/{item_id}"
    sweep_out = f"{base}/decoder_quality_sweep__{item_id}.json"
    recovery_out = f"{base}/decoder_bf16_pwl_scale_probe__{item_id}.json"
    recovery_report = f"{base}/decoder_bf16_pwl_scale_probe__{item_id}.md"
    rough_grid = "decoder_bf16_pwl_scale_probe_v1"
    commands = [
        {
            "name": "generate_decoder_bf16_pwl_scale_probe_reference",
            "run": (
                "python3 npu/eval/gen_llm_decoder_reference_suite.py "
                f"--dataset-manifest {dataset_manifest} "
                f"--out-dir {reference_dir} "
                f"--out-manifest {reference_manifest}"
            ),
        },
        {
            "name": "generate_decoder_bf16_pwl_scale_probe_candidate",
            "run": (
                "python3 npu/eval/gen_llm_decoder_candidate_suite.py "
                f"--dataset-manifest {dataset_manifest} "
                f"--out-dir {candidate_dir} "
                f"--out-manifest {candidate_manifest}"
            ),
        },
        {
            "name": "validate_decoder_bf16_pwl_scale_probe_contract",
            "run": f"python3 npu/eval/validate_llm_decoder_contract.py --dataset-manifest {dataset_manifest} --out {validation_out}",
        },
        {
            "name": "compare_decoder_bf16_pwl_scale_probe_quality",
            "run": (
                "python3 npu/eval/compare_llm_decoder_quality.py "
                f"--reference-manifest {reference_manifest} "
                f"--candidate-manifest {candidate_manifest} "
                f"--out {quality_out}"
            ),
        },
        {
            "name": "sweep_decoder_bf16_pwl_scale_probe",
            "run": (
                "python3 npu/eval/sweep_llm_decoder_candidate_quality.py "
                f"--dataset-manifest {dataset_manifest} "
                f"--rough-grid {rough_grid} "
                f"--out-dir {sweep_dir} "
                f"--out {sweep_out}"
            ),
        },
        {
            "name": "summarize_decoder_bf16_pwl_scale_probe",
            "run": (
                "python3 npu/eval/summarize_llm_decoder_bf16_pwl_recovery.py "
                f"--sweep {sweep_out} "
                f"--out {recovery_out} "
                f"--out-md {recovery_report}"
            ),
        },
    ]
    return {
        "inputs": {
            "dataset_manifest": dataset_manifest,
            "sample_file": sample_file,
            "reference_dir": reference_dir,
            "reference_manifest": reference_manifest,
            "candidate_dir": candidate_dir,
            "candidate_manifest": candidate_manifest,
            "validation_out": validation_out,
            "quality_out": quality_out,
            "candidate_sweep_dir": sweep_dir,
            "candidate_sweep_out": sweep_out,
            "candidate_sweep_grid": rough_grid,
            "scale_probe_out": recovery_out,
            "scale_probe_report": recovery_report,
            "scale_probe_scope": (
                "scale-sensitivity screen for the bf16/PWL plus logit tie-break path using "
                "larger top-k rank pressure and broader prompt regimes on the tiny decoder harness; "
                "not a substitute for a larger-model evaluation"
            ),
        },
        "commands": commands,
        "expected_outputs": [
            reference_manifest,
            candidate_manifest,
            validation_out,
            quality_out,
            sweep_out,
            recovery_out,
            recovery_report,
        ],
    }


def _decoder_trained_tiny_quality_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_trained_tiny_v1"
    dataset_manifest = f"{base}/manifest.json"
    sample_file = f"{base}/samples.jsonl"
    reference_dir = f"{base}/reference"
    reference_manifest = f"{base}/reference_manifest.json"
    candidate_dir = f"{base}/candidate"
    candidate_manifest = f"{base}/candidate_manifest.json"
    validation_out = f"{base}/decoder_contract_validation__{item_id}.json"
    quality_out = f"{base}/decoder_quality_compare__{item_id}.json"
    sweep_dir = f"{base}/candidate_sweeps/{item_id}"
    sweep_out = f"{base}/decoder_quality_sweep__{item_id}.json"
    trained_out = f"{base}/decoder_trained_tiny_quality__{item_id}.json"
    trained_report = f"{base}/decoder_trained_tiny_quality__{item_id}.md"
    rough_grid = "decoder_bf16_pwl_scale_probe_v1"
    commands = [
        {
            "name": "generate_decoder_trained_tiny_reference",
            "run": (
                "python3 npu/eval/gen_llm_decoder_reference_suite.py "
                f"--dataset-manifest {dataset_manifest} "
                f"--out-dir {reference_dir} "
                f"--out-manifest {reference_manifest}"
            ),
        },
        {
            "name": "generate_decoder_trained_tiny_candidate",
            "run": (
                "python3 npu/eval/gen_llm_decoder_candidate_suite.py "
                f"--dataset-manifest {dataset_manifest} "
                f"--out-dir {candidate_dir} "
                f"--out-manifest {candidate_manifest}"
            ),
        },
        {
            "name": "validate_decoder_trained_tiny_contract",
            "run": f"python3 npu/eval/validate_llm_decoder_contract.py --dataset-manifest {dataset_manifest} --out {validation_out}",
        },
        {
            "name": "compare_decoder_trained_tiny_quality",
            "run": (
                "python3 npu/eval/compare_llm_decoder_quality.py "
                f"--reference-manifest {reference_manifest} "
                f"--candidate-manifest {candidate_manifest} "
                f"--out {quality_out}"
            ),
        },
        {
            "name": "sweep_decoder_trained_tiny_quality",
            "run": (
                "python3 npu/eval/sweep_llm_decoder_candidate_quality.py "
                f"--dataset-manifest {dataset_manifest} "
                f"--rough-grid {rough_grid} "
                f"--out-dir {sweep_dir} "
                f"--out {sweep_out}"
            ),
        },
        {
            "name": "summarize_decoder_trained_tiny_quality",
            "run": (
                "python3 npu/eval/summarize_llm_decoder_bf16_pwl_recovery.py "
                f"--sweep {sweep_out} "
                f"--out {trained_out} "
                f"--out-md {trained_report}"
            ),
        },
    ]
    return {
        "inputs": {
            "dataset_manifest": dataset_manifest,
            "sample_file": sample_file,
            "reference_dir": reference_dir,
            "reference_manifest": reference_manifest,
            "candidate_dir": candidate_dir,
            "candidate_manifest": candidate_manifest,
            "validation_out": validation_out,
            "quality_out": quality_out,
            "candidate_sweep_dir": sweep_dir,
            "candidate_sweep_out": sweep_out,
            "candidate_sweep_grid": rough_grid,
            "trained_quality_out": trained_out,
            "trained_quality_report": trained_report,
            "trained_quality_scope": (
                "first trained-weight GPT-2-family decoder smoke using the existing bf16/PWL "
                "quality harness; gate this before scaling to distilgpt2 or GPT-2"
            ),
        },
        "commands": commands,
        "expected_outputs": [
            reference_manifest,
            candidate_manifest,
            validation_out,
            quality_out,
            sweep_out,
            trained_out,
            trained_report,
        ],
    }


def _decoder_distilgpt2_quality_evidence_for_dataset(
    *,
    item_id: str,
    base: str,
    dataset_id: str,
    output_prefix: str,
    command_suffix: str,
    materialized_model_scope: str,
    trained_quality_scope: str,
    dataset_status: str,
    dataset_notes: str,
    command_family: str = "distilgpt2",
    hf_model_id: str = "distilgpt2",
    contract_id: str = "llm_decoder_distilgpt2_trained_v1",
    model_dir: str = "runs/models/llm_decoder_distilgpt2_trained_v1",
    tokenizer_dir: str = "runs/tokenizers/llm_decoder_distilgpt2_trained_v1",
) -> dict[str, Any]:
    dataset_manifest = f"{base}/manifest.json"
    sample_file = f"{base}/samples.jsonl"
    reference_dir = f"{base}/reference"
    reference_manifest = f"{base}/reference_manifest.json"
    candidate_dir = f"{base}/candidate"
    candidate_manifest = f"{base}/candidate_manifest.json"
    validation_out = f"{base}/decoder_contract_validation__{item_id}.json"
    quality_out = f"{base}/decoder_quality_compare__{item_id}.json"
    sweep_dir = f"{base}/candidate_sweeps/{item_id}"
    sweep_out = f"{base}/decoder_quality_sweep__{item_id}.json"
    trained_out = f"{base}/{output_prefix}__{item_id}.json"
    trained_report = f"{base}/{output_prefix}__{item_id}.md"
    rough_grid = "decoder_bf16_pwl_scale_probe_v1"
    name_mid = f"_{command_suffix}" if command_suffix else ""
    commands = [
        {
            "name": f"materialize_decoder_{command_family}{name_mid}_contract",
            "run": (
                "bash npu/eval/run_hf_decoder_materializer.sh "
                f"--model-id {shlex.quote(hf_model_id)} "
                f"--contract-id {contract_id} "
                f"--model-dir {model_dir} "
                f"--tokenizer-dir {tokenizer_dir} "
                f"--dataset-id {dataset_id} "
                f"--dataset-dir {base} "
                f"--sample-file {sample_file} "
                f"--dataset-status {dataset_status} "
                f"--dataset-notes {shlex.quote(dataset_notes)}"
            ),
        },
        {
            "name": f"generate_decoder_{command_family}{name_mid}_reference",
            "run": (
                "python3 npu/eval/gen_llm_decoder_reference_suite.py "
                f"--dataset-manifest {dataset_manifest} "
                f"--out-dir {reference_dir} "
                f"--out-manifest {reference_manifest}"
            ),
        },
        {
            "name": f"generate_decoder_{command_family}{name_mid}_candidate",
            "run": (
                "python3 npu/eval/gen_llm_decoder_candidate_suite.py "
                f"--dataset-manifest {dataset_manifest} "
                f"--out-dir {candidate_dir} "
                f"--out-manifest {candidate_manifest}"
            ),
        },
        {
            "name": f"validate_decoder_{command_family}{name_mid}_contract",
            "run": f"python3 npu/eval/validate_llm_decoder_contract.py --dataset-manifest {dataset_manifest} --out {validation_out}",
        },
        {
            "name": f"compare_decoder_{command_family}{name_mid}_quality",
            "run": (
                "python3 npu/eval/compare_llm_decoder_quality.py "
                f"--reference-manifest {reference_manifest} "
                f"--candidate-manifest {candidate_manifest} "
                f"--out {quality_out}"
            ),
        },
        {
            "name": f"sweep_decoder_{command_family}{name_mid}_quality",
            "run": (
                "python3 npu/eval/sweep_llm_decoder_candidate_quality.py "
                f"--dataset-manifest {dataset_manifest} "
                f"--rough-grid {rough_grid} "
                f"--out-dir {sweep_dir} "
                f"--out {sweep_out}"
            ),
        },
        {
            "name": f"summarize_decoder_{command_family}{name_mid}_quality",
            "run": (
                "python3 npu/eval/summarize_llm_decoder_bf16_pwl_recovery.py "
                f"--sweep {sweep_out} "
                f"--out {trained_out} "
                f"--out-md {trained_report}"
            ),
        },
    ]
    return {
        "inputs": {
            "dataset_manifest": dataset_manifest,
            "sample_file": sample_file,
            "reference_dir": reference_dir,
            "reference_manifest": reference_manifest,
            "candidate_dir": candidate_dir,
            "candidate_manifest": candidate_manifest,
            "validation_out": validation_out,
            "quality_out": quality_out,
            "candidate_sweep_dir": sweep_dir,
            "candidate_sweep_out": sweep_out,
            "candidate_sweep_grid": rough_grid,
            "trained_quality_out": trained_out,
            "trained_quality_report": trained_report,
            "materialized_model_contract": f"{model_dir}/model_contract.json",
            "materialized_tokenizer_manifest": f"{tokenizer_dir}/manifest.json",
            "materialized_model_scope": materialized_model_scope,
            "trained_quality_scope": trained_quality_scope,
        },
        "commands": commands,
        "expected_outputs": [
            dataset_manifest,
            reference_manifest,
            candidate_manifest,
            validation_out,
            quality_out,
            sweep_out,
            trained_out,
            trained_report,
        ],
    }


def _decoder_distilgpt2_quality_evidence(*, item_id: str) -> dict[str, Any]:
    return _decoder_distilgpt2_quality_evidence_for_dataset(
        item_id=item_id,
        base="runs/datasets/llm_decoder_eval_distilgpt2_trained_v1",
        dataset_id="llm_decoder_eval_distilgpt2_trained_v1",
        output_prefix="decoder_distilgpt2_quality",
        command_suffix="",
        materialized_model_scope=(
            "distilgpt2 trained-checkpoint confirmation using evaluator-local generated "
            "ONNX/tokenizer artifacts; generated model files are intentionally gitignored"
        ),
        trained_quality_scope=(
            "larger trained GPT-2-family confirmation for the bf16/PWL logit tie-break "
            "frontier after the trained tiny smoke recovered exact-next behavior"
        ),
        dataset_status="materialized_distilgpt2_quality_manifest_v1",
        dataset_notes=(
            "distilgpt2 trained-checkpoint confirmation dataset. Run materialize_hf_decoder_contract.py "
            "before generating reference/candidate manifests because the model/tokenizer artifacts are gitignored."
        ),
    )


def _decoder_gpt2_quality_evidence(*, item_id: str) -> dict[str, Any]:
    return _decoder_distilgpt2_quality_evidence_for_dataset(
        item_id=item_id,
        base="runs/datasets/llm_decoder_eval_gpt2_trained_v1",
        dataset_id="llm_decoder_eval_gpt2_trained_v1",
        output_prefix="decoder_gpt2_quality",
        command_suffix="",
        command_family="gpt2",
        hf_model_id="gpt2",
        contract_id="llm_decoder_gpt2_trained_v1",
        model_dir="runs/models/llm_decoder_gpt2_trained_v1",
        tokenizer_dir="runs/tokenizers/llm_decoder_gpt2_trained_v1",
        materialized_model_scope=(
            "GPT-2 trained-checkpoint confirmation using evaluator-local generated "
            "ONNX/tokenizer artifacts; generated model files are intentionally gitignored"
        ),
        trained_quality_scope=(
            "larger 12-layer GPT-2 checkpoint confirmation for the bf16/PWL frontier after "
            "distilgpt2 prompt-stress stayed exact-safe"
        ),
        dataset_status="materialized_gpt2_quality_manifest_v1",
        dataset_notes=(
            "GPT-2 trained-checkpoint confirmation dataset. Run materialize_hf_decoder_contract.py "
            "before generating reference/candidate manifests because the model/tokenizer artifacts are gitignored."
        ),
    )


def _decoder_gpt2_prompt_stress_evidence(*, item_id: str) -> dict[str, Any]:
    return _decoder_distilgpt2_quality_evidence_for_dataset(
        item_id=item_id,
        base="runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1",
        dataset_id="llm_decoder_eval_gpt2_prompt_stress_v1",
        output_prefix="decoder_gpt2_prompt_stress",
        command_suffix="prompt_stress",
        command_family="gpt2",
        hf_model_id="gpt2",
        contract_id="llm_decoder_gpt2_trained_v1",
        model_dir="runs/models/llm_decoder_gpt2_trained_v1",
        tokenizer_dir="runs/tokenizers/llm_decoder_gpt2_trained_v1",
        materialized_model_scope=(
            "GPT-2 prompt-stress confirmation using evaluator-local generated ONNX/tokenizer "
            "artifacts; generated model files are intentionally gitignored and shared with the "
            "GPT-2 quality gate"
        ),
        trained_quality_scope=(
            "broader prompt/input-distribution stress check on GPT-2 small after the 24-sample "
            "GPT-2 checkpoint gate stayed exact-safe"
        ),
        dataset_status="materialized_gpt2_prompt_stress_manifest_v1",
        dataset_notes=(
            "GPT-2 prompt-stress dataset. Run materialize_hf_decoder_contract.py before generating "
            "reference/candidate manifests because the model/tokenizer artifacts are gitignored."
        ),
    )


def _decoder_gpt2_tie_rank_frontier_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    recovery = f"{base}/decoder_gpt2_prompt_stress__l2_decoder_gpt2_prompt_stress_v1.json"
    frontier_out = f"{base}/decoder_gpt2_tie_rank_frontier__{item_id}.json"
    frontier_report = f"{base}/decoder_gpt2_tie_rank_frontier__{item_id}.md"
    bf16_recip_ppa = "control_plane/shadow_exports/l1_promotions/l1_decoder_bf16_recip_norm_datapath_v1_r2.json"
    bf16_tie_rank_ppa = "control_plane/shadow_exports/l1_promotions/l1_decoder_bf16_pwl_tie_rank_datapath_v1_r2.json"
    return {
        "inputs": {
            "source_recovery": recovery,
            "bf16_reciprocal_datapath_ppa": bf16_recip_ppa,
            "bf16_score_tie_rank_datapath_ppa": bf16_tie_rank_ppa,
            "frontier_out": frontier_out,
            "frontier_report": frontier_report,
            "frontier_scope": (
                "hardware-plausibility gate for GPT-2 prompt-stress bf16/PWL logit tie-rank recovery "
                "using merged row-8 Nangate45 bf16 reciprocal and score-tie-rank component PPA"
            ),
        },
        "commands": [
            {
                "name": "estimate_decoder_gpt2_tie_rank_frontier",
                "run": (
                    "python3 npu/eval/estimate_llm_decoder_tie_rank_frontier.py "
                    f"--recovery {recovery} "
                    f"--bf16-recip-ppa {bf16_recip_ppa} "
                    f"--bf16-tie-rank-ppa {bf16_tie_rank_ppa} "
                    f"--out {frontier_out} "
                    f"--out-md {frontier_report}"
                ),
            },
        ],
        "expected_outputs": [frontier_out, frontier_report],
    }


def _decoder_gpt2_logit_rank_bypass_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    dataset_id = "llm_decoder_eval_gpt2_prompt_stress_v1"
    dataset_manifest = f"{base}/manifest.json"
    sample_file = f"{base}/samples.jsonl"
    reference_dir = f"{base}/reference"
    reference_manifest = f"{base}/reference_manifest.json"
    candidate_dir = f"{base}/candidate"
    candidate_manifest = f"{base}/candidate_manifest.json"
    validation_out = f"{base}/decoder_contract_validation__{item_id}.json"
    quality_out = f"{base}/decoder_quality_compare__{item_id}.json"
    sweep_dir = f"{base}/candidate_sweeps/{item_id}"
    sweep_out = f"{base}/decoder_quality_sweep__{item_id}.json"
    bypass_out = f"{base}/decoder_gpt2_logit_rank_bypass__{item_id}.json"
    bypass_report = f"{base}/decoder_gpt2_logit_rank_bypass__{item_id}.md"
    rough_grid = "decoder_logit_rank_bypass_v1"
    rank_ppa = "control_plane/shadow_exports/l1_promotions/l1_decoder_logit_rank_datapath_v1_r2.json"
    commands = [
        {
            "name": "materialize_decoder_gpt2_logit_rank_bypass_contract",
            "run": (
                "bash npu/eval/run_hf_decoder_materializer.sh "
                "--model-id gpt2 "
                "--contract-id llm_decoder_gpt2_trained_v1 "
                "--model-dir runs/models/llm_decoder_gpt2_trained_v1 "
                "--tokenizer-dir runs/tokenizers/llm_decoder_gpt2_trained_v1 "
                f"--dataset-id {dataset_id} "
                f"--dataset-dir {base} "
                f"--sample-file {sample_file} "
                "--dataset-status materialized_gpt2_logit_rank_bypass_manifest_v1 "
                "--dataset-notes 'GPT-2 prompt-stress logit-rank bypass dataset. Run materialization because model/tokenizer artifacts are gitignored.'"
            ),
        },
        {
            "name": "generate_decoder_gpt2_logit_rank_bypass_reference",
            "run": (
                "python3 npu/eval/gen_llm_decoder_reference_suite.py "
                f"--dataset-manifest {dataset_manifest} "
                f"--out-dir {reference_dir} "
                f"--out-manifest {reference_manifest}"
            ),
        },
        {
            "name": "generate_decoder_gpt2_logit_rank_bypass_candidate",
            "run": (
                "python3 npu/eval/gen_llm_decoder_candidate_suite.py "
                f"--dataset-manifest {dataset_manifest} "
                f"--out-dir {candidate_dir} "
                f"--out-manifest {candidate_manifest}"
            ),
        },
        {
            "name": "validate_decoder_gpt2_logit_rank_bypass_contract",
            "run": f"python3 npu/eval/validate_llm_decoder_contract.py --dataset-manifest {dataset_manifest} --out {validation_out}",
        },
        {
            "name": "compare_decoder_gpt2_logit_rank_bypass_quality",
            "run": (
                "python3 npu/eval/compare_llm_decoder_quality.py "
                f"--reference-manifest {reference_manifest} "
                f"--candidate-manifest {candidate_manifest} "
                f"--out {quality_out}"
            ),
        },
        {
            "name": "sweep_decoder_gpt2_logit_rank_bypass_quality",
            "run": (
                "python3 npu/eval/sweep_llm_decoder_candidate_quality.py "
                f"--dataset-manifest {dataset_manifest} "
                f"--rough-grid {rough_grid} "
                f"--out-dir {sweep_dir} "
                f"--out {sweep_out}"
            ),
        },
        {
            "name": "summarize_decoder_gpt2_logit_rank_bypass",
            "run": (
                "python3 npu/eval/summarize_llm_decoder_logit_rank_bypass.py "
                f"--sweep {sweep_out} "
                f"--rank-ppa {rank_ppa} "
                f"--out {bypass_out} "
                f"--out-md {bypass_report}"
            ),
        },
    ]
    return {
        "inputs": {
            "dataset_manifest": dataset_manifest,
            "sample_file": sample_file,
            "reference_dir": reference_dir,
            "reference_manifest": reference_manifest,
            "candidate_dir": candidate_dir,
            "candidate_manifest": candidate_manifest,
            "validation_out": validation_out,
            "quality_out": quality_out,
            "candidate_sweep_dir": sweep_dir,
            "candidate_sweep_out": sweep_out,
            "candidate_sweep_grid": rough_grid,
            "logit_rank_bypass_out": bypass_out,
            "logit_rank_bypass_report": bypass_report,
            "rank_datapath_ppa": rank_ppa,
            "logit_rank_bypass_scope": (
                "greedy/top-k GPT-2 prompt-stress check that bypasses softmax and ranks transformed logits "
                "directly; sampling modes remain out of scope because they require probabilities; "
                "rank cost is anchored to the measured logit-only argmax/top-k Layer 1 datapath"
            ),
        },
        "commands": commands,
        "expected_outputs": [
            dataset_manifest,
            reference_manifest,
            candidate_manifest,
            validation_out,
            quality_out,
            sweep_out,
            bypass_out,
            bypass_report,
        ],
    }


def _decoder_logit_rank_streaming_hierarchy_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    prompt_stress = f"{base}/decoder_gpt2_prompt_stress__l2_decoder_gpt2_prompt_stress_v1.json"
    logit_rank_bypass = f"{base}/decoder_gpt2_logit_rank_bypass__l2_decoder_gpt2_logit_rank_bypass_v1.json"
    hierarchy_out = f"{base}/decoder_logit_rank_streaming_hierarchy__{item_id}.json"
    hierarchy_report = f"{base}/decoder_logit_rank_streaming_hierarchy__{item_id}.md"
    rank_ppa = "control_plane/shadow_exports/l1_promotions/l1_decoder_logit_rank_datapath_v1_r2.json"
    scale_ppa = "control_plane/shadow_exports/l1_promotions/l1_decoder_logit_rank_scale_v1.json"
    candidate_merge_ppa = (
        "control_plane/shadow_exports/l1_promotions/l1_decoder_candidate_stream_merge_fifo_v1.json"
    )
    return {
        "inputs": {
            "source_prompt_stress": prompt_stress,
            "source_logit_rank_bypass": logit_rank_bypass,
            "rank_datapath_ppa": rank_ppa,
            "rank_scale_ppa": scale_ppa,
            "candidate_merge_ppa": candidate_merge_ppa,
            "streaming_hierarchy_out": hierarchy_out,
            "streaming_hierarchy_report": hierarchy_report,
            "streaming_hierarchy_scope": (
                "GPT-2 prompt-stress planning gate for a streaming hierarchy decoder that ranks logits "
                "directly and avoids full-vocabulary probability materialization for greedy/top-k modes"
            ),
        },
        "commands": [
            {
                "name": "estimate_decoder_logit_rank_streaming_hierarchy",
                "run": (
                    "python3 npu/eval/estimate_llm_decoder_logit_rank_streaming_hierarchy.py "
                    f"--prompt-stress {prompt_stress} "
                    f"--logit-rank-bypass {logit_rank_bypass} "
                    f"--rank-ppa {rank_ppa} "
                    f"--scale-ppa {scale_ppa} "
                    f"--candidate-merge-ppa {candidate_merge_ppa} "
                    f"--out {hierarchy_out} "
                    f"--out-md {hierarchy_report}"
                ),
            },
        ],
        "expected_outputs": [hierarchy_out, hierarchy_report],
    }


def _decoder_logit_rank_streaming_overlap_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    prompt_stress = f"{base}/decoder_gpt2_prompt_stress__l2_decoder_gpt2_prompt_stress_v1.json"
    logit_rank_bypass = f"{base}/decoder_gpt2_logit_rank_bypass__l2_decoder_gpt2_logit_rank_bypass_v1.json"
    overlap_out = f"{base}/decoder_logit_rank_streaming_overlap__{item_id}.json"
    overlap_report = f"{base}/decoder_logit_rank_streaming_overlap__{item_id}.md"
    rank_ppa = "control_plane/shadow_exports/l1_promotions/l1_decoder_logit_rank_datapath_v1_r2.json"
    scale_ppa = "control_plane/shadow_exports/l1_promotions/l1_decoder_logit_rank_scale_v1.json"
    candidate_merge_ppa = (
        "control_plane/shadow_exports/l1_promotions/l1_decoder_candidate_stream_merge_fifo_v1.json"
    )
    return {
        "inputs": {
            "source_prompt_stress": prompt_stress,
            "source_logit_rank_bypass": logit_rank_bypass,
            "rank_datapath_ppa": rank_ppa,
            "rank_scale_ppa": scale_ppa,
            "candidate_merge_ppa": candidate_merge_ppa,
            "streaming_overlap_out": overlap_out,
            "streaming_overlap_report": overlap_report,
            "streaming_overlap_scope": (
                "Refine the decoder logit-rank streaming hierarchy with measured candidate-stream "
                "merge/FIFO PPA, producer-overlap, FIFO, candidate-traffic, and perf-sim/RTL "
                "equivalence observables"
            ),
        },
        "commands": [
            {
                "name": "estimate_decoder_logit_rank_streaming_overlap",
                "run": (
                    "python3 npu/eval/estimate_llm_decoder_logit_rank_streaming_hierarchy.py "
                    f"--prompt-stress {prompt_stress} "
                    f"--logit-rank-bypass {logit_rank_bypass} "
                    f"--rank-ppa {rank_ppa} "
                    f"--scale-ppa {scale_ppa} "
                    f"--candidate-merge-ppa {candidate_merge_ppa} "
                    "--producer-lanes-list 8,16,32 "
                    "--top-k-list 1,4 "
                    "--producer-ii-cycles-list 1,2,4 "
                    "--global-merge-ii-cycles 1,2,4 "
                    "--candidate-fifo-depth-groups-list 16,256,4096 "
                    f"--out {overlap_out} "
                    f"--out-md {overlap_report}"
                ),
            },
        ],
        "expected_outputs": [overlap_out, overlap_report],
    }


def _decoder_distilgpt2_prompt_stress_evidence(*, item_id: str) -> dict[str, Any]:
    return _decoder_distilgpt2_quality_evidence_for_dataset(
        item_id=item_id,
        base="runs/datasets/llm_decoder_eval_distilgpt2_prompt_stress_v1",
        dataset_id="llm_decoder_eval_distilgpt2_prompt_stress_v1",
        output_prefix="decoder_distilgpt2_prompt_stress",
        command_suffix="prompt_stress",
        materialized_model_scope=(
            "distilgpt2 prompt-stress confirmation using evaluator-local generated ONNX/tokenizer "
            "artifacts; generated model files are intentionally gitignored and shared with the "
            "distilgpt2 quality gate"
        ),
        trained_quality_scope=(
            "broader prompt/input-distribution stress check for the bf16/PWL frontier before "
            "moving to GPT-2 scale or larger-array conclusions"
        ),
        dataset_status="materialized_distilgpt2_prompt_stress_manifest_v1",
        dataset_notes=(
            "distilgpt2 prompt-stress dataset. Run materialize_hf_decoder_contract.py before generating "
            "reference/candidate manifests because the model/tokenizer artifacts are gitignored."
        ),
    )


def _decoder_pwl_logit_sensitivity_ladder_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_tiny_v1"
    dataset_manifest = f"{base}/manifest_pwl_failure_focus_v1.json"
    sample_file = f"{base}/samples_pwl_failure_focus_v1.jsonl"
    reference_dir = f"{base}/reference_pwl_failure_focus_v1"
    reference_manifest = f"{base}/reference_pwl_failure_focus_v1_manifest.json"
    candidate_dir = f"{base}/candidate_pwl_failure_focus_v1"
    candidate_manifest = f"{base}/candidate_pwl_failure_focus_v1_manifest.json"
    validation_out = f"{base}/decoder_contract_validation__{item_id}.json"
    quality_out = f"{base}/decoder_quality_compare__{item_id}.json"
    sweep_dir = f"{base}/candidate_sweeps/{item_id}"
    sweep_out = f"{base}/decoder_quality_sweep__{item_id}.json"
    ladder_out = f"{base}/decoder_pwl_logit_ladder__{item_id}.json"
    ladder_report = f"{base}/decoder_pwl_logit_ladder__{item_id}.md"
    rough_grid = "decoder_pwl_logit_sensitivity_ladder_v1"
    commands = [
        {
            "name": "generate_decoder_pwl_logit_focus_reference",
            "run": (
                "python3 npu/eval/gen_llm_decoder_reference_suite.py "
                f"--dataset-manifest {dataset_manifest} "
                f"--out-dir {reference_dir} "
                f"--out-manifest {reference_manifest}"
            ),
        },
        {
            "name": "generate_decoder_pwl_logit_focus_candidate",
            "run": (
                "python3 npu/eval/gen_llm_decoder_candidate_suite.py "
                f"--dataset-manifest {dataset_manifest} "
                f"--out-dir {candidate_dir} "
                f"--out-manifest {candidate_manifest}"
            ),
        },
        {
            "name": "validate_decoder_pwl_logit_focus_contract",
            "run": f"python3 npu/eval/validate_llm_decoder_contract.py --dataset-manifest {dataset_manifest} --out {validation_out}",
        },
        {
            "name": "compare_decoder_pwl_logit_focus_quality",
            "run": (
                "python3 npu/eval/compare_llm_decoder_quality.py "
                f"--reference-manifest {reference_manifest} "
                f"--candidate-manifest {candidate_manifest} "
                f"--out {quality_out}"
            ),
        },
        {
            "name": "sweep_decoder_pwl_logit_ladder",
            "run": (
                "python3 npu/eval/sweep_llm_decoder_candidate_quality.py "
                f"--dataset-manifest {dataset_manifest} "
                f"--rough-grid {rough_grid} "
                f"--out-dir {sweep_dir} "
                f"--out {sweep_out}"
            ),
        },
        {
            "name": "summarize_decoder_pwl_logit_ladder",
            "run": (
                "python3 npu/eval/summarize_llm_decoder_pwl_logit_ladder.py "
                f"--sweep {sweep_out} "
                f"--sample-file {sample_file} "
                f"--out {ladder_out} "
                f"--out-md {ladder_report}"
            ),
        },
    ]
    return {
        "inputs": {
            "dataset_manifest": dataset_manifest,
            "sample_file": sample_file,
            "reference_dir": reference_dir,
            "reference_manifest": reference_manifest,
            "candidate_dir": candidate_dir,
            "candidate_manifest": candidate_manifest,
            "validation_out": validation_out,
            "quality_out": quality_out,
            "candidate_sweep_dir": sweep_dir,
            "candidate_sweep_out": sweep_out,
            "candidate_sweep_grid": rough_grid,
            "ladder_out": ladder_out,
            "ladder_report": ladder_report,
            "focus_samples": [
                "dist2_arith_three_plus_five",
                "dist2_sequence_months",
            ],
            "control_samples": [
                "dist2_arith_two_plus_two",
                "dist2_arith_six_times_two",
                "dist2_sequence_numbers",
                "dist2_sequence_weekdays",
            ],
            "ladder_scope": (
                "focused six-sample PWL/logit sensitivity ladder for the broad-v2 shared "
                "exact-token misses; separates exact logit quantization, unquantized PWL, "
                "PWL input/weight precision, and normalization precision"
            ),
        },
        "commands": commands,
        "expected_outputs": [
            reference_manifest,
            candidate_manifest,
            validation_out,
            quality_out,
            sweep_out,
            ladder_out,
            ladder_report,
        ],
    }


def _decoder_pwl_survivor_distribution_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_tiny_v1"
    dataset_manifest = f"{base}/manifest_distribution_v2.json"
    sample_file = f"{base}/samples_distribution_v2.jsonl"
    reference_dir = f"{base}/reference_distribution_v2"
    reference_manifest = f"{base}/reference_distribution_v2_manifest.json"
    candidate_dir = f"{base}/candidate_distribution_v2"
    candidate_manifest = f"{base}/candidate_distribution_v2_manifest.json"
    validation_out = f"{base}/decoder_contract_validation__{item_id}.json"
    quality_out = f"{base}/decoder_quality_compare__{item_id}.json"
    sweep_dir = f"{base}/candidate_sweeps/{item_id}"
    sweep_out = f"{base}/decoder_quality_sweep__{item_id}.json"
    summary_out = f"{base}/decoder_pwl_survivor_distribution__{item_id}.json"
    summary_report = f"{base}/decoder_pwl_survivor_distribution__{item_id}.md"
    rough_grid = "decoder_pwl_survivor_distribution_v1"
    commands = [
        {
            "name": "generate_decoder_pwl_survivor_distribution_reference",
            "run": (
                "python3 npu/eval/gen_llm_decoder_reference_suite.py "
                f"--dataset-manifest {dataset_manifest} "
                f"--out-dir {reference_dir} "
                f"--out-manifest {reference_manifest}"
            ),
        },
        {
            "name": "generate_decoder_pwl_survivor_distribution_candidate",
            "run": (
                "python3 npu/eval/gen_llm_decoder_candidate_suite.py "
                f"--dataset-manifest {dataset_manifest} "
                f"--out-dir {candidate_dir} "
                f"--out-manifest {candidate_manifest}"
            ),
        },
        {
            "name": "validate_decoder_pwl_survivor_distribution_contract",
            "run": f"python3 npu/eval/validate_llm_decoder_contract.py --dataset-manifest {dataset_manifest} --out {validation_out}",
        },
        {
            "name": "compare_decoder_pwl_survivor_distribution_quality",
            "run": (
                "python3 npu/eval/compare_llm_decoder_quality.py "
                f"--reference-manifest {reference_manifest} "
                f"--candidate-manifest {candidate_manifest} "
                f"--out {quality_out}"
            ),
        },
        {
            "name": "sweep_decoder_pwl_survivor_distribution",
            "run": (
                "python3 npu/eval/sweep_llm_decoder_candidate_quality.py "
                f"--dataset-manifest {dataset_manifest} "
                f"--rough-grid {rough_grid} "
                f"--out-dir {sweep_dir} "
                f"--out {sweep_out}"
            ),
        },
        {
            "name": "summarize_decoder_pwl_survivor_distribution",
            "run": (
                "python3 npu/eval/summarize_llm_decoder_pwl_survivor_distribution.py "
                f"--sweep {sweep_out} "
                f"--sample-file {sample_file} "
                f"--out {summary_out} "
                f"--out-md {summary_report}"
            ),
        },
    ]
    return {
        "inputs": {
            "dataset_manifest": dataset_manifest,
            "sample_file": sample_file,
            "reference_dir": reference_dir,
            "reference_manifest": reference_manifest,
            "candidate_dir": candidate_dir,
            "candidate_manifest": candidate_manifest,
            "validation_out": validation_out,
            "quality_out": quality_out,
            "candidate_sweep_dir": sweep_dir,
            "candidate_sweep_out": sweep_out,
            "candidate_sweep_grid": rough_grid,
            "survivor_distribution_out": summary_out,
            "survivor_distribution_report": summary_report,
            "survivor_distribution_scope": (
                "expanded v2 broad prompt-regime check for q12/unquantized PWL survivors, "
                "with fp16/bf16, q10, and q8 rows kept as precision controls before RTL/PPA promotion"
            ),
        },
        "commands": commands,
        "expected_outputs": [
            reference_manifest,
            candidate_manifest,
            validation_out,
            quality_out,
            sweep_out,
            summary_out,
            summary_report,
        ],
    }


def _decoder_pwl_bitwidth_boundary_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_tiny_v1"
    dataset_manifest = f"{base}/manifest_distribution_v2.json"
    sample_file = f"{base}/samples_distribution_v2.jsonl"
    reference_dir = f"{base}/reference_distribution_v2"
    reference_manifest = f"{base}/reference_distribution_v2_manifest.json"
    candidate_dir = f"{base}/candidate_distribution_v2"
    candidate_manifest = f"{base}/candidate_distribution_v2_manifest.json"
    validation_out = f"{base}/decoder_contract_validation__{item_id}.json"
    quality_out = f"{base}/decoder_quality_compare__{item_id}.json"
    sweep_dir = f"{base}/candidate_sweeps/{item_id}"
    sweep_out = f"{base}/decoder_quality_sweep__{item_id}.json"
    boundary_out = f"{base}/decoder_pwl_bitwidth_boundary__{item_id}.json"
    boundary_report = f"{base}/decoder_pwl_bitwidth_boundary__{item_id}.md"
    rough_grid = "decoder_pwl_bitwidth_boundary_v1"
    commands = [
        {
            "name": "generate_decoder_pwl_bitwidth_boundary_reference",
            "run": (
                "python3 npu/eval/gen_llm_decoder_reference_suite.py "
                f"--dataset-manifest {dataset_manifest} "
                f"--out-dir {reference_dir} "
                f"--out-manifest {reference_manifest}"
            ),
        },
        {
            "name": "generate_decoder_pwl_bitwidth_boundary_candidate",
            "run": (
                "python3 npu/eval/gen_llm_decoder_candidate_suite.py "
                f"--dataset-manifest {dataset_manifest} "
                f"--out-dir {candidate_dir} "
                f"--out-manifest {candidate_manifest}"
            ),
        },
        {
            "name": "validate_decoder_pwl_bitwidth_boundary_contract",
            "run": f"python3 npu/eval/validate_llm_decoder_contract.py --dataset-manifest {dataset_manifest} --out {validation_out}",
        },
        {
            "name": "compare_decoder_pwl_bitwidth_boundary_quality",
            "run": (
                "python3 npu/eval/compare_llm_decoder_quality.py "
                f"--reference-manifest {reference_manifest} "
                f"--candidate-manifest {candidate_manifest} "
                f"--out {quality_out}"
            ),
        },
        {
            "name": "sweep_decoder_pwl_bitwidth_boundary",
            "run": (
                "python3 npu/eval/sweep_llm_decoder_candidate_quality.py "
                f"--dataset-manifest {dataset_manifest} "
                f"--rough-grid {rough_grid} "
                f"--out-dir {sweep_dir} "
                f"--out {sweep_out}"
            ),
        },
        {
            "name": "summarize_decoder_pwl_bitwidth_boundary",
            "run": (
                "python3 npu/eval/summarize_llm_decoder_pwl_bitwidth_boundary.py "
                f"--sweep {sweep_out} "
                f"--sample-file {sample_file} "
                f"--out {boundary_out} "
                f"--out-md {boundary_report}"
            ),
        },
    ]
    return {
        "inputs": {
            "dataset_manifest": dataset_manifest,
            "sample_file": sample_file,
            "reference_dir": reference_dir,
            "reference_manifest": reference_manifest,
            "candidate_dir": candidate_dir,
            "candidate_manifest": candidate_manifest,
            "validation_out": validation_out,
            "quality_out": quality_out,
            "candidate_sweep_dir": sweep_dir,
            "candidate_sweep_out": sweep_out,
            "candidate_sweep_grid": rough_grid,
            "bitwidth_boundary_out": boundary_out,
            "bitwidth_boundary_report": boundary_report,
            "bitwidth_boundary_scope": (
                "expanded v2 prompt-distribution check for the lowest exact-safe integer PWL "
                "softmax input/weight bit width after q12 proved broad-safe but expensive in PPA"
            ),
        },
        "commands": commands,
        "expected_outputs": [
            reference_manifest,
            candidate_manifest,
            validation_out,
            quality_out,
            sweep_out,
            boundary_out,
            boundary_report,
        ],
    }


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
    proposal_id: str | None,
    proposal_path: str | None,
    evaluation_mode: str | None,
    abstraction_layer: str | None,
    expected_direction: str | None,
    expected_reason: str | None,
    comparison_role: str | None,
    paired_baseline_item_id: str | None,
    depends_on_item_ids: list[str] | None,
    requires_merged_inputs: bool,
    requires_materialized_refs: bool,
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
    task_inputs: dict[str, Any] = {
        **inputs,
        "generated_campaign": {
            "base_campaign_path": campaign_path,
            "path": generated_campaign_path,
            "clean_outputs": True,
            "outputs": generated_outputs,
        },
    }
    abstraction_layer_name = str(abstraction_layer or "").strip()
    if abstraction_layer_name in {
        "decoder_probability_path",
        "decoder_probability_sweep",
        "decoder_probability_sensitivity",
        "decoder_probability_fp_sensitivity",
        "decoder_distribution_robustness",
        "decoder_survivor_prompt_stress",
        "decoder_survivor_cost_proxy",
        "decoder_pwl_frontier_detail",
        "decoder_q8_normalization_frontier",
        "decoder_q8_normalization_distribution",
        "decoder_q8_normalization_distribution_broad_v2",
        "decoder_bf16_pwl_recovery",
        "decoder_bf16_pwl_scale_probe",
        "decoder_bf16_pwl_recoverability",
        "decoder_pwl_failure_diagnosis",
        "decoder_pwl_logit_sensitivity_ladder",
        "decoder_pwl_survivor_distribution",
        "decoder_pwl_bitwidth_boundary",
        "decoder_trained_tiny_quality",
        "decoder_distilgpt2_quality",
        "decoder_distilgpt2_prompt_stress",
        "decoder_gpt2_quality",
        "decoder_gpt2_prompt_stress",
        "decoder_gpt2_tie_rank_frontier",
        "decoder_gpt2_logit_rank_bypass",
        "decoder_logit_rank_streaming_hierarchy",
        "decoder_logit_rank_streaming_overlap",
        "decoder_quantization_outline",
    }:
        if abstraction_layer_name == "decoder_quantization_outline":
            decoder_evidence = _decoder_quantization_outline_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_logit_rank_streaming_overlap":
            decoder_evidence = _decoder_logit_rank_streaming_overlap_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_logit_rank_streaming_hierarchy":
            decoder_evidence = _decoder_logit_rank_streaming_hierarchy_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_gpt2_logit_rank_bypass":
            decoder_evidence = _decoder_gpt2_logit_rank_bypass_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_gpt2_tie_rank_frontier":
            decoder_evidence = _decoder_gpt2_tie_rank_frontier_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_gpt2_prompt_stress":
            decoder_evidence = _decoder_gpt2_prompt_stress_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_gpt2_quality":
            decoder_evidence = _decoder_gpt2_quality_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_distilgpt2_prompt_stress":
            decoder_evidence = _decoder_distilgpt2_prompt_stress_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_distilgpt2_quality":
            decoder_evidence = _decoder_distilgpt2_quality_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_trained_tiny_quality":
            decoder_evidence = _decoder_trained_tiny_quality_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_bf16_pwl_scale_probe":
            decoder_evidence = _decoder_bf16_pwl_scale_probe_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_bf16_pwl_recovery":
            decoder_evidence = _decoder_bf16_pwl_recovery_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_bf16_pwl_recoverability":
            decoder_evidence = _decoder_bf16_pwl_recoverability_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_pwl_bitwidth_boundary":
            decoder_evidence = _decoder_pwl_bitwidth_boundary_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_pwl_survivor_distribution":
            decoder_evidence = _decoder_pwl_survivor_distribution_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_pwl_logit_sensitivity_ladder":
            decoder_evidence = _decoder_pwl_logit_sensitivity_ladder_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_pwl_failure_diagnosis":
            decoder_evidence = _decoder_pwl_failure_diagnosis_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_q8_normalization_distribution_broad_v2":
            decoder_evidence = _decoder_q8_normalization_distribution_evidence(item_id=item_id, distribution_version="v2")
        elif abstraction_layer_name == "decoder_q8_normalization_distribution":
            decoder_evidence = _decoder_q8_normalization_distribution_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_q8_normalization_frontier":
            decoder_evidence = _decoder_q8_normalization_frontier_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_pwl_frontier_detail":
            decoder_evidence = _decoder_pwl_frontier_detail_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_survivor_cost_proxy":
            decoder_evidence = _decoder_survivor_cost_proxy_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_survivor_prompt_stress":
            decoder_evidence = _decoder_survivor_prompt_stress_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_distribution_robustness":
            decoder_evidence = _decoder_distribution_robustness_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_probability_fp_sensitivity":
            decoder_evidence = _decoder_probability_fp_sensitivity_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_probability_sensitivity":
            decoder_evidence = _decoder_probability_sensitivity_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_probability_sweep":
            decoder_evidence = _decoder_probability_sweep_evidence(item_id=item_id)
        else:
            decoder_evidence = _decoder_probability_path_evidence(item_id=item_id)
        commands = [*decoder_evidence["commands"], *commands]
        expected_outputs = _uniq([*expected_outputs, *decoder_evidence["expected_outputs"]])
        task_inputs["decoder_contract"] = decoder_evidence["inputs"]

    payload = {
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
            "inputs": task_inputs,
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
            "pr_title": _default_pr_title(title=title),
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
    if proposal_id or proposal_path or evaluation_mode or abstraction_layer or expected_direction or expected_reason or comparison_role or paired_baseline_item_id or depends_on_item_ids or requires_merged_inputs or requires_materialized_refs:
        payload["developer_loop"] = {
            "proposal_id": proposal_id or "",
            "proposal_path": proposal_path or "",
        }
        if evaluation_mode or expected_direction or expected_reason:
            payload["developer_loop"]["evaluation"] = {
                "mode": evaluation_mode or "",
                "expected_direction": expected_direction or "",
                "expected_reason": expected_reason or "",
            }
        if abstraction_layer:
            payload["developer_loop"]["abstraction"] = {
                "layer": abstraction_layer,
            }
        effective_comparison_role = comparison_role or {
            "baseline_refresh": "refreshed_baseline",
            "paired_comparison": "candidate",
            "broad_ranking": "ranking",
        }.get(str(evaluation_mode or "").strip(), "")
        if effective_comparison_role or paired_baseline_item_id:
            payload["developer_loop"]["comparison"] = {
                "role": effective_comparison_role,
                "paired_baseline_item_id": paired_baseline_item_id or "",
            }
        dependency_ids = [str(item).strip() for item in (depends_on_item_ids or []) if str(item).strip()]
        if dependency_ids or requires_merged_inputs or requires_materialized_refs:
            payload["developer_loop"]["dependencies"] = {
                "item_ids": dependency_ids,
                "requires_merged_inputs": requires_merged_inputs,
                "requires_materialized_refs": requires_materialized_refs,
            }
    return payload


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
    proposal_path = _repo_rel(request.proposal_path, repo_root) if request.proposal_path else None
    proposal_path = canonicalize_proposal_path(repo_root, proposal_path=proposal_path, proposal_id=request.proposal_id)
    requested_entry = _load_requested_item_entry(repo_root, proposal_path, item_id)
    effective_evaluation_mode = _resolve_requested_entry_text(
        requested_entry,
        key="evaluation_mode",
        explicit=request.evaluation_mode,
    )
    effective_abstraction_layer = _resolve_requested_entry_text(
        requested_entry,
        key="abstraction_layer",
        explicit=request.abstraction_layer,
    )
    effective_comparison_role = _resolve_requested_entry_text(
        requested_entry,
        key="comparison_role",
        explicit=request.comparison_role,
    )
    effective_paired_baseline_item_id = _resolve_requested_entry_text(
        requested_entry,
        key="paired_baseline_item_id",
        explicit=request.paired_baseline_item_id,
    )
    effective_depends_on_item_ids = _resolve_requested_entry_list(
        requested_entry,
        key="depends_on_item_ids",
        explicit=request.depends_on_item_ids,
    )
    effective_requires_merged_inputs = _resolve_requested_entry_bool(
        requested_entry,
        key="requires_merged_inputs",
        explicit=request.requires_merged_inputs,
    )
    effective_requires_materialized_refs = _resolve_requested_entry_bool(
        requested_entry,
        key="requires_materialized_refs",
        explicit=request.requires_materialized_refs,
    )
    source_commit = _resolve_source_commit(repo_root, request.source_commit)
    _upsert_requested_item_entry(
        repo_root=repo_root,
        proposal_id=request.proposal_id,
        proposal_path=proposal_path,
        item_id=item_id,
        task_type='l2_campaign',
        objective=objective,
        evaluation_mode=effective_evaluation_mode,
        abstraction_layer=effective_abstraction_layer,
        comparison_role=effective_comparison_role,
        paired_baseline_item_id=effective_paired_baseline_item_id,
        depends_on_item_ids=effective_depends_on_item_ids,
        requires_merged_inputs=effective_requires_merged_inputs,
        requires_materialized_refs=effective_requires_materialized_refs,
        expected_direction=request.expected_direction,
        expected_reason=request.expected_reason,
        source_commit=source_commit,
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
        proposal_id=request.proposal_id,
        proposal_path=proposal_path,
        evaluation_mode=effective_evaluation_mode,
        abstraction_layer=effective_abstraction_layer,
        expected_direction=request.expected_direction,
        expected_reason=request.expected_reason,
        comparison_role=effective_comparison_role,
        paired_baseline_item_id=effective_paired_baseline_item_id,
        depends_on_item_ids=effective_depends_on_item_ids,
        requires_merged_inputs=effective_requires_merged_inputs,
        requires_materialized_refs=effective_requires_materialized_refs,
    )
    initial_state = WorkItemState.DISPATCH_PENDING
    transient_work_item = WorkItem(
        work_item_key=f"l2_campaign:{item_id}",
        task_request_id="",
        item_id=item_id,
        layer=LayerName.LAYER2,
        flow=FlowName.OPENROAD,
        platform=platform,
        task_type="l2_campaign",
        state=WorkItemState.DRAFT,
        priority=request.priority,
        source_mode="src_verilog",
    )
    transient_task_request = TaskRequest(
        request_key=f"l2_campaign:{item_id}",
        source="l2_task_generator",
        requested_by=request.requested_by,
        title=title,
        description=objective,
        layer=LayerName.LAYER2,
        flow=FlowName.OPENROAD,
        priority=request.priority,
        request_payload=payload,
        source_commit=source_commit,
    )
    transient_work_item.task_request = transient_task_request
    gate = evaluate_work_item_dependencies(session, repo_root=repo_root, work_item=transient_work_item)
    if not gate.satisfied:
        initial_state = WorkItemState.BLOCKED

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
            source_commit=source_commit,
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
            state=initial_state,
            priority=request.priority,
            source_mode="src_verilog",
            input_manifest=payload["task"]["inputs"],
            command_manifest=payload["task"]["commands"],
            expected_outputs=payload["task"]["expected_outputs"],
            acceptance_rules=payload["task"]["acceptance"],
            source_commit=source_commit,
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
    existing.task_request.source_commit = source_commit

    existing.priority = request.priority
    existing.platform = platform
    existing.source_mode = "src_verilog"
    existing.input_manifest = payload["task"]["inputs"]
    existing.command_manifest = payload["task"]["commands"]
    existing.expected_outputs = payload["task"]["expected_outputs"]
    existing.acceptance_rules = payload["task"]["acceptance"]
    existing.source_commit = source_commit
    existing.state = initial_state
    existing.queue_snapshot_path = None
    session.commit()
    return Layer2TaskGenerateResult(
        item_id=item_id,
        status=status,
        work_item_id=existing.id,
        task_request_id=existing.task_request_id,
    )
