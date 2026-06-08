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
from control_plane.services.source_requirement import build_source_requirement


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


def _npu_compute_full_path_equivalence_guard_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/campaigns/npu/frontier_guards"
    guard_out = f"{base}/npu_compute_module_guard__{item_id}.json"
    equivalence_log = f"{base}/npu_contract_equivalence__{item_id}.log"
    configs = [
        "runs/designs/npu_blocks/npu_fp16_cpp_nm1_cmp/config_nm1.json",
        "runs/designs/npu_blocks/npu_fp16_cpp_nm2_cmp/config_nm2.json",
        "runs/designs/npu_blocks/npu_fp16_cpp_nm4_cmp/config_nm4.json",
    ]
    config_args = " ".join(shlex.quote(path) for path in configs)
    return {
        "inputs": {
            "npu_compute_guard_out": guard_out,
            "npu_contract_equivalence_log": equivalence_log,
            "rtlgen_configs": configs,
            "guard_scope": (
                "Pre-PPA guard for the corrected NPU compute frontier: prove RTL/perf "
                "architectural writeback equivalence and confirm generated nm1/nm2/nm4 RTL "
                "retains the requested FP16 GEMM module structure."
            ),
        },
        "commands": [
            {
                "name": "build_generator",
                "run": "export PATH=/oss-cad-suite/bin:$PATH && cmake -S . -B build && cmake --build build --target rtlgen",
            },
            {
                "name": "check_npu_compute_module_guard",
                "run": (
                    "python3 npu/eval/check_npu_compute_module_guard.py "
                    f"--configs {config_args} "
                    f"--out {guard_out}"
                ),
            },
            {
                "name": "run_npu_contract_equivalence",
                "run": f"mkdir -p {base} && python3 tests/test_npu_contract_equivalence.py > {equivalence_log} 2>&1",
            },
        ],
        "expected_outputs": [guard_out, equivalence_log],
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
    boundary_ppa = (
        "control_plane/shadow_exports/l1_promotions/"
        "l1_decoder_logit_rank_r128_k1_pin_perimeter_bound_v1.json"
    )
    return {
        "inputs": {
            "source_prompt_stress": prompt_stress,
            "source_logit_rank_bypass": logit_rank_bypass,
            "rank_datapath_ppa": rank_ppa,
            "rank_scale_ppa": scale_ppa,
            "candidate_merge_ppa": candidate_merge_ppa,
            "boundary_ppa": boundary_ppa,
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
                    f"--boundary-ppa {boundary_ppa} "
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
    boundary_ppa = (
        "control_plane/shadow_exports/l1_promotions/"
        "l1_decoder_logit_rank_r128_k1_pin_perimeter_bound_v1.json"
    )
    sram_metrics_json = "runs/designs/sram/minimal_v0_2_draft/sram_metrics.json"
    memory_model = {
        "memory_bandwidth_bytes_per_cycle": 64,
        "sram_metrics_json": sram_metrics_json,
        "vocab_size_list": [50257, 100000, 200000],
        "producer_lanes_list": [8, 16, 32, 64, 128],
        "sram_read_energy_pj_per_byte": 0.05,
        "sram_write_energy_pj_per_byte": 0.07,
        "noc_hops": 2,
        "noc_energy_pj_per_byte_hop": 0.02,
        "source": "sram_metrics_json_plus_planning_noc",
        "sram_source": "cacti_estimated_nangate45_minimal_v0_2_draft",
        "noc_source": "planning_default_not_literature_backed",
    }
    return {
        "inputs": {
            "source_prompt_stress": prompt_stress,
            "source_logit_rank_bypass": logit_rank_bypass,
            "rank_datapath_ppa": rank_ppa,
            "rank_scale_ppa": scale_ppa,
            "candidate_merge_ppa": candidate_merge_ppa,
            "boundary_ppa": boundary_ppa,
            "memory_model": memory_model,
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
                    f"--boundary-ppa {boundary_ppa} "
                    f"--sram-metrics-json {sram_metrics_json} "
                    "--vocab-size-list 50257,100000,200000 "
                    "--producer-lanes-list 8,16,32,64,128 "
                    "--top-k-list 1,4 "
                    "--producer-ii-cycles-list 1,2 "
                    "--global-merge-ii-cycles 1,2 "
                    "--candidate-fifo-depth-groups-list 16,256,4096 "
                    "--memory-bandwidth-bytes-per-cycle 64 "
                    "--sram-read-energy-pj-per-byte 0.05 "
                    "--sram-write-energy-pj-per-byte 0.07 "
                    "--noc-hops 2 "
                    "--noc-energy-pj-per-byte-hop 0.02 "
                    f"--out {overlap_out} "
                    f"--out-md {overlap_report}"
                ),
            },
        ],
        "expected_outputs": [overlap_out, overlap_report],
    }


def _decoder_logit_rank_streaming_producer_integrated_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    prompt_stress = f"{base}/decoder_gpt2_prompt_stress__l2_decoder_gpt2_prompt_stress_v1.json"
    logit_rank_bypass = f"{base}/decoder_gpt2_logit_rank_bypass__l2_decoder_gpt2_logit_rank_bypass_v1.json"
    interface_out = f"{base}/decoder_logit_rank_streaming_producer_integrated__{item_id}.json"
    interface_report = f"{base}/decoder_logit_rank_streaming_producer_integrated__{item_id}.md"
    rank_ppa = "control_plane/shadow_exports/l1_promotions/l1_decoder_logit_rank_datapath_v1_r2.json"
    scale_ppa = "control_plane/shadow_exports/l1_promotions/l1_decoder_logit_rank_scale_v1.json"
    candidate_merge_ppa = (
        "control_plane/shadow_exports/l1_promotions/l1_decoder_candidate_stream_merge_fifo_v1.json"
    )
    boundary_ppa = (
        "control_plane/shadow_exports/l1_promotions/"
        "l1_decoder_logit_rank_r128_k1_pin_perimeter_bound_v1.json"
    )
    sram_metrics_json = "runs/designs/sram/minimal_v0_2_draft/sram_metrics.json"
    memory_model = {
        "memory_bandwidth_bytes_per_cycle": 64,
        "sram_metrics_json": sram_metrics_json,
        "vocab_size_list": [50257, 100000, 200000],
        "producer_lanes_list": [8, 16, 32, 64, 128],
        "producer_interface_focus_lanes": [64, 128],
        "sram_read_energy_pj_per_byte": 0.05,
        "sram_write_energy_pj_per_byte": 0.07,
        "noc_hops": 2,
        "noc_energy_pj_per_byte_hop": 0.02,
        "source": "sram_metrics_json_plus_planning_noc",
        "sram_source": "cacti_estimated_nangate45_minimal_v0_2_draft",
        "noc_source": "planning_default_not_literature_backed",
    }
    return {
        "inputs": {
            "source_prompt_stress": prompt_stress,
            "source_logit_rank_bypass": logit_rank_bypass,
            "rank_datapath_ppa": rank_ppa,
            "rank_scale_ppa": scale_ppa,
            "candidate_merge_ppa": candidate_merge_ppa,
            "boundary_ppa": boundary_ppa,
            "memory_model": memory_model,
            "producer_integrated_out": interface_out,
            "producer_integrated_report": interface_report,
            "producer_integrated_scope": (
                "Focus r64/r128 decoder logit-rank candidates as producer-integrated ready-valid "
                "interfaces. Keep exposed-pin macro-boundary PPA diagnostic-only, exclude padded "
                "die area from main cost, and preserve perf-sim/RTL equivalence observables."
            ),
        },
        "commands": [
            {
                "name": "estimate_decoder_logit_rank_streaming_producer_integrated",
                "run": (
                    "python3 npu/eval/estimate_llm_decoder_logit_rank_streaming_hierarchy.py "
                    f"--prompt-stress {prompt_stress} "
                    f"--logit-rank-bypass {logit_rank_bypass} "
                    f"--rank-ppa {rank_ppa} "
                    f"--scale-ppa {scale_ppa} "
                    f"--candidate-merge-ppa {candidate_merge_ppa} "
                    f"--boundary-ppa {boundary_ppa} "
                    f"--sram-metrics-json {sram_metrics_json} "
                    "--vocab-size-list 50257,100000,200000 "
                    "--producer-lanes-list 8,16,32,64,128 "
                    "--producer-interface-focus-lanes 64,128 "
                    "--top-k-list 1,4 "
                    "--producer-ii-cycles-list 1,2 "
                    "--global-merge-ii-cycles 1,2 "
                    "--candidate-fifo-depth-groups-list 16,256,4096 "
                    "--memory-bandwidth-bytes-per-cycle 64 "
                    "--sram-read-energy-pj-per-byte 0.05 "
                    "--sram-write-energy-pj-per-byte 0.07 "
                    "--noc-hops 2 "
                    "--noc-energy-pj-per-byte-hop 0.02 "
                    f"--out {interface_out} "
                    f"--out-md {interface_report}"
                ),
            },
        ],
        "expected_outputs": [interface_out, interface_report],
    }


def _decoder_output_projection_service_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    out = f"{base}/decoder_output_projection_service__{item_id}.json"
    report = f"{base}/decoder_output_projection_service__{item_id}.md"
    return {
        "inputs": {
            "producer_service_out": out,
            "producer_service_report": report,
            "producer_service_scope": (
                "Stage-serialized output-projection producer service model for shared GEMM: "
                "derive producer latency and integer II from tile MAC count, weight traffic, "
                "hidden-vector load, and memory bandwidth."
            ),
            "producer_service_grid": {
                "vocab_size_list": [50257, 100000, 200000],
                "hidden_size_list": [768, 1024, 2048],
                "producer_lanes_list": [64, 128, 256],
                "macs_per_cycle_list": [8192, 32768],
                "memory_bandwidth_bytes_per_cycle_list": [64, 256],
            },
        },
        "commands": [
            {
                "name": "estimate_decoder_output_projection_service",
                "run": (
                    "python3 npu/eval/estimate_llm_decoder_producer_ranker_coupling.py "
                    "--mode producer_service "
                    "--vocab-size-list 50257,100000,200000 "
                    "--hidden-size-list 768,1024,2048 "
                    "--producer-lanes-list 64,128,256 "
                    "--macs-per-cycle-list 8192,32768 "
                    "--memory-bandwidth-bytes-per-cycle-list 64,256 "
                    f"--out {out} "
                    f"--out-md {report}"
                ),
            },
        ],
        "expected_outputs": [out, report],
    }


def _decoder_producer_ranker_coupled_noc_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    out = f"{base}/decoder_producer_ranker_coupled_noc__{item_id}.json"
    report = f"{base}/decoder_producer_ranker_coupled_noc__{item_id}.md"
    rank_ppa = "control_plane/shadow_exports/l1_promotions/l1_decoder_logit_rank_datapath_v1_r2.json"
    scale_ppa = "control_plane/shadow_exports/l1_promotions/l1_decoder_logit_rank_scale_v1.json"
    candidate_merge_ppa = (
        "control_plane/shadow_exports/l1_promotions/l1_decoder_candidate_stream_merge_fifo_v1.json"
    )
    boundary_ppa = (
        "control_plane/shadow_exports/l1_promotions/"
        "l1_decoder_logit_rank_r128_k1_pin_perimeter_bound_v1.json"
    )
    producer_control_boundary = (
        "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
        "decoder_output_projection_producer_softmax_event_ablation__"
        "l2_decoder_output_projection_producer_event_scoreboard_v1.json"
    )
    producer_physical_boundary = (
        "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
        "decoder_output_projection_producer_pnr_feasibility__"
        "l2_decoder_output_projection_producer_pnr_nm16_v1.json"
    )
    sram_metrics_json = "runs/designs/sram/minimal_v0_2_draft/sram_metrics.json"
    return {
        "inputs": {
            "producer_ranker_coupled_out": out,
            "producer_ranker_coupled_report": report,
            "rank_datapath_ppa": rank_ppa,
            "rank_scale_ppa": scale_ppa,
            "candidate_merge_ppa": candidate_merge_ppa,
            "boundary_ppa": boundary_ppa,
            "producer_control_boundary": producer_control_boundary,
            "producer_physical_boundary": producer_physical_boundary,
            "sram_metrics_json": sram_metrics_json,
            "producer_ranker_coupled_scope": (
                "Couple stage-serialized output-projection producer service curves to the "
                "producer-integrated ready-valid ranker frontier, including shared NoC/memory "
                "bandwidth shares for contention sensitivity and bounded SOFTMAX/EVENT "
                "producer-control synthesis evidence plus nm16 producer-wrapper physical "
                "feasibility/PPA evidence."
            ),
            "memory_share_list": [1.0, 0.5, 0.25],
        },
        "commands": [
            {
                "name": "estimate_decoder_producer_ranker_coupled_noc",
                "run": (
                    "python3 npu/eval/estimate_llm_decoder_producer_ranker_coupling.py "
                    "--mode coupled_noc "
                    f"--rank-ppa {rank_ppa} "
                    f"--scale-ppa {scale_ppa} "
                    f"--candidate-merge-ppa {candidate_merge_ppa} "
                    f"--boundary-ppa {boundary_ppa} "
                    f"--producer-control-boundary {producer_control_boundary} "
                    f"--producer-physical-boundary {producer_physical_boundary} "
                    f"--sram-metrics-json {sram_metrics_json} "
                    "--vocab-size-list 50257,100000,200000 "
                    "--hidden-size-list 768,1024,2048 "
                    "--producer-lanes-list 64,128,256 "
                    "--macs-per-cycle-list 8192,32768 "
                    "--memory-bandwidth-bytes-per-cycle-list 64,256 "
                    "--memory-share-list 1.0,0.5,0.25 "
                    "--top-k-list 1,4 "
                    f"--out {out} "
                    f"--out-md {report}"
                ),
            },
        ],
        "expected_outputs": [out, report],
    }


def _decoder_producer_ranker_service_compatibility_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    out = f"{base}/decoder_producer_ranker_service_compatibility__{item_id}.json"
    report = f"{base}/decoder_producer_ranker_service_compatibility__{item_id}.md"
    producer_service = (
        f"{base}/decoder_output_projection_service__"
        "l2_decoder_output_projection_service_v1.json"
    )
    serial_ranker = (
        f"{base}/decoder_serial_ranker_architecture__"
        "l2_decoder_serial_ranker_architecture_v1.json"
    )
    rank_tree = (
        f"{base}/decoder_rank_tree_architecture__"
        "l2_decoder_rank_tree_architecture_v1.json"
    )
    return {
        "inputs": {
            "producer_ranker_service_compatibility_out": out,
            "producer_ranker_service_compatibility_report": report,
            "producer_service": producer_service,
            "serial_ranker_architecture": serial_ranker,
            "rank_tree_architecture": rank_tree,
            "producer_ranker_service_compatibility_scope": (
                "Compare measured r64/k1 serial and fully parallel ranker service cycles against "
                "the output-projection producer tile cadence. Includes single-r64 and banked-r64 "
                "integration assumptions for wider producer tiles before choosing producer-coupled RTL."
            ),
        },
        "commands": [
            {
                "name": "estimate_decoder_producer_ranker_service_compatibility",
                "run": (
                    "python3 npu/eval/estimate_llm_decoder_producer_ranker_service_compatibility.py "
                    f"--producer-service {producer_service} "
                    f"--serial-ranker {serial_ranker} "
                    f"--rank-tree {rank_tree} "
                    f"--out {out} "
                    f"--out-md {report}"
                ),
            },
        ],
        "expected_outputs": [out, report],
    }


def _decoder_serial_ranker_producer_replay_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    out = f"{base}/decoder_serial_ranker_producer_replay__{item_id}.json"
    report = f"{base}/decoder_serial_ranker_producer_replay__{item_id}.md"
    serial_ranker = (
        f"{base}/decoder_serial_ranker_architecture__"
        "l2_decoder_serial_ranker_architecture_v1.json"
    )
    service_compatibility = (
        f"{base}/decoder_producer_ranker_service_compatibility__"
        "l2_decoder_producer_ranker_service_compatibility_v1.json"
    )
    merge_config = (
        "runs/designs/activations/candidate_stream_merge_fifo_k1_l16_t16_d16_wrapper/"
        "config_candidate_stream_merge_fifo_k1_l16_t16_d16.json"
    )
    return {
        "inputs": {
            "serial_ranker_producer_replay_out": out,
            "serial_ranker_producer_replay_report": report,
            "serial_ranker_architecture": serial_ranker,
            "producer_ranker_service_compatibility": service_compatibility,
            "candidate_merge_config": merge_config,
            "serial_ranker_producer_replay_scope": (
                "Replay fixed producer tile issue intervals through the measured serial-ranker "
                "RTL wrappers for lpc1, lpc2, and lpc4. The harness checks full-token top-1 "
                "equivalence and records ready-valid backpressure at aggressive and producer-model cadences."
            ),
        },
        "commands": [
            {
                "name": "build_generator",
                "run": "export PATH=/oss-cad-suite/bin:$PATH && cmake -S . -B build && cmake --build build --target rtlgen",
            },
            {
                "name": "probe_decoder_serial_ranker_producer_replay",
                "run": (
                    "python3 npu/eval/probe_llm_decoder_serial_ranker_producer_replay.py "
                    f"--serial-ranker {serial_ranker} "
                    f"--service-compatibility {service_compatibility} "
                    f"--merge-config {merge_config} "
                    "--lanes-per-cycle 1,2,4 "
                    "--producer-ii-cycles 16,33,65,384 "
                    "--num-tiles 6 "
                    f"--out {out} "
                    f"--out-md {report}"
                ),
            },
        ],
        "expected_outputs": [out, report],
    }


def _decoder_serial_lpc1_producer_coupled_wrapper_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    out = f"{base}/decoder_serial_lpc1_producer_coupled_wrapper__{item_id}.json"
    report = f"{base}/decoder_serial_lpc1_producer_coupled_wrapper__{item_id}.md"
    serial_ranker = (
        f"{base}/decoder_serial_ranker_architecture__"
        "l2_decoder_serial_ranker_architecture_v1.json"
    )
    service_compatibility = (
        f"{base}/decoder_producer_ranker_service_compatibility__"
        "l2_decoder_producer_ranker_service_compatibility_v1.json"
    )
    producer_replay = (
        f"{base}/decoder_serial_ranker_producer_replay__"
        "l2_decoder_serial_ranker_producer_replay_v1.json"
    )
    merge_config = (
        "runs/designs/activations/candidate_stream_merge_fifo_k1_l16_t16_d16_wrapper/"
        "config_candidate_stream_merge_fifo_k1_l16_t16_d16.json"
    )
    return {
        "inputs": {
            "serial_lpc1_producer_coupled_wrapper_out": out,
            "serial_lpc1_producer_coupled_wrapper_report": report,
            "serial_ranker_architecture": serial_ranker,
            "producer_ranker_service_compatibility": service_compatibility,
            "serial_ranker_producer_replay": producer_replay,
            "candidate_merge_config": merge_config,
            "serial_lpc1_producer_coupled_wrapper_scope": (
                "Promote the measured serial_lpc1 r64/k1 ranker wrapper as the selected "
                "output-projection producer-coupled ranker. The job runs a focused RTL replay "
                "at the selected producer II=384, checks zero backpressure, and carries forward "
                "measured serial_lpc1 PPA from the architecture sweep."
            ),
        },
        "commands": [
            {
                "name": "build_generator",
                "run": "export PATH=/oss-cad-suite/bin:$PATH && cmake -S . -B build && cmake --build build --target rtlgen",
            },
            {
                "name": "promote_decoder_serial_lpc1_producer_wrapper",
                "run": (
                    "python3 npu/eval/promote_llm_decoder_serial_lpc1_producer_wrapper.py "
                    f"--serial-ranker {serial_ranker} "
                    f"--service-compatibility {service_compatibility} "
                    f"--producer-replay {producer_replay} "
                    f"--merge-config {merge_config} "
                    "--lanes-per-cycle 1 "
                    "--producer-ii-cycles 384 "
                    "--num-tiles 6 "
                    f"--out {out} "
                    f"--out-md {report}"
                ),
            },
        ],
        "expected_outputs": [out, report],
    }


def _decoder_output_projection_cadence_sensitivity_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    out = f"{base}/decoder_output_projection_cadence_sensitivity__{item_id}.json"
    report = f"{base}/decoder_output_projection_cadence_sensitivity__{item_id}.md"
    serial_ranker = (
        f"{base}/decoder_serial_ranker_architecture__"
        "l2_decoder_serial_ranker_architecture_v1.json"
    )
    producer_replay = (
        f"{base}/decoder_serial_ranker_producer_replay__"
        "l2_decoder_serial_ranker_producer_replay_v1.json"
    )
    promoted_wrapper = (
        f"{base}/decoder_serial_lpc1_producer_coupled_wrapper__"
        "l2_decoder_serial_lpc1_producer_coupled_wrapper_v1.json"
    )
    return {
        "inputs": {
            "output_projection_cadence_sensitivity_out": out,
            "output_projection_cadence_sensitivity_report": report,
            "serial_ranker_architecture": serial_ranker,
            "serial_ranker_producer_replay": producer_replay,
            "serial_lpc1_producer_coupled_wrapper": promoted_wrapper,
            "output_projection_cadence_sensitivity_scope": (
                "Stress the serial_lpc1 promotion against faster output-projection producer cadences "
                "caused by resident or cache-backed output weights. The model compares producer II "
                "against replay-observed zero-backpressure thresholds for serial_lpc1/lpc2/lpc4."
            ),
        },
        "commands": [
            {
                "name": "estimate_decoder_output_projection_cadence_sensitivity",
                "run": (
                    "python3 npu/eval/estimate_llm_decoder_output_projection_cadence_sensitivity.py "
                    f"--serial-ranker {serial_ranker} "
                    f"--producer-replay {producer_replay} "
                    f"--promoted-wrapper {promoted_wrapper} "
                    "--vocab-size-list 50257,100000 "
                    "--hidden-size-list 768,2048 "
                    "--producer-lanes-list 64,128 "
                    "--macs-per-cycle-list 8192,32768 "
                    "--memory-bandwidth-bytes-per-cycle-list 64,256 "
                    "--weight-cache-hit-rate-list 0.0,0.5,0.9,1.0 "
                    f"--out {out} "
                    f"--out-md {report}"
                ),
            },
        ],
        "expected_outputs": [out, report],
    }


def _decoder_resident_weight_ranker_fallback_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    out = f"{base}/decoder_resident_weight_ranker_fallback__{item_id}.json"
    report = f"{base}/decoder_resident_weight_ranker_fallback__{item_id}.md"
    cadence_sensitivity = (
        f"{base}/decoder_output_projection_cadence_sensitivity__"
        "l2_decoder_output_projection_cadence_sensitivity_v1.json"
    )
    rank_tree = (
        f"{base}/decoder_rank_tree_architecture__"
        "l2_decoder_rank_tree_architecture_v1.json"
    )
    return {
        "inputs": {
            "resident_weight_ranker_fallback_out": out,
            "resident_weight_ranker_fallback_report": report,
            "output_projection_cadence_sensitivity": cadence_sensitivity,
            "rank_tree_architecture": rank_tree,
            "resident_weight_ranker_fallback_small_buffer_tiles": 32,
            "resident_weight_ranker_fallback_scope": (
                "Compare small waiting buffers in front of measured serial_lpc1/lpc2/lpc4 "
                "rankers against measured r64 rank-tree fallback variants for resident-weight "
                "producer cadences that outpace replay-proven serial ranker service."
            ),
        },
        "commands": [
            {
                "name": "estimate_decoder_resident_weight_ranker_fallback",
                "run": (
                    "python3 npu/eval/estimate_llm_decoder_resident_weight_ranker_fallback.py "
                    f"--cadence-sensitivity {cadence_sensitivity} "
                    f"--rank-tree {rank_tree} "
                    "--small-buffer-tiles 32 "
                    f"--out {out} "
                    f"--out-md {report}"
                ),
            },
        ],
        "expected_outputs": [out, report],
    }


def _decoder_resident_ranktree_fallback_promotion_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    out = f"{base}/decoder_resident_ranktree_fallback_promotion__{item_id}.json"
    report = f"{base}/decoder_resident_ranktree_fallback_promotion__{item_id}.md"
    fallback = (
        f"{base}/decoder_resident_weight_ranker_fallback__"
        "l2_decoder_resident_weight_ranker_fallback_v1.json"
    )
    rank_tree = (
        f"{base}/decoder_rank_tree_architecture__"
        "l2_decoder_rank_tree_architecture_v1.json"
    )
    return {
        "inputs": {
            "resident_ranktree_fallback_promotion_out": out,
            "resident_ranktree_fallback_promotion_report": report,
            "resident_weight_ranker_fallback": fallback,
            "rank_tree_architecture": rank_tree,
            "resident_ranktree_fallback_promotion_scope": (
                "Promote the resident-weight output-projection fallback policy to the measured "
                "radix-4 r64 rank-tree: one instance for r64 producer tiles and banked r64 "
                "instances for wider resident-weight producer tiles."
            ),
        },
        "commands": [
            {
                "name": "promote_decoder_resident_ranktree_fallback",
                "run": (
                    "python3 npu/eval/promote_llm_decoder_resident_ranktree_fallback.py "
                    f"--fallback {fallback} "
                    f"--rank-tree {rank_tree} "
                    f"--out {out} "
                    f"--out-md {report}"
                ),
            },
        ],
        "expected_outputs": [out, report],
    }


def _decoder_output_projection_ranker_policy_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    out = f"{base}/decoder_output_projection_ranker_policy__{item_id}.json"
    report = f"{base}/decoder_output_projection_ranker_policy__{item_id}.md"
    serial_wrapper = (
        f"{base}/decoder_serial_lpc1_producer_coupled_wrapper__"
        "l2_decoder_serial_lpc1_producer_coupled_wrapper_v1.json"
    )
    cadence_sensitivity = (
        f"{base}/decoder_output_projection_cadence_sensitivity__"
        "l2_decoder_output_projection_cadence_sensitivity_v1.json"
    )
    ranktree_promotion = (
        f"{base}/decoder_resident_ranktree_fallback_promotion__"
        "l2_decoder_resident_ranktree_fallback_promotion_v1.json"
    )
    return {
        "inputs": {
            "output_projection_ranker_policy_out": out,
            "output_projection_ranker_policy_report": report,
            "serial_lpc1_producer_coupled_wrapper": serial_wrapper,
            "output_projection_cadence_sensitivity": cadence_sensitivity,
            "resident_ranktree_fallback_promotion": ranktree_promotion,
            "output_projection_ranker_policy_scope": (
                "Promote the output-projection ranker selection policy: serial_lpc1 for "
                "producer cadences at or above the replay-proven lpc1 threshold, and radix-4 "
                "rank-tree fallback for faster resident/cache-backed producer cadences."
            ),
        },
        "commands": [
            {
                "name": "promote_decoder_output_projection_ranker_policy",
                "run": (
                    "python3 npu/eval/promote_llm_decoder_output_projection_ranker_policy.py "
                    f"--serial-wrapper {serial_wrapper} "
                    f"--cadence-sensitivity {cadence_sensitivity} "
                    f"--ranktree-promotion {ranktree_promotion} "
                    f"--out {out} "
                    f"--out-md {report}"
                ),
            },
        ],
        "expected_outputs": [out, report],
    }


def _decoder_output_projection_ranker_wrapper_contract_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    out = f"{base}/decoder_output_projection_ranker_wrapper_contract__{item_id}.json"
    report = f"{base}/decoder_output_projection_ranker_wrapper_contract__{item_id}.md"
    policy = (
        f"{base}/decoder_output_projection_ranker_policy__"
        "l2_decoder_output_projection_ranker_policy_v1.json"
    )
    serial_wrapper = (
        f"{base}/decoder_serial_lpc1_producer_coupled_wrapper__"
        "l2_decoder_serial_lpc1_producer_coupled_wrapper_v1.json"
    )
    ranktree_promotion = (
        f"{base}/decoder_resident_ranktree_fallback_promotion__"
        "l2_decoder_resident_ranktree_fallback_promotion_v1.json"
    )
    merge_config = (
        "runs/designs/activations/candidate_stream_merge_fifo_k1_l16_t16_d16_wrapper/"
        "config_candidate_stream_merge_fifo_k1_l16_t16_d16.json"
    )
    return {
        "inputs": {
            "output_projection_ranker_wrapper_contract_out": out,
            "output_projection_ranker_wrapper_contract_report": report,
            "output_projection_ranker_policy": policy,
            "serial_lpc1_producer_coupled_wrapper": serial_wrapper,
            "resident_ranktree_fallback_promotion": ranktree_promotion,
            "candidate_merge_config": merge_config,
            "output_projection_ranker_wrapper_contract_scope": (
                "Check representative wrapper-policy cases before implementing final RTL mux/control: "
                "fresh serial_lpc1 RTL replay, r64 rank-tree primitive RTL equivalence, and r128 "
                "banked-r64 composition against the full-tile perf reference."
            ),
        },
        "commands": [
            {
                "name": "build_generator",
                "run": "export PATH=/oss-cad-suite/bin:$PATH && cmake -S . -B build && cmake --build build --target rtlgen",
            },
            {
                "name": "probe_decoder_output_projection_ranker_wrapper_contract",
                "run": (
                    "python3 npu/eval/probe_llm_decoder_output_projection_ranker_wrapper_contract.py "
                    f"--policy {policy} "
                    f"--serial-wrapper {serial_wrapper} "
                    f"--ranktree-promotion {ranktree_promotion} "
                    f"--merge-config {merge_config} "
                    "--num-tiles 6 "
                    f"--out {out} "
                    f"--out-md {report}"
                ),
            },
        ],
        "expected_outputs": [out, report],
    }


def _decoder_output_projection_ranker_wrapper_physical_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    out = f"{base}/decoder_output_projection_ranker_wrapper_physical__{item_id}.json"
    report = f"{base}/decoder_output_projection_ranker_wrapper_physical__{item_id}.md"
    policy = (
        f"{base}/decoder_output_projection_ranker_policy__"
        "l2_decoder_output_projection_ranker_policy_v1.json"
    )
    wrapper_contract = (
        f"{base}/decoder_output_projection_ranker_wrapper_contract__"
        "l2_decoder_output_projection_ranker_wrapper_contract_v1.json"
    )
    merge_config = (
        "runs/designs/activations/candidate_stream_merge_fifo_k1_l16_t16_d16_wrapper/"
        "config_candidate_stream_merge_fifo_k1_l16_t16_d16.json"
    )
    sweep = "runs/campaigns/npu/decoder_output_projection_ranker_wrapper_physical/sweeps/nangate45_policy_wrapper.json"
    design_root = "runs/designs/activations"
    tops = [
        "decoder_output_ranker_policy_r64_wrapper",
        "decoder_output_ranker_policy_r128_wrapper",
    ]
    return {
        "inputs": {
            "output_projection_ranker_wrapper_physical_out": out,
            "output_projection_ranker_wrapper_physical_report": report,
            "output_projection_ranker_policy": policy,
            "output_projection_ranker_wrapper_contract": wrapper_contract,
            "candidate_merge_config": merge_config,
            "output_projection_ranker_wrapper_physical_sweep": sweep,
            "output_projection_ranker_wrapper_physical_make_target": "3_3_place_gp",
            "output_projection_ranker_wrapper_physical_scope": (
                "Generate concrete output-projection ranker policy wrappers for r64 and r128, "
                "simulate both serial and rank-tree selected paths, then measure wrapper mux/control "
                "and inactive-path overhead with a bounded nangate45 physical sweep."
            ),
        },
        "commands": [
            {
                "name": "build_generator",
                "run": "export PATH=/oss-cad-suite/bin:$PATH && cmake -S . -B build && cmake --build build --target rtlgen",
            },
            {
                "name": "probe_decoder_output_projection_ranker_wrapper_physical",
                "run": (
                    "python3 npu/eval/probe_llm_decoder_output_projection_ranker_wrapper_physical.py "
                    f"--policy {policy} "
                    f"--wrapper-contract {wrapper_contract} "
                    f"--merge-config {merge_config} "
                    f"--design-root {design_root} "
                    "--producer-lanes 64,128 "
                    f"--sweep {sweep} "
                    "--platform nangate45 "
                    "--make-target 3_3_place_gp "
                    "--timeout-seconds 1800 "
                    "--stall-timeout-seconds 900 "
                    f"--out {out} "
                    f"--out-md {report}"
                ),
            },
            {
                "name": "build_runs_index",
                "run": "python3 scripts/build_runs_index.py",
            },
        ],
        "expected_outputs": [
            out,
            report,
            "runs/index.csv",
            *[f"{design_root}/{top}/metrics.csv" for top in tops],
            *[f"{design_root}/{top}/verilog/{top}.v" for top in tops],
        ],
    }


def _decoder_output_projection_producer_ranker_integration_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    out = f"{base}/decoder_output_projection_producer_ranker_integration__{item_id}.json"
    report = f"{base}/decoder_output_projection_producer_ranker_integration__{item_id}.md"
    producer_summary = (
        "runs/campaigns/npu/e2e_eval_mlp_smoke_v1_reuse__"
        "l2_decoder_producer_ranker_physical_wrapper_v1/summary.csv"
    )
    ranker_wrapper_physical = (
        f"{base}/decoder_output_projection_ranker_wrapper_physical__"
        "l2_decoder_output_projection_ranker_wrapper_physical_v1.json"
    )
    policy = (
        f"{base}/decoder_output_projection_ranker_policy__"
        "l2_decoder_output_projection_ranker_policy_v1.json"
    )
    return {
        "inputs": {
            "output_projection_producer_ranker_integration_out": out,
            "output_projection_producer_ranker_integration_report": report,
            "output_projection_producer_summary": producer_summary,
            "output_projection_ranker_wrapper_physical": ranker_wrapper_physical,
            "output_projection_ranker_policy": policy,
            "output_projection_producer_ranker_integration_scope": (
                "Additively account independently measured output-projection producer PPA "
                "and measured output-ranker policy-wrapper PPA. Report timing bottleneck, "
                "area/power overhead, and serial versus rank-tree service behavior before "
                "requesting a heavier routed monolithic wrapper."
            ),
        },
        "commands": [
            {
                "name": "estimate_decoder_output_projection_producer_ranker_integration",
                "run": (
                    "python3 npu/eval/estimate_llm_decoder_output_projection_integrated_breakdown.py "
                    f"--producer-summary {producer_summary} "
                    f"--ranker-wrapper-physical {ranker_wrapper_physical} "
                    f"--policy {policy} "
                    "--lane-map fp16_nm1=64,fp16_nm2=128 "
                    f"--out {out} "
                    f"--out-md {report}"
                ),
            },
        ],
        "expected_outputs": [out, report],
    }


def _decoder_producer_ranker_policy_calibration_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    out = f"{base}/decoder_producer_ranker_policy_calibration__{item_id}.json"
    report = f"{base}/decoder_producer_ranker_policy_calibration__{item_id}.md"
    coupled = (
        f"{base}/decoder_producer_ranker_coupled_noc__"
        "l2_decoder_frontier_synthesis_integrated_v1.json"
    )
    ranker_wrapper_physical = (
        f"{base}/decoder_output_projection_ranker_wrapper_physical__"
        "l2_decoder_output_projection_ranker_wrapper_physical_v1.json"
    )
    policy = (
        f"{base}/decoder_output_projection_ranker_policy__"
        "l2_decoder_output_projection_ranker_policy_v1.json"
    )
    return {
        "inputs": {
            "producer_ranker_policy_calibration_out": out,
            "producer_ranker_policy_calibration_report": report,
            "producer_ranker_coupled_report": coupled,
            "output_projection_ranker_wrapper_physical": ranker_wrapper_physical,
            "output_projection_ranker_policy": policy,
            "producer_ranker_policy_calibration_scope": (
                "Recompute producer/ranker coupling with measured output-ranker policy-wrapper "
                "service latency. This preserves the old coupled report as baseline evidence while "
                "checking whether the reported output-projection domination came from stale ranker "
                "hierarchy latency rather than measured policy-wrapper service."
            ),
        },
        "commands": [
            {
                "name": "calibrate_decoder_producer_ranker_policy_service",
                "run": (
                    "python3 npu/eval/calibrate_llm_decoder_producer_ranker_policy_service.py "
                    f"--coupled-report {coupled} "
                    f"--wrapper-physical {ranker_wrapper_physical} "
                    f"--policy {policy} "
                    f"--out {out} "
                    f"--out-md {report}"
                ),
            },
        ],
        "expected_outputs": [out, report],
    }


def _decoder_stage_breakdown_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    out = f"{base}/decoder_stage_breakdown__{item_id}.json"
    report = f"{base}/decoder_stage_breakdown__{item_id}.md"
    return {
        "inputs": {
            "stage_breakdown_out": out,
            "stage_breakdown_report": report,
            "stage_breakdown_scope": (
                "Coarse whole-decoder single-token latency and traffic breakdown across attention, "
                "MLP, output projection, and ranker. Includes both streaming-weight and "
                "resident-weight bounds to expose when attention/KV traffic becomes dominant."
            ),
            "stage_breakdown_grid": {
                "sequence_length_list": [128, 512, 2048, 8192],
                "macs_per_cycle_list": [8192, 32768],
                "memory_bandwidth_bytes_per_cycle_list": [64, 256],
                "weight_residency_models": ["streaming_weights", "resident_weights"],
            },
        },
        "commands": [
            {
                "name": "estimate_decoder_stage_breakdown",
                "run": (
                    "python3 npu/eval/estimate_llm_decoder_stage_breakdown.py "
                    "--sequence-length-list 128,512,2048,8192 "
                    "--macs-per-cycle-list 8192,32768 "
                    "--memory-bandwidth-bytes-per-cycle-list 64,256 "
                    "--ranker-lanes 64 "
                    "--ranker-ii-cycles 384 "
                    f"--out {out} "
                    f"--out-md {report}"
                ),
            },
        ],
        "expected_outputs": [out, report],
    }


def _decoder_attention_kv_memory_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    out = f"{base}/decoder_attention_kv_memory__{item_id}.json"
    report = f"{base}/decoder_attention_kv_memory__{item_id}.md"
    return {
        "inputs": {
            "attention_kv_memory_out": out,
            "attention_kv_memory_report": report,
            "attention_kv_memory_scope": (
                "Coarse single-token decoder attention model that separates QKV projection, "
                "QK score, softmax, value mix, output projection, KV-cache memory tier, "
                "NoC hops, KV precision, and MHA/GQA/MQA sharing."
            ),
            "attention_kv_memory_grid": {
                "sequence_length_list": [128, 512, 2048, 8192, 32768, 131072],
                "macs_per_cycle_list": [8192, 32768, 131072, 524288],
                "kv_memory_tier_list": ["local_sram", "shared_sram", "hbm", "remote_hbm"],
                "kv_sharing_list": ["mha", "gqa4", "gqa8", "mqa"],
                "kv_bits_list": [8, 16],
                "noc_hops_list": [0, 1, 2, 4, 8],
            },
            "measured_tile_metrics": [
                "runs/designs/activations/attention_kv_tile_hd64_kv4_l16_b128_wrapper/metrics.csv",
                "runs/designs/activations/attention_kv_tile_hd64_kv4_l32_b256_wrapper/metrics.csv",
                "runs/designs/activations/attention_kv_tile_hd64_kv8_l32_b256_wrapper/metrics.csv",
                "runs/designs/activations/attention_kv_tile_hd128_kv4_l32_b256_wrapper/metrics.csv",
                "runs/designs/activations/attention_kv_tile_hd128_kv8_l64_b512_wrapper/metrics.csv",
                "runs/designs/activations/attention_kv_tile_hd128_kv16_l64_b512_wrapper/metrics.csv",
            ],
        },
        "commands": [
            {
                "name": "estimate_decoder_attention_kv_memory",
                "run": (
                    "python3 npu/eval/estimate_llm_decoder_attention_kv_memory.py "
                    "--sequence-length-list 128,512,2048,8192,32768,131072 "
                    "--macs-per-cycle-list 8192,32768,131072,524288 "
                    "--kv-memory-tier-list local_sram,shared_sram,hbm,remote_hbm "
                    "--kv-sharing-list mha,gqa4,gqa8,mqa "
                    "--kv-bits-list 8,16 "
                    "--noc-hops-list 1,2,4,8 "
                    "--noc-bandwidth-bytes-per-cycle 4096 "
                    "--measured-tile-metrics "
                    "runs/designs/activations/attention_kv_tile_hd64_kv4_l16_b128_wrapper/metrics.csv,"
                    "runs/designs/activations/attention_kv_tile_hd64_kv4_l32_b256_wrapper/metrics.csv,"
                    "runs/designs/activations/attention_kv_tile_hd64_kv8_l32_b256_wrapper/metrics.csv,"
                    "runs/designs/activations/attention_kv_tile_hd128_kv4_l32_b256_wrapper/metrics.csv,"
                    "runs/designs/activations/attention_kv_tile_hd128_kv8_l64_b512_wrapper/metrics.csv,"
                    "runs/designs/activations/attention_kv_tile_hd128_kv16_l64_b512_wrapper/metrics.csv "
                    f"--out {out} "
                    f"--out-md {report}"
                ),
            },
        ],
        "expected_outputs": [out, report],
    }


def _decoder_frontier_synthesis_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    stage = _decoder_stage_breakdown_evidence(item_id=item_id)
    attention = _decoder_attention_kv_memory_evidence(item_id=item_id)
    producer = _decoder_producer_ranker_coupled_noc_evidence(item_id=item_id)
    out = f"{base}/decoder_frontier_synthesis__{item_id}.json"
    report = f"{base}/decoder_frontier_synthesis__{item_id}.md"

    stage_out = stage["inputs"]["stage_breakdown_out"]
    attention_out = attention["inputs"]["attention_kv_memory_out"]
    producer_out = producer["inputs"]["producer_ranker_coupled_out"]
    commands = [
        *stage["commands"],
        *attention["commands"],
        *producer["commands"],
        {
            "name": "synthesize_decoder_frontier",
            "run": (
                "python3 npu/eval/synthesize_llm_decoder_frontier.py "
                f"--stage-breakdown {stage_out} "
                f"--attention-kv-memory {attention_out} "
                f"--producer-ranker-coupled {producer_out} "
                f"--out {out} "
                f"--out-md {report}"
            ),
        },
    ]
    return {
        "inputs": {
            **stage["inputs"],
            **attention["inputs"],
            **producer["inputs"],
            "decoder_frontier_synthesis_out": out,
            "decoder_frontier_synthesis_report": report,
            "decoder_frontier_synthesis_scope": (
                "Combine whole-decoder stage breakdown, measured attention/KV tile-calibrated "
                "memory pressure, and producer/ranker NoC coupling to identify the dominant "
                "frontier before queueing deeper RTL blocks."
            ),
        },
        "commands": commands,
        "expected_outputs": [
            *stage["expected_outputs"],
            *attention["expected_outputs"],
            *producer["expected_outputs"],
            out,
            report,
        ],
    }


def _decoder_frontier_synthesis_integrated_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    stage = _decoder_stage_breakdown_evidence(item_id=item_id)
    attention = _decoder_attention_kv_memory_evidence(item_id=item_id)
    producer = _decoder_producer_ranker_coupled_noc_evidence(item_id=item_id)
    integration = _decoder_output_projection_producer_ranker_integration_evidence(item_id=item_id)
    out = f"{base}/decoder_frontier_synthesis__{item_id}.json"
    report = f"{base}/decoder_frontier_synthesis__{item_id}.md"

    stage_out = stage["inputs"]["stage_breakdown_out"]
    attention_out = attention["inputs"]["attention_kv_memory_out"]
    producer_out = producer["inputs"]["producer_ranker_coupled_out"]
    integration_out = integration["inputs"]["output_projection_producer_ranker_integration_out"]
    commands = [
        *stage["commands"],
        *attention["commands"],
        *producer["commands"],
        *integration["commands"],
        {
            "name": "synthesize_decoder_frontier",
            "run": (
                "python3 npu/eval/synthesize_llm_decoder_frontier.py "
                f"--stage-breakdown {stage_out} "
                f"--attention-kv-memory {attention_out} "
                f"--producer-ranker-coupled {producer_out} "
                f"--producer-ranker-integration {integration_out} "
                f"--out {out} "
                f"--out-md {report}"
            ),
        },
    ]
    return {
        "inputs": {
            **stage["inputs"],
            **attention["inputs"],
            **producer["inputs"],
            **integration["inputs"],
            "decoder_frontier_synthesis_out": out,
            "decoder_frontier_synthesis_report": report,
            "decoder_frontier_synthesis_scope": (
                "Combine whole-decoder stage breakdown, measured attention/KV tile-calibrated "
                "memory pressure, producer/ranker NoC coupling, and measured additive "
                "producer/ranker integration accounting to identify the dominant frontier "
                "before queueing deeper RTL blocks."
            ),
        },
        "commands": commands,
        "expected_outputs": [
            *stage["expected_outputs"],
            *attention["expected_outputs"],
            *producer["expected_outputs"],
            *integration["expected_outputs"],
            out,
            report,
        ],
    }


def _decoder_frontier_synthesis_policy_calibrated_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    out = f"{base}/decoder_frontier_synthesis__{item_id}.json"
    report = f"{base}/decoder_frontier_synthesis__{item_id}.md"
    stage_out = f"{base}/decoder_stage_breakdown__l2_decoder_stage_breakdown_large_array_v2.json"
    attention_out = f"{base}/decoder_attention_kv_memory__l2_decoder_attention_kv_memory_131k_v1.json"
    producer_out = f"{base}/decoder_producer_ranker_coupled_noc__l2_decoder_frontier_synthesis_integrated_v1.json"
    integration_out = (
        f"{base}/decoder_output_projection_producer_ranker_integration__"
        "l2_decoder_frontier_synthesis_integrated_v1.json"
    )
    calibration_out = (
        f"{base}/decoder_producer_ranker_policy_calibration__"
        "l2_decoder_producer_ranker_policy_calibration_v1.json"
    )
    return {
        "inputs": {
            "stage_breakdown_out": stage_out,
            "attention_kv_memory_out": attention_out,
            "producer_ranker_coupled_out": producer_out,
            "output_projection_producer_ranker_integration_out": integration_out,
            "producer_ranker_policy_calibration_out": calibration_out,
            "decoder_frontier_synthesis_out": out,
            "decoder_frontier_synthesis_report": report,
            "decoder_frontier_synthesis_scope": (
                "Refresh whole-decoder frontier synthesis with the measured policy-wrapper "
                "producer/ranker latency calibration. This replaces the older streaming ranker "
                "hierarchy latency in the ranking while preserving the coupled and additive "
                "integration reports as context."
            ),
        },
        "commands": [
            {
                "name": "synthesize_decoder_frontier_policy_calibrated",
                "run": (
                    "python3 npu/eval/synthesize_llm_decoder_frontier.py "
                    f"--stage-breakdown {stage_out} "
                    f"--attention-kv-memory {attention_out} "
                    f"--producer-ranker-coupled {producer_out} "
                    f"--producer-ranker-integration {integration_out} "
                    f"--producer-ranker-policy-calibration {calibration_out} "
                    f"--out {out} "
                    f"--out-md {report}"
                ),
            },
        ],
        "expected_outputs": [out, report],
    }


def _decoder_output_projection_producer_memory_hierarchy_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    out = f"{base}/decoder_output_projection_producer_memory_hierarchy__{item_id}.json"
    report = f"{base}/decoder_output_projection_producer_memory_hierarchy__{item_id}.md"
    frontier = (
        f"{base}/decoder_frontier_synthesis__"
        "l2_decoder_frontier_synthesis_policy_calibrated_v1.json"
    )
    calibration = (
        f"{base}/decoder_producer_ranker_policy_calibration__"
        "l2_decoder_producer_ranker_policy_calibration_v1.json"
    )
    return {
        "inputs": {
            "producer_memory_hierarchy_out": out,
            "producer_memory_hierarchy_report": report,
            "frontier_synthesis_policy_calibrated": frontier,
            "producer_ranker_policy_calibration": calibration,
            "producer_memory_hierarchy_scope": (
                "Explore output-projection producer weight-memory hierarchy assumptions after "
                "ranker service calibration. Sweep cache capacity, effective cache hit rate, "
                "off-chip bandwidth, local-cache bandwidth, compute lanes, and producer lanes to "
                "identify whether producer latency is mainly storage/bandwidth limited or compute limited."
            ),
        },
        "commands": [
            {
                "name": "estimate_decoder_output_projection_producer_memory_hierarchy",
                "run": (
                    "python3 npu/eval/estimate_llm_decoder_output_projection_producer_memory_hierarchy.py "
                    f"--frontier {frontier} "
                    f"--calibration {calibration} "
                    "--producer-lanes-list 64,128,256 "
                    "--macs-per-cycle-list 32768,65536,131072 "
                    "--offchip-bw-bytes-per-cycle-list 256,1024,4096 "
                    "--local-cache-bw-bytes-per-cycle-list 1024,4096,16384 "
                    "--cache-capacity-mb-list 0,8,32,128,256 "
                    "--cache-hit-rate-list 0,0.5,0.9,0.99,1.0 "
                    f"--out {out} "
                    f"--out-md {report}"
                ),
            },
        ],
        "expected_outputs": [out, report],
    }


def _decoder_attention_kv_capacity_noc_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    out = f"{base}/decoder_attention_kv_capacity_noc__{item_id}.json"
    report = f"{base}/decoder_attention_kv_capacity_noc__{item_id}.md"
    return {
        "inputs": {
            "attention_kv_memory_out": out,
            "attention_kv_memory_report": report,
            "attention_kv_capacity_noc_scope": (
                "Capacity-constrained attention/KV memory and NoC baseline. Sweep die area, "
                "SRAM area fraction, usable SRAM fraction, bitcell density, local/shared SRAM "
                "partition, bank bandwidth, NoC bandwidth/hops, HBM bandwidth, KV sharing, and "
                "KV precision. Local/shared SRAM placements are disallowed unless the KV cache "
                "fits in the selected capacity."
            ),
        },
        "commands": [
            {
                "name": "estimate_decoder_attention_kv_capacity_noc",
                "run": (
                    "python3 npu/eval/estimate_llm_decoder_attention_kv_capacity_noc.py "
                    "--sequence-length-list 32768,131072 "
                    "--kv-sharing-list mqa,gqa8,mha "
                    "--kv-bits-list 8,16 "
                    "--die-area-mm2-list 25,50,100,200,400 "
                    "--sram-area-fraction-list 0.2,0.4,0.6 "
                    "--usable-sram-fraction-list 0.55,0.7 "
                    "--bitcell-area-um2-per-bit-list 0.02,0.05,0.1 "
                    "--local-sram-fraction-list 0.25,0.5,0.75 "
                    "--bank-count-list 16,64,256 "
                    "--bank-bandwidth-bytes-per-cycle-list 64,256,1024 "
                    "--noc-bandwidth-bytes-per-cycle-list 1024,4096,16384 "
                    "--noc-hops-list 1,2,4,8 "
                    "--hbm-bandwidth-bytes-per-cycle-list 256,1024,4096 "
                    "--macs-per-cycle 524288 "
                    "--vector-ops-per-cycle 65536 "
                    f"--out {out} "
                    f"--out-md {report}"
                ),
            },
        ],
        "expected_outputs": [out, report],
    }


def _decoder_attention_kv_noc_scheduler_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    out = f"{base}/decoder_attention_kv_noc_scheduler__{item_id}.json"
    report = f"{base}/decoder_attention_kv_noc_scheduler__{item_id}.md"
    capacity_noc = (
        f"{base}/decoder_attention_kv_capacity_noc__"
        "l2_decoder_attention_kv_capacity_noc_baseline_v1.json"
    )
    return {
        "inputs": {
            "attention_kv_memory_out": out,
            "attention_kv_memory_report": report,
            "attention_kv_capacity_noc_baseline": capacity_noc,
            "attention_kv_noc_scheduler_scope": (
                "Selected-point attention/KV NoC scheduler refinement. Use the capacity/NoC "
                "best-by-die frontier at the 131k-token transition points and estimate tile "
                "size, SRAM bank pressure, NoC hop/arbitration cost, virtual-channel relief, "
                "and strict-vs-overlap producer bounds."
            ),
        },
        "commands": [
            {
                "name": "estimate_decoder_attention_kv_noc_scheduler",
                "run": (
                    "python3 npu/eval/estimate_llm_decoder_attention_kv_noc_scheduler.py "
                    f"--capacity-noc-baseline {capacity_noc} "
                    "--selected-points "
                    "gpt2_small:131072:100,gpt2_small:131072:200,"
                    "gpt2_medium_proxy:131072:200,gpt2_medium_proxy:131072:400,"
                    "llama7b_proxy:131072:400 "
                    "--tile-tokens-list 128,256,512,1024,2048 "
                    "--virtual-channel-list 1,2,4 "
                    "--arbitration-efficiency-list 0.55,0.7,0.85 "
                    "--bank-interleave-tokens 16 "
                    "--bank-conflict-efficiency 0.75 "
                    "--router-latency-cycles-per-hop 2 "
                    "--macs-per-cycle 524288 "
                    "--vector-ops-per-cycle 65536 "
                    f"--out {out} "
                    f"--out-md {report}"
                ),
            },
        ],
        "expected_outputs": [out, report],
    }


def _decoder_attention_kv_spill_scheduler_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    out = f"{base}/decoder_attention_kv_spill_scheduler__{item_id}.json"
    report = f"{base}/decoder_attention_kv_spill_scheduler__{item_id}.md"
    capacity_noc = (
        f"{base}/decoder_attention_kv_capacity_noc__"
        "l2_decoder_attention_kv_capacity_noc_baseline_v1.json"
    )
    scheduler = (
        f"{base}/decoder_attention_kv_noc_scheduler__"
        "l2_decoder_attention_kv_noc_scheduler_selected_v1.json"
    )
    return {
        "inputs": {
            "attention_kv_memory_out": out,
            "attention_kv_memory_report": report,
            "attention_kv_capacity_noc_baseline": capacity_noc,
            "attention_kv_noc_scheduler_selected": scheduler,
            "attention_kv_spill_scheduler_scope": (
                "Tile-level spill scheduler for the hard llama7b_proxy 131k 400 mm2 point. "
                "Refine the shared-SRAM/HBM spill result with HBM prefetch distance, finite "
                "outstanding HBM requests, HBM efficiency, NoC arbitration, virtual channels, "
                "bank conflict pressure, and producer-prefetch overlap."
            ),
        },
        "commands": [
            {
                "name": "estimate_decoder_attention_kv_spill_scheduler",
                "run": (
                    "python3 npu/eval/estimate_llm_decoder_attention_kv_spill_scheduler.py "
                    f"--capacity-noc-baseline {capacity_noc} "
                    "--label llama7b_proxy "
                    "--sequence-length 131072 "
                    "--die-area-mm2 400 "
                    "--tile-tokens-list 256,512,1024,2048,4096 "
                    "--prefetch-distance-tiles-list 1,2,4,8,16 "
                    "--hbm-outstanding-list 1,2,4,8 "
                    "--hbm-efficiency-list 0.4,0.6,0.8 "
                    "--arbitration-efficiency-list 0.55,0.7,0.85 "
                    "--virtual-channel-list 1,2,4 "
                    "--bank-interleave-tokens 16 "
                    "--bank-conflict-efficiency 0.75 "
                    "--router-latency-cycles-per-hop 2 "
                    "--prefetch-start-list after_qkv,during_qkv "
                    "--macs-per-cycle 524288 "
                    "--vector-ops-per-cycle 65536 "
                    f"--out {out} "
                    f"--out-md {report}"
                ),
            },
        ],
        "expected_outputs": [out, report],
    }


def _decoder_attention_kv_hbm_controller_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    out = f"{base}/decoder_attention_kv_hbm_controller__{item_id}.json"
    report = f"{base}/decoder_attention_kv_hbm_controller__{item_id}.md"
    capacity_noc = (
        f"{base}/decoder_attention_kv_capacity_noc__"
        "l2_decoder_attention_kv_capacity_noc_baseline_v1.json"
    )
    spill = (
        f"{base}/decoder_attention_kv_spill_scheduler__"
        "l2_decoder_attention_kv_spill_scheduler_llama7b_v1_r2.json"
    )
    return {
        "inputs": {
            "attention_kv_memory_out": out,
            "attention_kv_memory_report": report,
            "attention_kv_capacity_noc_baseline": capacity_noc,
            "attention_kv_spill_scheduler": spill,
            "attention_kv_hbm_controller_scope": (
                "HBM-controller realism refinement for the llama7b_proxy 131k 400 mm2 "
                "spill point. Derive HBM service from channel count, per-channel bandwidth, "
                "burst size, outstanding requests, command overhead, row-hit rate, row-miss "
                "penalty, and scheduler efficiency before rerunning the tile-level spill model."
            ),
        },
        "commands": [
            {
                "name": "estimate_decoder_attention_kv_hbm_controller",
                "run": (
                    "python3 npu/eval/estimate_llm_decoder_attention_kv_hbm_controller.py "
                    f"--capacity-noc-baseline {capacity_noc} "
                    "--label llama7b_proxy "
                    "--sequence-length 131072 "
                    "--die-area-mm2 400 "
                    "--tile-tokens-list 1024,2048,4096 "
                    "--prefetch-distance-tiles-list 2,4,8,16 "
                    "--channel-count-list 4,8,16 "
                    "--channel-bandwidth-bytes-per-cycle-list 128,256,512 "
                    "--burst-bytes-list 256,512,1024 "
                    "--hbm-outstanding-list 2,4,8,16 "
                    "--request-overhead-cycles-list 4,8,16 "
                    "--row-hit-rate-list 0.5,0.75,0.9 "
                    "--row-miss-penalty-cycles-list 16,32,64 "
                    "--scheduler-efficiency-list 0.6,0.75,0.9 "
                    "--arbitration-efficiency-list 0.7,0.85 "
                    "--virtual-channel-list 2,4 "
                    "--prefetch-start-list during_qkv "
                    "--bank-interleave-tokens 16 "
                    "--bank-conflict-efficiency 0.75 "
                    "--router-latency-cycles-per-hop 2 "
                    "--macs-per-cycle 524288 "
                    "--vector-ops-per-cycle 65536 "
                    f"--out {out} "
                    f"--out-md {report}"
                ),
            },
        ],
        "expected_outputs": [out, report],
    }


def _decoder_attention_kv_physical_hbm_frontier_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    out = f"{base}/decoder_attention_kv_physical_hbm_frontier__{item_id}.json"
    report = f"{base}/decoder_attention_kv_physical_hbm_frontier__{item_id}.md"
    return {
        "inputs": {
            "attention_kv_memory_out": out,
            "attention_kv_memory_report": report,
            "attention_kv_physical_hbm_frontier_scope": (
                "Physical-HBM and KV-byte-reduction frontier for llama7b_proxy decode. "
                "Derive HBM bandwidth from stack count, pseudo-channel count, interface width, "
                "MT/s, and core clock; then sweep KV sharing, packed KV bitwidth, die SRAM "
                "capacity, tile size, and prefetch service."
            ),
        },
        "commands": [
            {
                "name": "estimate_decoder_attention_kv_physical_hbm_frontier",
                "run": (
                    "python3 npu/eval/estimate_llm_decoder_attention_kv_physical_hbm_frontier.py "
                    "--label llama7b_proxy "
                    "--sequence-length-list 32768,65536,131072 "
                    "--die-area-mm2-list 100,200,400 "
                    "--kv-sharing-list mha,gqa4,gqa8,mqa "
                    "--kv-bits-list 16,8,4 "
                    "--stack-count-list 1,2,4,8 "
                    "--pseudo-channels-per-stack-list 8,16 "
                    "--pseudo-channel-width-bits-list 64 "
                    "--data-rate-mtps-list 3200,6400,9000 "
                    "--hbm-efficiency-list 0.35,0.55,0.75 "
                    "--tile-tokens-list 512,1024 "
                    "--prefetch-distance-tiles-list 4 "
                    "--hbm-outstanding-list 8,16 "
                    "--arbitration-efficiency-list 0.85 "
                    "--virtual-channel-list 4 "
                    "--prefetch-start-list during_qkv "
                    "--sram-area-fraction 0.6 "
                    "--usable-sram-fraction 0.7 "
                    "--bitcell-area-um2-per-bit 0.02 "
                    "--local-sram-fraction 0.25 "
                    "--bank-count 16 "
                    "--bank-bandwidth-bytes-per-cycle 1024 "
                    "--bank-interleave-tokens 16 "
                    "--bank-conflict-efficiency 0.75 "
                    "--noc-bandwidth-bytes-per-cycle 16384 "
                    "--noc-hops 1 "
                    "--router-latency-cycles-per-hop 2 "
                    "--macs-per-cycle 524288 "
                    "--vector-ops-per-cycle 65536 "
                    "--clock-ns 1.0 "
                    f"--out {out} "
                    f"--out-md {report}"
                ),
            },
        ],
        "expected_outputs": [out, report],
    }


def _decoder_attention_kv_physical_hbm_quality_backed_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    out = f"{base}/decoder_attention_kv_physical_hbm_quality_backed__{item_id}.json"
    report = f"{base}/decoder_attention_kv_physical_hbm_quality_backed__{item_id}.md"
    native_quality = (
        f"{base}/decoder_attention_kv_model_native_quality__"
        "l2_decoder_attention_kv_model_native_quality_tinyllama_v1_r2.json"
    )
    native_recovery = (
        f"{base}/decoder_attention_kv_model_native_recovery__"
        "l2_decoder_attention_kv_model_native_recovery_tinyllama_v1.json"
    )
    physical_frontier = (
        f"{base}/decoder_attention_kv_physical_hbm_frontier__"
        "l2_decoder_attention_kv_physical_hbm_frontier_llama7b_v1.json"
    )
    return {
        "inputs": {
            "attention_kv_model_native_quality": native_quality,
            "attention_kv_model_native_recovery": native_recovery,
            "attention_kv_physical_hbm_frontier": physical_frontier,
            "attention_kv_memory_out": out,
            "attention_kv_memory_report": report,
            "attention_kv_physical_hbm_quality_backed_out": out,
            "attention_kv_physical_hbm_quality_backed_report": report,
            "attention_kv_physical_hbm_quality_backed_scope": (
                "Quality-backed physical-HBM frontier for llama7b_proxy decode. "
                "Constrain the physical sweep to native-GQA group-8 KV storage with "
                "KV16 and KV8 only: native TinyLlama evidence accepts KV8, while "
                "KV4 remains below top-1/top-k thresholds even with per-token-vector "
                "scaling. MQA and other structural KV sharing are excluded until "
                "trained-checkpoint quality evidence exists."
            ),
        },
        "commands": [
            {
                "name": "estimate_decoder_attention_kv_physical_hbm_quality_backed",
                "run": (
                    "python3 npu/eval/estimate_llm_decoder_attention_kv_physical_hbm_frontier.py "
                    "--label llama7b_proxy "
                    "--sequence-length-list 32768,65536,131072 "
                    "--die-area-mm2-list 100,200,400 "
                    "--kv-sharing-list gqa8 "
                    "--kv-bits-list 16,8 "
                    "--stack-count-list 1,2,4,8 "
                    "--pseudo-channels-per-stack-list 8,16 "
                    "--pseudo-channel-width-bits-list 64 "
                    "--data-rate-mtps-list 3200,6400,9000 "
                    "--hbm-efficiency-list 0.35,0.55,0.75 "
                    "--tile-tokens-list 512,1024 "
                    "--prefetch-distance-tiles-list 4 "
                    "--hbm-outstanding-list 8,16 "
                    "--arbitration-efficiency-list 0.85 "
                    "--virtual-channel-list 4 "
                    "--prefetch-start-list during_qkv "
                    "--sram-area-fraction 0.6 "
                    "--usable-sram-fraction 0.7 "
                    "--bitcell-area-um2-per-bit 0.02 "
                    "--local-sram-fraction 0.25 "
                    "--bank-count 16 "
                    "--bank-bandwidth-bytes-per-cycle 1024 "
                    "--bank-interleave-tokens 16 "
                    "--bank-conflict-efficiency 0.75 "
                    "--noc-bandwidth-bytes-per-cycle 16384 "
                    "--noc-hops 1 "
                    "--router-latency-cycles-per-hop 2 "
                    "--macs-per-cycle 524288 "
                    "--vector-ops-per-cycle 65536 "
                    "--clock-ns 1.0 "
                    f"--out {out} "
                    f"--out-md {report}"
                ),
            },
        ],
        "expected_outputs": [out, report],
    }


def _decoder_attention_kv_physical_hbm_memory_noc_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    out = f"{base}/decoder_attention_kv_physical_hbm_memory_noc__{item_id}.json"
    report = f"{base}/decoder_attention_kv_physical_hbm_memory_noc__{item_id}.md"
    quality_backed = (
        f"{base}/decoder_attention_kv_physical_hbm_quality_backed__"
        "l2_decoder_attention_kv_physical_hbm_quality_backed_llama7b_v1.json"
    )
    native_recovery = (
        f"{base}/decoder_attention_kv_model_native_recovery__"
        "l2_decoder_attention_kv_model_native_recovery_tinyllama_v1.json"
    )
    return {
        "inputs": {
            "attention_kv_physical_hbm_quality_backed": quality_backed,
            "attention_kv_model_native_recovery": native_recovery,
            "attention_kv_memory_out": out,
            "attention_kv_memory_report": report,
            "attention_kv_physical_hbm_memory_noc_scope": (
                "Quality-backed native-GQA KV8 memory/NoC sensitivity at 131k context. "
                "Keep KV4 and MQA out of the ranking, then vary die size, SRAM area/use "
                "fraction, local/shared split, bank service, NoC bandwidth/hops, tile size, "
                "and HBM service to see whether the optimum moves from HBM-bound to SRAM/NoC "
                "or compute-bound under practical physical constraints."
            ),
        },
        "commands": [
            {
                "name": "estimate_decoder_attention_kv_physical_hbm_memory_noc",
                "run": (
                    "python3 npu/eval/estimate_llm_decoder_attention_kv_physical_hbm_frontier.py "
                    "--label llama7b_proxy "
                    "--sequence-length-list 131072 "
                    "--die-area-mm2-list 100,200,400,800,1200 "
                    "--kv-sharing-list gqa8 "
                    "--kv-bits-list 8,16 "
                    "--stack-count-list 8 "
                    "--pseudo-channels-per-stack-list 16 "
                    "--pseudo-channel-width-bits-list 64 "
                    "--data-rate-mtps-list 6400,9000 "
                    "--hbm-efficiency-list 0.55,0.75 "
                    "--tile-tokens-list 512,1024 "
                    "--prefetch-distance-tiles-list 4 "
                    "--hbm-outstanding-list 8,16 "
                    "--arbitration-efficiency-list 0.85 "
                    "--virtual-channel-list 4 "
                    "--prefetch-start-list during_qkv "
                    "--sram-area-fraction 0.4,0.6,0.75 "
                    "--usable-sram-fraction 0.7,0.85 "
                    "--bitcell-area-um2-per-bit 0.02,0.05 "
                    "--local-sram-fraction 0.1,0.25,0.5 "
                    "--bank-count 16,64 "
                    "--bank-bandwidth-bytes-per-cycle 512,2048 "
                    "--bank-interleave-tokens 16 "
                    "--bank-conflict-efficiency 0.75 "
                    "--noc-bandwidth-bytes-per-cycle 8192,32768 "
                    "--noc-hops 1,4 "
                    "--router-latency-cycles-per-hop 2 "
                    "--macs-per-cycle 524288 "
                    "--vector-ops-per-cycle 65536 "
                    "--clock-ns 1.0 "
                    f"--out {out} "
                    f"--out-md {report}"
                ),
            },
        ],
        "expected_outputs": [out, report],
    }


def _decoder_attention_kv_physical_hbm_compute_sensitivity_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    out = f"{base}/decoder_attention_kv_physical_hbm_compute_sensitivity__{item_id}.json"
    report = f"{base}/decoder_attention_kv_physical_hbm_compute_sensitivity__{item_id}.md"
    memory_noc = (
        f"{base}/decoder_attention_kv_physical_hbm_memory_noc__"
        "l2_decoder_attention_kv_physical_hbm_memory_noc_llama7b_v1_r2.json"
    )
    native_recovery = (
        f"{base}/decoder_attention_kv_model_native_recovery__"
        "l2_decoder_attention_kv_model_native_recovery_tinyllama_v1.json"
    )
    return {
        "inputs": {
            "attention_kv_physical_hbm_memory_noc": memory_noc,
            "attention_kv_model_native_recovery": native_recovery,
            "attention_kv_memory_out": out,
            "attention_kv_memory_report": report,
            "attention_kv_physical_hbm_compute_sensitivity_scope": (
                "Quality-backed native-GQA KV8 compute-downsizing sensitivity at 131k context. "
                "Hold the best practical HBM and high-SRAM memory/NoC region from the previous "
                "frontier, then sweep MAC/cycle and vector-op/cycle throughput downward to find "
                "the smallest compute array that remains memory-bound."
            ),
        },
        "commands": [
            {
                "name": "estimate_decoder_attention_kv_physical_hbm_compute_sensitivity",
                "run": (
                    "python3 npu/eval/estimate_llm_decoder_attention_kv_physical_hbm_frontier.py "
                    "--label llama7b_proxy "
                    "--sequence-length-list 131072 "
                    "--die-area-mm2-list 400,800,1200 "
                    "--kv-sharing-list gqa8 "
                    "--kv-bits-list 8 "
                    "--stack-count-list 8 "
                    "--pseudo-channels-per-stack-list 16 "
                    "--pseudo-channel-width-bits-list 64 "
                    "--data-rate-mtps-list 9000 "
                    "--hbm-efficiency-list 0.75 "
                    "--tile-tokens-list 512,1024 "
                    "--prefetch-distance-tiles-list 4 "
                    "--hbm-outstanding-list 16 "
                    "--arbitration-efficiency-list 0.85 "
                    "--virtual-channel-list 4 "
                    "--prefetch-start-list during_qkv "
                    "--sram-area-fraction 0.75 "
                    "--usable-sram-fraction 0.7,0.85 "
                    "--bitcell-area-um2-per-bit 0.02 "
                    "--local-sram-fraction 0.1,0.25,0.5 "
                    "--bank-count 16,64 "
                    "--bank-bandwidth-bytes-per-cycle 2048 "
                    "--bank-interleave-tokens 16 "
                    "--bank-conflict-efficiency 0.75 "
                    "--noc-bandwidth-bytes-per-cycle 32768 "
                    "--noc-hops 1 "
                    "--router-latency-cycles-per-hop 2 "
                    "--macs-per-cycle 32768,65536,131072,262144,524288 "
                    "--vector-ops-per-cycle 8192,16384,32768,65536 "
                    "--clock-ns 1.0 "
                    f"--out {out} "
                    f"--out-md {report}"
                ),
            },
        ],
        "expected_outputs": [out, report],
    }


def _decoder_attention_kv_compute_floor_gap_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    out = f"{base}/decoder_attention_kv_compute_floor_gap__{item_id}.json"
    report = f"{base}/decoder_attention_kv_compute_floor_gap__{item_id}.md"
    compute_sensitivity = (
        f"{base}/decoder_attention_kv_physical_hbm_compute_sensitivity__"
        "l2_decoder_attention_kv_physical_hbm_compute_sensitivity_llama7b_v2.json"
    )
    measured_compute = (
        f"{base}/decoder_attention_kv_measured_compute__"
        "l2_decoder_attention_kv_measured_compute_llama7b_v1.json"
    )
    measured_partition = (
        f"{base}/decoder_attention_kv_measured_compute_partition__"
        "l2_decoder_attention_kv_measured_compute_partition_llama7b_v1.json"
    )
    return {
        "inputs": {
            "attention_kv_physical_hbm_compute_sensitivity": compute_sensitivity,
            "attention_kv_measured_compute": measured_compute,
            "attention_kv_measured_compute_partition": measured_partition,
            "attention_kv_compute_floor_gap_out": out,
            "attention_kv_compute_floor_gap_report": report,
            "attention_kv_compute_floor_gap_scope": (
                "Compare the merged Llama7B 131k HBM-bound compute floor against merged "
                "measured NPU compute PPA and clustered measured-compute partition results. "
                "Quantify the MAC/cycle and MAC/cycle/mm2 gap before requesting deeper "
                "SRAM/NoC arbitration simulation."
            ),
        },
        "commands": [
            {
                "name": "estimate_decoder_attention_kv_compute_floor_gap",
                "run": (
                    "python3 npu/eval/estimate_llm_decoder_attention_kv_compute_floor_gap.py "
                    f"--compute-sensitivity {compute_sensitivity} "
                    f"--measured-compute {measured_compute} "
                    f"--measured-partition {measured_partition} "
                    "--target-macs-per-cycle-list 131072,262144,524288 "
                    "--die-area-mm2-list 400,800,1200 "
                    "--logic-area-fraction-list 0.2,0.4,0.6 "
                    f"--out {out} "
                    f"--out-md {report}"
                ),
            },
        ],
        "expected_outputs": [out, report],
    }


def _decoder_attention_kv_compute_ceiling_envelope_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    out = f"{base}/decoder_attention_kv_compute_ceiling_envelope__{item_id}.json"
    report = f"{base}/decoder_attention_kv_compute_ceiling_envelope__{item_id}.md"
    compute_sensitivity = (
        f"{base}/decoder_attention_kv_physical_hbm_compute_sensitivity__"
        "l2_decoder_attention_kv_physical_hbm_compute_sensitivity_llama7b_v2.json"
    )
    measured_compute = (
        f"{base}/decoder_attention_kv_measured_compute__"
        "l2_decoder_attention_kv_measured_compute_llama7b_v1.json"
    )
    internal_measurements = "runs/design_registry/internal_measurements.jsonl"
    external_measurements = "runs/design_registry/external_measurements.jsonl"
    comparison_claims = "runs/design_registry/comparison_claims.jsonl"
    return {
        "inputs": {
            "attention_kv_physical_hbm_compute_sensitivity": compute_sensitivity,
            "attention_kv_measured_compute": measured_compute,
            "design_registry_internal_measurements": internal_measurements,
            "design_registry_external_measurements": external_measurements,
            "design_registry_comparison_claims": comparison_claims,
            "attention_kv_compute_ceiling_envelope_out": out,
            "attention_kv_compute_ceiling_envelope_report": report,
            "attention_kv_compute_ceiling_envelope_scope": (
                "Recompute the Llama7B attention/KV frontier under physical compute-density "
                "ceilings derived from measured RTLGen PPA and explicit optimistic external "
                "reference envelopes. Require registry evidence citations for internal "
                "baselines and third-party calibration references."
            ),
        },
        "commands": [
            {
                "name": "estimate_decoder_attention_kv_compute_ceiling_envelope",
                "run": (
                    "python3 npu/eval/estimate_llm_decoder_attention_kv_compute_ceiling_envelope.py "
                    f"--compute-sensitivity {compute_sensitivity} "
                    f"--measured-compute {measured_compute} "
                    f"--internal-measurements {internal_measurements} "
                    f"--external-measurements {external_measurements} "
                    f"--comparison-claims {comparison_claims} "
                    "--density-envelope-macs-per-cycle-per-mm2-list 150,300 "
                    "--die-area-mm2-list 400,800,1200 "
                    "--logic-area-fraction-list 0.2,0.4,0.6 "
                    "--vector-ops-per-mac 0.125 "
                    f"--out {out} "
                    f"--out-md {report}"
                ),
            },
        ],
        "expected_outputs": [out, report],
    }


def _decoder_attention_kv_measured_compute_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    out = f"{base}/decoder_attention_kv_measured_compute__{item_id}.json"
    report = f"{base}/decoder_attention_kv_measured_compute__{item_id}.md"
    memory_noc = (
        f"{base}/decoder_attention_kv_physical_hbm_memory_noc__"
        "l2_decoder_attention_kv_physical_hbm_memory_noc_llama7b_v1_r2.json"
    )
    compute_frontier = "docs/proposals/prop_l1_npu_corrected_compute_frontier_v1/promotion_result.json"
    iso_util = "docs/proposals/prop_l1_npu_corrected_compute_iso_util_v1/promotion_result.json"
    return {
        "inputs": {
            "attention_kv_physical_hbm_memory_noc": memory_noc,
            "corrected_compute_frontier": compute_frontier,
            "corrected_compute_iso_util": iso_util,
            "attention_kv_memory_out": out,
            "attention_kv_memory_report": report,
            "attention_kv_measured_compute_scope": (
                "Quality-backed native-GQA KV8 Llama7B 131k estimate using merged corrected "
                "NPU compute PPA instead of abstract MAC/cycle points. The sweep converts "
                "measured nm1..nm64 block area, power, delay, and num_modules into die-budgeted "
                "replica counts, then substitutes the resulting throughput and clock into the "
                "physical-HBM memory/NoC model."
            ),
        },
        "commands": [
            {
                "name": "estimate_decoder_attention_kv_measured_compute",
                "run": (
                    "python3 npu/eval/estimate_llm_decoder_attention_kv_measured_compute.py "
                    "--repo-root . "
                    "--tag-substring compute_stability_cmp33 "
                    "--sequence-length-list 131072 "
                    "--die-area-mm2-list 100,200,400,800,1200 "
                    "--sram-area-fraction 0.4,0.6,0.75 "
                    "--logic-area-fraction 0.05,0.1,0.2 "
                    "--reserved-area-fraction 0.1 "
                    "--usable-sram-fraction 0.7,0.85 "
                    "--local-sram-fraction 0.1,0.25,0.5 "
                    "--tile-tokens-list 512,1024 "
                    "--bank-count 16,64 "
                    "--vector-ops-per-mac 0.125 "
                    f"--out {out} "
                    f"--out-md {report}"
                ),
            },
        ],
        "expected_outputs": [out, report],
    }


def _decoder_attention_kv_dense_tile_measured_compute_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    out = f"{base}/decoder_attention_kv_dense_tile_measured_compute__{item_id}.json"
    report = f"{base}/decoder_attention_kv_dense_tile_measured_compute__{item_id}.md"
    memory_noc = (
        f"{base}/decoder_attention_kv_physical_hbm_memory_noc__"
        "l2_decoder_attention_kv_physical_hbm_memory_noc_llama7b_v1_r2.json"
    )
    dense_scaling = "docs/proposals/prop_l1_npu_dense_gemm_tile_scaling_v2/promotion_result.json"
    dense_envelope = (
        f"{base}/decoder_attention_kv_compute_ceiling_envelope__"
        "l2_decoder_attention_kv_dense_compute_ceiling_envelope_llama7b_v2.json"
    )
    return {
        "inputs": {
            "attention_kv_physical_hbm_memory_noc": memory_noc,
            "dense_gemm_tile_scaling": dense_scaling,
            "attention_kv_dense_compute_ceiling_envelope": dense_envelope,
            "attention_kv_dense_tile_measured_compute_out": out,
            "attention_kv_dense_tile_measured_compute_report": report,
            "attention_kv_dense_tile_measured_compute_scope": (
                "Quality-backed native-GQA KV8 Llama7B 131k estimate using merged dense FP16 "
                "GEMM tile PPA instead of the older nm-count compute blocks. The sweep converts "
                "measured 8x16, 16x8, and 16x16 dense tile area, power, delay, and MAC/cycle "
                "into die-budgeted replica counts, then substitutes the resulting throughput "
                "and clock into the physical-HBM memory/NoC model."
            ),
        },
        "commands": [
            {
                "name": "estimate_decoder_attention_kv_dense_tile_measured_compute",
                "run": (
                    "python3 npu/eval/estimate_llm_decoder_attention_kv_measured_compute.py "
                    "--repo-root . "
                    "--compute-source dense_gemm_tile "
                    "--tag-substring npu_dense_gemm_tile_v2_scale_hier "
                    "--sequence-length-list 131072 "
                    "--die-area-mm2-list 100,200,400,800,1200 "
                    "--sram-area-fraction 0.4,0.6,0.75 "
                    "--logic-area-fraction 0.05,0.1,0.2,0.4,0.6 "
                    "--reserved-area-fraction 0.1 "
                    "--usable-sram-fraction 0.7,0.85 "
                    "--local-sram-fraction 0.1,0.25,0.5 "
                    "--tile-tokens-list 512,1024 "
                    "--bank-count 16,64 "
                    "--vector-ops-per-mac 0.125 "
                    f"--out {out} "
                    f"--out-md {report}"
                ),
            },
        ],
        "expected_outputs": [out, report],
    }


def _decoder_attention_kv_measured_compute_partition_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    out = f"{base}/decoder_attention_kv_measured_compute_partition__{item_id}.json"
    report = f"{base}/decoder_attention_kv_measured_compute_partition__{item_id}.md"
    measured_compute = (
        f"{base}/decoder_attention_kv_measured_compute__"
        "l2_decoder_attention_kv_measured_compute_llama7b_v1.json"
    )
    return {
        "inputs": {
            "attention_kv_measured_compute": measured_compute,
            "attention_kv_partition_out": out,
            "attention_kv_partition_report": report,
            "attention_kv_measured_compute_partition_scope": (
                "Quality-backed native-GQA KV8 Llama7B 131k estimate that keeps merged measured "
                "NPU compute PPA but compares clustered sequence-sharded compute fabrics. The "
                "sweep varies cluster count, local/shared SRAM split, NoC bandwidth, and NoC hop "
                "penalty so the measured-compute frontier is not ranked only as one monolithic "
                "compute fabric."
            ),
        },
        "commands": [
            {
                "name": "estimate_decoder_attention_kv_measured_compute_partition",
                "run": (
                    "python3 npu/eval/estimate_llm_decoder_attention_kv_measured_compute_partition.py "
                    "--repo-root . "
                    "--tag-substring compute_stability_cmp33 "
                    "--sequence-length-list 131072 "
                    "--die-area-mm2-list 100,200,400,800,1200 "
                    "--sram-area-fraction 0.4,0.6,0.75 "
                    "--logic-area-fraction 0.05,0.1,0.2 "
                    "--reserved-area-fraction 0.1 "
                    "--usable-sram-fraction 0.7,0.85 "
                    "--local-sram-fraction 0.1,0.25,0.5 "
                    "--tile-tokens-list 512,1024 "
                    "--bank-count 16,64 "
                    "--cluster-count 1,2,4,8,16,32,64 "
                    "--noc-bandwidth-bytes-per-cycle 8192,32768,131072 "
                    "--noc-hops 1,2,4 "
                    "--vector-ops-per-mac 0.125 "
                    f"--out {out} "
                    f"--out-md {report}"
                ),
            },
        ],
        "expected_outputs": [out, report],
    }


def _decoder_attention_kv_clustered_schedule_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    out = f"{base}/decoder_attention_kv_clustered_schedule__{item_id}.json"
    report = f"{base}/decoder_attention_kv_clustered_schedule__{item_id}.md"
    measured_partition = (
        f"{base}/decoder_attention_kv_measured_compute_partition__"
        "l2_decoder_attention_kv_measured_compute_partition_llama7b_v1.json"
    )
    return {
        "inputs": {
            "attention_kv_measured_compute_partition": measured_partition,
            "attention_kv_clustered_schedule_out": out,
            "attention_kv_clustered_schedule_report": report,
            "attention_kv_clustered_schedule_scope": (
                "Quality-backed native-GQA KV8 Llama7B 131k estimate that keeps measured "
                "compute PPA and clustered sequence tiling, but makes cross-tile softmax/value "
                "reduction explicit. The sweep compares centralized per-tile reduction, "
                "owner-cluster local reduction, and tree reduction so the prior wave-only "
                "partition model can be checked for hidden reduction optimism."
            ),
        },
        "commands": [
            {
                "name": "estimate_decoder_attention_kv_clustered_schedule",
                "run": (
                    "python3 npu/eval/estimate_llm_decoder_attention_kv_clustered_schedule.py "
                    "--repo-root . "
                    "--tag-substring compute_stability_cmp33 "
                    "--sequence-length-list 131072 "
                    "--die-area-mm2-list 100,200,400,800,1200 "
                    "--sram-area-fraction 0.4,0.6,0.75 "
                    "--logic-area-fraction 0.05,0.1,0.2 "
                    "--reserved-area-fraction 0.1 "
                    "--usable-sram-fraction 0.7,0.85 "
                    "--local-sram-fraction 0.1,0.25,0.5 "
                    "--tile-tokens-list 256,512,1024 "
                    "--bank-count 16,64 "
                    "--cluster-count 1,2,4,8,16 "
                    "--noc-bandwidth-bytes-per-cycle 8192,32768,131072 "
                    "--noc-hops 1,2,4 "
                    "--reduction-strategy owner_cluster,cluster_tree,centralized_tile "
                    "--vector-ops-per-mac 0.125 "
                    "--reduction-scalar-bytes 2 "
                    f"--out {out} "
                    f"--out-md {report}"
                ),
            },
        ],
        "expected_outputs": [out, report],
    }


def _decoder_attention_kv_clustered_schedule_overhead_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    out = f"{base}/decoder_attention_kv_clustered_schedule_overhead__{item_id}.json"
    report = f"{base}/decoder_attention_kv_clustered_schedule_overhead__{item_id}.md"
    clustered_schedule = (
        f"{base}/decoder_attention_kv_clustered_schedule__"
        "l2_decoder_attention_kv_clustered_schedule_llama7b_v1_r2.json"
    )
    return {
        "inputs": {
            "attention_kv_clustered_schedule": clustered_schedule,
            "attention_kv_clustered_schedule_overhead_out": out,
            "attention_kv_clustered_schedule_overhead_report": report,
            "attention_kv_clustered_schedule_overhead_scope": (
                "Sensitivity pass for the quality-backed native-GQA KV8 Llama7B 131k clustered "
                "attention schedule. Keep the measured-compute sweep space but add explicit "
                "command-dispatch and reducer overhead knobs to test whether the current "
                "nm64-flat/owner-cluster frontier is fragile before investing in routed command "
                "hierarchy RTL."
            ),
        },
        "commands": [
            {
                "name": "estimate_decoder_attention_kv_clustered_schedule_overhead",
                "run": (
                    "python3 npu/eval/estimate_llm_decoder_attention_kv_clustered_schedule.py "
                    "--repo-root . "
                    "--tag-substring compute_stability_cmp33 "
                    "--sequence-length-list 131072 "
                    "--die-area-mm2-list 400,800,1200 "
                    "--sram-area-fraction 0.4 "
                    "--logic-area-fraction 0.2 "
                    "--reserved-area-fraction 0.1 "
                    "--usable-sram-fraction 0.7 "
                    "--local-sram-fraction 0.1,0.25 "
                    "--tile-tokens-list 1024 "
                    "--bank-count 16 "
                    "--cluster-count 1,2,4,8,16 "
                    "--noc-bandwidth-bytes-per-cycle 32768 "
                    "--noc-hops 1,2 "
                    "--reduction-strategy owner_cluster,cluster_tree,centralized_tile "
                    "--vector-ops-per-mac 0.125 "
                    "--reduction-scalar-bytes 2 "
                    "--command-cycles-per-tile 0,1,4,16 "
                    "--command-cycles-per-wave 0,8,32 "
                    "--reducer-setup-cycles 0,32,128 "
                    "--reduction-cycle-multiplier 1,2,4 "
                    f"--out {out} "
                    f"--out-md {report}"
                ),
            },
        ],
        "expected_outputs": [out, report],
    }


def _decoder_attention_kv_measured_l1_clustered_schedule_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    out = f"{base}/decoder_attention_kv_measured_l1_clustered_schedule__{item_id}.json"
    report = f"{base}/decoder_attention_kv_measured_l1_clustered_schedule__{item_id}.md"
    clustered_schedule = (
        f"{base}/decoder_attention_kv_clustered_schedule_overhead__"
        "l2_decoder_attention_kv_clustered_schedule_overhead_llama7b_v1.json"
    )
    measured_l1_costs = "runs/campaigns/npu/l1_measured_costs/llama7b_attention_local_costs_v1.json"
    return {
        "inputs": {
            "attention_kv_clustered_schedule_overhead": clustered_schedule,
            "attention_kv_measured_l1_clustered_schedule_out": out,
            "attention_kv_measured_l1_clustered_schedule_report": report,
            "attention_kv_measured_l1_costs": measured_l1_costs,
            "attention_kv_measured_l1_clustered_schedule_scope": (
                "Quality-backed native-GQA KV8 Llama7B 131k estimate that keeps measured "
                "compute-array PPA, explicit clustered reduction, and overhead sensitivity, "
                "then replaces the free local cluster datapath assumption with measured folded "
                "attention tile/reducer plus FIFO/router PPA anchors. This is still an L2 "
                "schedule model; it charges area, power, and clock for the measured L1 proxies "
                "without claiming full value-datapath RTL closure."
            ),
        },
        "commands": [
            {
                "name": "estimate_decoder_attention_kv_measured_l1_clustered_schedule",
                "run": (
                    "python3 npu/eval/estimate_llm_decoder_attention_kv_clustered_schedule.py "
                    "--repo-root . "
                    "--tag-substring compute_stability_cmp33 "
                    "--sequence-length-list 131072 "
                    "--die-area-mm2-list 200,400,800,1200 "
                    "--sram-area-fraction 0.4,0.6 "
                    "--logic-area-fraction 0.1,0.2 "
                    "--reserved-area-fraction 0.1 "
                    "--usable-sram-fraction 0.7 "
                    "--local-sram-fraction 0.1,0.25 "
                    "--tile-tokens-list 512 "
                    "--bank-count 16,64 "
                    "--cluster-count 1,2,4,8,16 "
                    "--noc-bandwidth-bytes-per-cycle 8192,32768 "
                    "--noc-hops 1,2,4 "
                    "--reduction-strategy owner_cluster,cluster_tree "
                    "--vector-ops-per-mac 0.125 "
                    "--reduction-scalar-bytes 2 "
                    "--command-cycles-per-tile 0,4 "
                    "--command-cycles-per-wave 0,16 "
                    "--reducer-setup-cycles 0,64 "
                    "--reduction-cycle-multiplier 1,2 "
                    f"--measured-l1-costs {measured_l1_costs} "
                    "--measured-l1-profile all "
                    f"--out {out} "
                    f"--out-md {report}"
                ),
            },
        ],
        "expected_outputs": [out, report],
    }


def _decoder_attention_kv_full_value_l1_clustered_schedule_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    out = f"{base}/decoder_attention_kv_full_value_l1_clustered_schedule__{item_id}.json"
    report = f"{base}/decoder_attention_kv_full_value_l1_clustered_schedule__{item_id}.md"
    clustered_schedule = (
        f"{base}/decoder_attention_kv_clustered_schedule_overhead__"
        "l2_decoder_attention_kv_clustered_schedule_overhead_llama7b_v1.json"
    )
    measured_l1_costs = "runs/campaigns/npu/l1_measured_costs/llama7b_attention_local_costs_full_value_v1.json"
    return {
        "inputs": {
            "attention_kv_clustered_schedule_overhead": clustered_schedule,
            "attention_kv_full_value_l1_clustered_schedule_out": out,
            "attention_kv_full_value_l1_clustered_schedule_report": report,
            "attention_kv_full_value_l1_costs": measured_l1_costs,
            "attention_kv_full_value_l1_clustered_schedule_scope": (
                "Quality-backed native-GQA KV8 Llama7B 131k estimate that keeps measured "
                "compute-array PPA, explicit clustered reduction, and overhead sensitivity, "
                "then replaces the folded local cluster datapath proxy with the measured "
                "full-value attention tile datapaths from the L1 closure run. This remains an "
                "L2 schedule model: it charges area, power, and clock for the full-value L1 "
                "anchors plus FIFO/router PPA, but does not yet model cycle-accurate SRAM, NoC "
                "arbitration, or full softmax-weight generation."
            ),
        },
        "commands": [
            {
                "name": "estimate_decoder_attention_kv_full_value_l1_clustered_schedule",
                "run": (
                    "python3 npu/eval/estimate_llm_decoder_attention_kv_clustered_schedule.py "
                    "--repo-root . "
                    "--tag-substring compute_stability_cmp33 "
                    "--sequence-length-list 131072 "
                    "--die-area-mm2-list 200,400,800,1200 "
                    "--sram-area-fraction 0.4,0.6 "
                    "--logic-area-fraction 0.1,0.2 "
                    "--reserved-area-fraction 0.1 "
                    "--usable-sram-fraction 0.7 "
                    "--local-sram-fraction 0.1,0.25 "
                    "--tile-tokens-list 512 "
                    "--bank-count 16,64 "
                    "--cluster-count 1,2,4,8,16 "
                    "--noc-bandwidth-bytes-per-cycle 8192,32768 "
                    "--noc-hops 1,2,4 "
                    "--reduction-strategy owner_cluster,cluster_tree "
                    "--vector-ops-per-mac 0.125 "
                    "--reduction-scalar-bytes 2 "
                    "--command-cycles-per-tile 0,4 "
                    "--command-cycles-per-wave 0,16 "
                    "--reducer-setup-cycles 0,64 "
                    "--reduction-cycle-multiplier 1,2 "
                    f"--measured-l1-costs {measured_l1_costs} "
                    "--measured-l1-profile all "
                    f"--out {out} "
                    f"--out-md {report}"
                ),
            },
        ],
        "expected_outputs": [out, report],
    }


def _decoder_attention_kv_all_measured_l1_clustered_schedule_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    out = f"{base}/decoder_attention_kv_all_measured_l1_clustered_schedule__{item_id}.json"
    report = f"{base}/decoder_attention_kv_all_measured_l1_clustered_schedule__{item_id}.md"
    clustered_schedule = (
        f"{base}/decoder_attention_kv_clustered_schedule_overhead__"
        "l2_decoder_attention_kv_clustered_schedule_overhead_llama7b_v1.json"
    )
    full_value_costs = "runs/campaigns/npu/l1_measured_costs/llama7b_attention_local_costs_full_value_v1.json"
    all_measured_costs = "runs/campaigns/npu/l1_measured_costs/llama7b_attention_local_costs_all_measured_v1.json"
    softmax_promotion = "control_plane/shadow_exports/l1_promotions/l1_decoder_attention_softmax_weight_generator_v1_r2.json"
    sram_profile = f"{base}/decoder_attention_sram_profile__l2_decoder_attention_sram_profile_v1.json"
    noc_profile = f"{base}/decoder_attention_noc_profile__l2_decoder_attention_noc_profile_v1.json"
    return {
        "inputs": {
            "attention_kv_clustered_schedule_overhead": clustered_schedule,
            "attention_kv_full_value_l1_costs": full_value_costs,
            "attention_kv_all_measured_l1_costs": all_measured_costs,
            "attention_softmax_weight_generator_promotion": softmax_promotion,
            "attention_sram_profile": sram_profile,
            "attention_noc_profile": noc_profile,
            "attention_kv_all_measured_l1_clustered_schedule_out": out,
            "attention_kv_all_measured_l1_clustered_schedule_report": report,
            "attention_kv_all_measured_l1_clustered_schedule_scope": (
                "Llama7B 131k native-GQA KV8 schedule ranking using measured compute-array PPA, "
                "full-value attention tile datapaths, exact-int softmax-weight generator PPA, "
                "and measured FIFO/router local NoC anchors. SRAM capacity/service and global "
                "NoC arbitration remain analytic L2 service terms, with the merged SRAM/NoC "
                "profile outputs recorded as calibration references."
            ),
        },
        "commands": [
            {
                "name": "estimate_decoder_attention_kv_all_measured_l1_clustered_schedule",
                "run": (
                    "python3 npu/eval/estimate_llm_decoder_attention_kv_clustered_schedule.py "
                    "--repo-root . "
                    "--tag-substring compute_stability_cmp33 "
                    "--sequence-length-list 131072 "
                    "--die-area-mm2-list 200,400,800,1200 "
                    "--sram-area-fraction 0.4,0.6 "
                    "--logic-area-fraction 0.1,0.2 "
                    "--reserved-area-fraction 0.1 "
                    "--usable-sram-fraction 0.7 "
                    "--local-sram-fraction 0.1,0.25 "
                    "--tile-tokens-list 512 "
                    "--bank-count 16,64 "
                    "--cluster-count 1,2,4,8,16 "
                    "--noc-bandwidth-bytes-per-cycle 8192,32768 "
                    "--noc-hops 1,2,4 "
                    "--reduction-strategy owner_cluster,cluster_tree "
                    "--vector-ops-per-mac 0.125 "
                    "--reduction-scalar-bytes 2 "
                    "--command-cycles-per-tile 0,4 "
                    "--command-cycles-per-wave 0,16 "
                    "--reducer-setup-cycles 0,64 "
                    "--reduction-cycle-multiplier 1,2 "
                    f"--measured-l1-costs {all_measured_costs} "
                    "--measured-l1-profile all "
                    f"--out {out} "
                    f"--out-md {report}"
                ),
            },
        ],
        "expected_outputs": [out, report],
    }


def _decoder_attention_kv_dense_tile_all_measured_l1_clustered_schedule_evidence(
    *,
    item_id: str,
) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    out = f"{base}/decoder_attention_kv_dense_tile_all_measured_l1_clustered_schedule__{item_id}.json"
    report = f"{base}/decoder_attention_kv_dense_tile_all_measured_l1_clustered_schedule__{item_id}.md"
    dense_compute = (
        f"{base}/decoder_attention_kv_dense_tile_measured_compute__"
        "l2_decoder_attention_kv_dense_tile_measured_compute_llama7b_v1.json"
    )
    full_value_costs = "runs/campaigns/npu/l1_measured_costs/llama7b_attention_local_costs_full_value_v1.json"
    all_measured_costs = "runs/campaigns/npu/l1_measured_costs/llama7b_attention_local_costs_all_measured_v1.json"
    softmax_promotion = "control_plane/shadow_exports/l1_promotions/l1_decoder_attention_softmax_weight_generator_v1_r2.json"
    sram_profile = f"{base}/decoder_attention_sram_profile__l2_decoder_attention_sram_profile_v1.json"
    noc_profile = f"{base}/decoder_attention_noc_profile__l2_decoder_attention_noc_profile_v1.json"
    return {
        "inputs": {
            "attention_kv_dense_tile_measured_compute": dense_compute,
            "attention_kv_full_value_l1_costs": full_value_costs,
            "attention_kv_all_measured_l1_costs": all_measured_costs,
            "attention_softmax_weight_generator_promotion": softmax_promotion,
            "attention_sram_profile": sram_profile,
            "attention_noc_profile": noc_profile,
            "attention_kv_dense_tile_all_measured_l1_clustered_schedule_out": out,
            "attention_kv_dense_tile_all_measured_l1_clustered_schedule_report": report,
            "attention_kv_dense_tile_all_measured_l1_clustered_schedule_scope": (
                "Llama7B 131k native-GQA KV8 schedule ranking using measured dense GEMM tile "
                "compute PPA, full-value attention tile datapaths, exact-int softmax-weight "
                "generator PPA, and measured FIFO/router local NoC anchors. SRAM capacity/"
                "service and global NoC arbitration remain analytic L2 service terms, with "
                "the merged SRAM/NoC profile outputs recorded as calibration references."
            ),
        },
        "commands": [
            {
                "name": "estimate_decoder_attention_kv_dense_tile_all_measured_l1_clustered_schedule",
                "run": (
                    "python3 npu/eval/estimate_llm_decoder_attention_kv_clustered_schedule.py "
                    "--repo-root . "
                    "--compute-source dense_gemm_tile "
                    "--tag-substring npu_dense_gemm_tile_v2_scale_hier "
                    "--sequence-length-list 131072 "
                    "--die-area-mm2-list 200,400,800,1200 "
                    "--sram-area-fraction 0.4,0.6 "
                    "--logic-area-fraction 0.1,0.2,0.4 "
                    "--reserved-area-fraction 0.1 "
                    "--usable-sram-fraction 0.7 "
                    "--local-sram-fraction 0.1,0.25 "
                    "--tile-tokens-list 512 "
                    "--bank-count 16,64 "
                    "--cluster-count 1,2,4,8,16 "
                    "--noc-bandwidth-bytes-per-cycle 8192,32768 "
                    "--noc-hops 1,2,4 "
                    "--reduction-strategy owner_cluster,cluster_tree "
                    "--vector-ops-per-mac 0.125 "
                    "--reduction-scalar-bytes 2 "
                    "--command-cycles-per-tile 0,4 "
                    "--command-cycles-per-wave 0,16 "
                    "--reducer-setup-cycles 0,64 "
                    "--reduction-cycle-multiplier 1,2 "
                    f"--measured-l1-costs {all_measured_costs} "
                    "--measured-l1-profile all "
                    f"--out {out} "
                    f"--out-md {report}"
                ),
            },
        ],
        "expected_outputs": [out, report],
    }


def _decoder_attention_kv_dense_tile_reduction_noc_frontier_evidence(
    *,
    item_id: str,
) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    out = f"{base}/decoder_attention_kv_dense_tile_reduction_noc_frontier__{item_id}.json"
    report = f"{base}/decoder_attention_kv_dense_tile_reduction_noc_frontier__{item_id}.md"
    dense_clustered = (
        f"{base}/decoder_attention_kv_dense_tile_all_measured_l1_clustered_schedule__"
        "l2_decoder_attention_kv_dense_tile_all_measured_l1_clustered_schedule_llama7b_v1.json"
    )
    all_measured_costs = "runs/campaigns/npu/l1_measured_costs/llama7b_attention_local_costs_all_measured_v1.json"
    sram_profile = f"{base}/decoder_attention_sram_profile__l2_decoder_attention_sram_profile_v1.json"
    noc_profile = f"{base}/decoder_attention_noc_profile__l2_decoder_attention_noc_profile_v1.json"
    return {
        "inputs": {
            "attention_kv_dense_tile_all_measured_l1_clustered_schedule": dense_clustered,
            "attention_kv_all_measured_l1_costs": all_measured_costs,
            "attention_sram_profile": sram_profile,
            "attention_noc_profile": noc_profile,
            "attention_kv_dense_tile_reduction_noc_frontier_out": out,
            "attention_kv_dense_tile_reduction_noc_frontier_report": report,
            "attention_kv_dense_tile_reduction_noc_frontier_scope": (
                "Focused Llama7B 131k native-GQA KV8 frontier around the selected "
                "dense_gemm_16x8_k1_p1 compute anchor. The sweep spends its row budget on "
                "local/shared SRAM placement, NoC bandwidth and hop sensitivity, cluster "
                "count, command overhead, and cross-tile reduction overhead to identify "
                "whether the next detailed closure should prioritize global NoC, reduction "
                "hierarchy, or SRAM placement."
            ),
        },
        "commands": [
            {
                "name": "estimate_decoder_attention_kv_dense_tile_reduction_noc_frontier",
                "run": (
                    "python3 npu/eval/estimate_llm_decoder_attention_kv_clustered_schedule.py "
                    "--repo-root . "
                    "--compute-source dense_gemm_tile "
                    "--compute-arch-list dense_gemm_16x8_k1_p1 "
                    "--tag-substring npu_dense_gemm_tile_v2_scale_hier "
                    "--sequence-length-list 131072 "
                    "--die-area-mm2-list 800,1200 "
                    "--sram-area-fraction 0.35,0.4,0.5,0.6 "
                    "--logic-area-fraction 0.3,0.4,0.5 "
                    "--reserved-area-fraction 0.1 "
                    "--usable-sram-fraction 0.7 "
                    "--local-sram-fraction 0.05,0.1,0.25,0.5 "
                    "--tile-tokens-list 512,1024 "
                    "--bank-count 16,64,128 "
                    "--cluster-count 1,2,4,8,16,32 "
                    "--noc-bandwidth-bytes-per-cycle 4096,8192,16384,32768,65536 "
                    "--noc-hops 1,2,4,8 "
                    "--reduction-strategy centralized_tile,owner_cluster,cluster_tree "
                    "--vector-ops-per-mac 0.125 "
                    "--reduction-scalar-bytes 2 "
                    "--command-cycles-per-tile 0,4,16 "
                    "--command-cycles-per-wave 0,16,64 "
                    "--reducer-setup-cycles 0,64,256 "
                    "--reduction-cycle-multiplier 1,2,4 "
                    f"--measured-l1-costs {all_measured_costs} "
                    "--measured-l1-profile hd64_kv8_full_value_p8_ppc2_noc128_softmax_int8_q10 "
                    f"--out {out} "
                    f"--out-md {report}"
                ),
            },
        ],
        "expected_outputs": [out, report],
    }


def _decoder_attention_kv_dense_tile_topology_scheduler_pairs_evidence(
    *,
    item_id: str,
) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    out = f"{base}/decoder_attention_kv_dense_tile_topology_scheduler_pairs__{item_id}.json"
    report = f"{base}/decoder_attention_kv_dense_tile_topology_scheduler_pairs__{item_id}.md"
    reduction_noc_frontier = (
        f"{base}/decoder_attention_kv_dense_tile_reduction_noc_frontier__"
        "l2_decoder_attention_kv_dense_tile_reduction_noc_frontier_llama7b_v1.json"
    )
    return {
        "inputs": {
            "attention_kv_dense_tile_reduction_noc_frontier": reduction_noc_frontier,
            "attention_kv_dense_tile_topology_scheduler_pairs_out": out,
            "attention_kv_dense_tile_topology_scheduler_pairs_report": report,
            "attention_kv_dense_tile_topology_scheduler_pairs_scope": (
                "Validate logically compatible NoC topology, scheduler, reducer, bank-placement, "
                "link-width, and virtual-channel pairs for the Llama7B dense-tile attention "
                "frontier. This replaces independent bandwidth/hop/reduction sweeps with "
                "topology-derived service envelopes and explicit invalid-pair reasons before "
                "the next scheduler/performance run."
            ),
        },
        "commands": [
            {
                "name": "estimate_decoder_attention_kv_dense_tile_topology_scheduler_pairs",
                "run": (
                    "python3 npu/eval/estimate_llm_decoder_attention_kv_topology_scheduler_pairs.py "
                    "--repo-root . "
                    f"--frontier-json {reduction_noc_frontier} "
                    "--cluster-count-list 4,8,16 "
                    "--topology-list cluster_tree,mesh2d,ring,crossbar "
                    "--scheduler-policy-list static_wave,locality_aware,bank_aware_prefetch,"
                    "tree_reduction_aware,double_buffered_overlap "
                    "--reduction-strategy-list centralized_tile,owner_cluster,cluster_tree "
                    "--bank-placement-list per_cluster_local,grouped_shared,distributed_shared "
                    "--bank-count-list 16,64,128 "
                    "--link-width-bits-list 256,512,1024,2048 "
                    "--virtual-channel-list 1,2,4 "
                    "--local-sram-fraction-list 0.05,0.1,0.25 "
                    f"--out {out} "
                    f"--out-md {report}"
                ),
            },
        ],
        "expected_outputs": [out, report],
    }


def _decoder_attention_kv_dense_tile_topology_derived_schedule_evidence(
    *,
    item_id: str,
) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    out = f"{base}/decoder_attention_kv_dense_tile_topology_derived_schedule__{item_id}.json"
    report = f"{base}/decoder_attention_kv_dense_tile_topology_derived_schedule__{item_id}.md"
    topology_pairs = (
        f"{base}/decoder_attention_kv_dense_tile_topology_scheduler_pairs__"
        "l2_decoder_attention_kv_dense_tile_topology_scheduler_pairs_llama7b_v1_r2.json"
    )
    all_measured_costs = "runs/campaigns/npu/l1_measured_costs/llama7b_attention_local_costs_all_measured_v1.json"
    return {
        "inputs": {
            "attention_kv_dense_tile_topology_scheduler_pairs": topology_pairs,
            "attention_kv_all_measured_l1_costs": all_measured_costs,
            "attention_kv_dense_tile_topology_derived_schedule_out": out,
            "attention_kv_dense_tile_topology_derived_schedule_report": report,
            "attention_kv_dense_tile_topology_derived_schedule_scope": (
                "Rerun the Llama7B dense-tile clustered schedule using only topology-derived "
                "NoC service rows from the valid topology/scheduler pair matrix. This couples "
                "cluster count, bank count, local SRAM fraction, reduction strategy, link width, "
                "and hop latency instead of sweeping independent abstract NoC bandwidth/hops."
            ),
        },
        "commands": [
            {
                "name": "estimate_decoder_attention_kv_dense_tile_topology_derived_schedule",
                "run": (
                    "python3 npu/eval/estimate_llm_decoder_attention_kv_topology_derived_schedule.py "
                    "--repo-root . "
                    f"--topology-pairs-json {topology_pairs} "
                    "--compute-source dense_gemm_tile "
                    "--compute-arch-list dense_gemm_16x8_k1_p1 "
                    "--tag-substring npu_dense_gemm_tile_v2_scale_hier "
                    "--sequence-length-list 131072 "
                    "--die-area-mm2-list 800,1200 "
                    "--sram-area-fraction 0.35,0.4,0.5,0.6 "
                    "--logic-area-fraction 0.3,0.4,0.5 "
                    "--reserved-area-fraction 0.1 "
                    "--usable-sram-fraction 0.7 "
                    "--tile-tokens-list 512,1024 "
                    "--topology-row-limit 128 "
                    "--vector-ops-per-mac 0.125 "
                    "--reduction-scalar-bytes 2 "
                    "--command-cycles-per-tile 0,4,16 "
                    "--command-cycles-per-wave 0,16,64 "
                    "--reducer-setup-cycles 0,64,256 "
                    "--reduction-cycle-multiplier 1,2,4 "
                    f"--measured-l1-costs {all_measured_costs} "
                    "--measured-l1-profile hd64_kv8_full_value_p8_ppc2_noc128_softmax_int8_q10 "
                    f"--out {out} "
                    f"--out-md {report}"
                ),
            },
        ],
        "expected_outputs": [out, report],
    }


def _decoder_attention_kv_sram_noc_constrained_schedule_evidence(
    *,
    item_id: str,
) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    out = f"{base}/decoder_attention_kv_sram_noc_constrained_schedule__{item_id}.json"
    report = f"{base}/decoder_attention_kv_sram_noc_constrained_schedule__{item_id}.md"
    topology_derived = (
        f"{base}/decoder_attention_kv_dense_tile_topology_derived_schedule__"
        "l2_decoder_attention_kv_dense_tile_topology_derived_schedule_llama7b_v1.json"
    )
    sram_profile = f"{base}/decoder_attention_sram_profile__l2_decoder_attention_sram_profile_v1.json"
    return {
        "inputs": {
            "attention_kv_dense_tile_topology_derived_schedule": topology_derived,
            "attention_sram_profile": sram_profile,
            "attention_kv_sram_noc_constrained_schedule_out": out,
            "attention_kv_sram_noc_constrained_schedule_report": report,
            "attention_kv_sram_noc_constrained_schedule_scope": (
                "Apply practical local SRAM tile-buffer capacity, 256-bit SRAM-bank read service, "
                "and endpoint injection/ejection caps to retained Llama7B topology-derived dense-tile "
                "schedule frontier rows. This corrects the optimistic abstract SRAM-bank bandwidth "
                "without reintroducing independent NoC bandwidth/hop sweeps."
            ),
        },
        "commands": [
            {
                "name": "estimate_decoder_attention_kv_sram_noc_constrained_schedule",
                "run": (
                    "python3 npu/eval/estimate_llm_decoder_attention_kv_sram_noc_constrained_schedule.py "
                    "--repo-root . "
                    f"--topology-derived-json {topology_derived} "
                    f"--sram-profile-json {sram_profile} "
                    "--frontier-row-limit 256 "
                    "--sram-bank-port-bytes-per-cycle 32 "
                    "--sram-read-ports-per-bank 1 "
                    "--sram-bank-efficiency 0.70,0.85 "
                    "--endpoint-port-bytes-per-cycle 32,64,128 "
                    "--endpoint-ports-per-cluster 1,2 "
                    "--endpoint-efficiency 0.70,0.85 "
                    "--local-buffer-multiplier 1,2 "
                    f"--out {out} "
                    f"--out-md {report}"
                ),
            },
        ],
        "expected_outputs": [out, report],
    }


def _decoder_attention_sram_profile_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    out = f"{base}/decoder_attention_sram_profile__{item_id}.json"
    report = f"{base}/decoder_attention_sram_profile__{item_id}.md"
    arch = f"runs/designs/sram/llama7b_attention_tile_buffers_v1/arch.yml"
    sram_metrics = "runs/designs/sram/llama7b_attention_tile_buffers_v1/sram_metrics.json"
    sram_summary = "runs/designs/sram/llama7b_attention_tile_buffers_v1/sram_metrics_summary.json"
    return {
        "inputs": {
            "attention_sram_profile_out": out,
            "attention_sram_profile_report": report,
            "attention_sram_profile_arch": arch,
            "attention_sram_metrics_json": sram_metrics,
            "attention_sram_metrics_summary_json": sram_summary,
            "attention_sram_profile_scope": (
                "Measure the selected Llama7B 131k tile-local attention SRAM quantities for "
                "score buffering, softmax weights, staged K/V reads, partial-value buffering, "
                "and result writeback. This closes tile-local SRAM access/energy inputs for "
                "the clustered schedule; full KV-cache capacity placement and NoC contention "
                "remain separate closure items."
            ),
        },
        "commands": [
            {
                "name": "measure_decoder_attention_sram_profile",
                "run": (
                    "python3 npu/eval/measure_llm_decoder_attention_sram_profile.py "
                    f"--out {out} "
                    f"--report {report} "
                    f"--arch-out {arch} "
                    "--sram-id llama7b_attention_tile_buffers_v1 "
                    "--run-cacti"
                ),
            },
        ],
        "expected_outputs": [out, report, arch, sram_metrics, sram_summary],
    }


def _decoder_attention_noc_profile_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    out = f"{base}/decoder_attention_noc_profile__{item_id}.json"
    report = f"{base}/decoder_attention_noc_profile__{item_id}.md"
    primitive_profile = "control_plane/shadow_exports/l1_promotions/l1_decoder_memory_noc_primitives_v1.json"
    return {
        "inputs": {
            "attention_noc_profile_out": out,
            "attention_noc_profile_report": report,
            "attention_noc_primitive_profile": primitive_profile,
            "attention_noc_profile_scope": (
                "Quantify selected Llama7B attention NoC traffic for shared tile reads, "
                "cross-tile reduction, and KV writeback using measured FIFO/router PPA "
                "anchors plus explicit flit width, hop, virtual-channel, and arbitration "
                "efficiency bounds. This closes the hidden bandwidth/hop proxy terms for "
                "the final schedule, while leaving full routed NoC RTL as a named residual."
            ),
        },
        "commands": [
            {
                "name": "measure_decoder_attention_noc_profile",
                "run": (
                    "python3 npu/eval/measure_llm_decoder_attention_noc_profile.py "
                    "--repo-root . "
                    f"--out {out} "
                    f"--report {report}"
                ),
            },
        ],
        "expected_outputs": [out, report],
    }


def _decoder_attention_kv_quality_gate_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    out = f"{base}/decoder_attention_kv_quality_gate__{item_id}.json"
    report = f"{base}/decoder_attention_kv_quality_gate__{item_id}.md"
    physical_frontier = (
        f"{base}/decoder_attention_kv_physical_hbm_frontier__"
        "l2_decoder_attention_kv_physical_hbm_frontier_llama7b_v1.json"
    )
    return {
        "inputs": {
            "attention_kv_memory_out": out,
            "attention_kv_memory_report": report,
            "attention_kv_physical_hbm_frontier": physical_frontier,
            "attention_kv_quality_gate_scope": (
                "Quality-risk gate for structural KV reductions identified by the physical-HBM "
                "frontier. Treat MQA and KV4 hardware wins as non-deployable until model-quality "
                "or retraining evidence exists, and select practical GQA/KV candidates for follow-up."
            ),
        },
        "commands": [
            {
                "name": "estimate_decoder_attention_kv_quality_gate",
                "run": (
                    "python3 npu/eval/estimate_llm_decoder_attention_kv_quality_gate.py "
                    f"--physical-hbm-frontier {physical_frontier} "
                    "--sequence-length-list 131072 "
                    "--die-area-mm2-list 100,200,400 "
                    f"--out {out} "
                    f"--out-md {report}"
                ),
            },
        ],
        "expected_outputs": [out, report],
    }


def _decoder_attention_kv_quality_proxy_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    out = f"{base}/decoder_attention_kv_quality_proxy__{item_id}.json"
    report = f"{base}/decoder_attention_kv_quality_proxy__{item_id}.md"
    quality_gate = f"{base}/decoder_attention_kv_quality_gate__l2_decoder_attention_kv_quality_gate_llama7b_v1.json"
    return {
        "inputs": {
            "attention_kv_memory_out": out,
            "attention_kv_memory_report": report,
            "attention_kv_quality_gate": quality_gate,
            "attention_kv_quality_proxy_scope": (
                "Controlled attention proxy for GQA/MQA head sharing and packed KV quantization. "
                "Compare attention top-1, retrieval hit, distribution KL, and value-output cosine "
                "against an MHA/KV16 reference on correlated, retrieval, low-margin, and independent-head regimes."
            ),
        },
        "commands": [
            {
                "name": "estimate_decoder_attention_kv_quality_proxy",
                "run": (
                    "python3 npu/eval/estimate_llm_decoder_attention_kv_quality_proxy.py "
                    f"--quality-gate {quality_gate} "
                    "--attention-heads 32 "
                    "--head-dim 32 "
                    "--sequence-length-list 128,512 "
                    "--regime-list correlated_heads,retrieval,low_margin,independent_heads "
                    "--seed-count 2 "
                    "--candidate-spec-list mha:kv8,mha:kv4,gqa8:kv8,gqa8:kv4,mqa:kv4 "
                    f"--out {out} "
                    f"--out-md {report}"
                ),
            },
        ],
        "expected_outputs": [out, report],
    }


def _decoder_attention_kv_native_gqa_proxy_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    out = f"{base}/decoder_attention_kv_native_gqa_proxy__{item_id}.json"
    report = f"{base}/decoder_attention_kv_native_gqa_proxy__{item_id}.md"
    quality_proxy = f"{base}/decoder_attention_kv_quality_proxy__l2_decoder_attention_kv_quality_proxy_llama7b_v1.json"
    return {
        "inputs": {
            "attention_kv_memory_out": out,
            "attention_kv_memory_report": report,
            "attention_kv_quality_proxy": quality_proxy,
            "attention_kv_native_gqa_proxy_scope": (
                "Native same-sharing attention/KV quality proxy for GQA8/MQA with KV8 and KV4. "
                "Compare each candidate against a same-sharing KV16 reference, so GQA is not penalized "
                "for differing from post-hoc MHA head sharing."
            ),
        },
        "commands": [
            {
                "name": "estimate_decoder_attention_kv_native_gqa_proxy",
                "run": (
                    "python3 npu/eval/estimate_llm_decoder_attention_kv_native_gqa_proxy.py "
                    f"--quality-proxy {quality_proxy} "
                    "--attention-heads 32 "
                    "--head-dim 32 "
                    "--sequence-length-list 128,512 "
                    "--regime-list native_correlated_queries,native_retrieval,native_low_margin "
                    "--seed-count 2 "
                    "--candidate-spec-list gqa8:kv8,gqa8:kv4,mqa:kv8,mqa:kv4 "
                    f"--out {out} "
                    f"--out-md {report}"
                ),
            },
        ],
        "expected_outputs": [out, report],
    }


def _decoder_attention_kv_trace_calibration_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    out = f"{base}/decoder_attention_kv_trace_calibration__{item_id}.json"
    report = f"{base}/decoder_attention_kv_trace_calibration__{item_id}.md"
    native_gqa = f"{base}/decoder_attention_kv_native_gqa_proxy__l2_decoder_attention_kv_native_gqa_proxy_llama7b_v1.json"
    gpt2_quality = f"{base}/decoder_quality_compare__l2_decoder_gpt2_prompt_stress_v1.json"
    distil_quality = (
        "runs/datasets/llm_decoder_eval_distilgpt2_prompt_stress_v1/"
        "decoder_quality_compare__l2_decoder_distilgpt2_prompt_stress_v1.json"
    )
    return {
        "inputs": {
            "attention_kv_memory_out": out,
            "attention_kv_memory_report": report,
            "attention_kv_native_gqa_proxy": native_gqa,
            "gpt2_prompt_stress_quality_compare": gpt2_quality,
            "distilgpt2_prompt_stress_quality_compare": distil_quality,
            "attention_kv_trace_calibration_scope": (
                "Calibrate the native GQA8/KV4 proxy with real GPT-2-family prompt-stress KV trace "
                "statistics. This is a scheduling gate for a model-native or QAT GQA run, not a "
                "native-GQA quality claim."
            ),
        },
        "commands": [
            {
                "name": "estimate_decoder_attention_kv_trace_calibration",
                "run": (
                    "python3 npu/eval/estimate_llm_decoder_attention_kv_trace_calibration.py "
                    f"--native-gqa-proxy {native_gqa} "
                    f"--quality-compare gpt2_prompt_stress={gpt2_quality} "
                    f"--quality-compare distilgpt2_prompt_stress={distil_quality} "
                    f"--out {out} "
                    f"--out-md {report}"
                ),
            },
        ],
        "expected_outputs": [out, report],
    }


def _decoder_attention_kv_model_native_quality_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    out = f"{base}/decoder_attention_kv_model_native_quality__{item_id}.json"
    report = f"{base}/decoder_attention_kv_model_native_quality__{item_id}.md"
    trace_calibration = f"{base}/decoder_attention_kv_trace_calibration__l2_decoder_attention_kv_trace_calibration_v1.json"
    return {
        "inputs": {
            "attention_kv_memory_out": out,
            "attention_kv_memory_report": report,
            "attention_kv_trace_calibration": trace_calibration,
            "attention_kv_model_native_quality_scope": (
                "Run a trained native-GQA checkpoint through teacher-forced decode while feeding back "
                "KV8/KV4-quantized past_key_values. This is the first real-checkpoint quality gate after "
                "the synthetic native-GQA proxy and GPT-2-family trace calibration; it is not QAT."
            ),
        },
        "commands": [
            {
                "name": "evaluate_decoder_attention_kv_model_native_quality",
                "run": (
                    "bash npu/eval/run_hf_eval_python.sh "
                    "npu/eval/evaluate_llm_decoder_model_native_kv_quant.py "
                    "--expected-gqa-group-size 8 "
                    "--kv-bits-list 8,4 "
                    "--max-prompts 8 "
                    "--generation-steps 8 "
                    "--topk 5 "
                    f"--out {out} "
                    f"--out-md {report}"
                ),
            },
        ],
        "expected_outputs": [out, report],
    }


def _decoder_attention_kv_model_native_recovery_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    out = f"{base}/decoder_attention_kv_model_native_recovery__{item_id}.json"
    report = f"{base}/decoder_attention_kv_model_native_recovery__{item_id}.md"
    native_quality = (
        f"{base}/decoder_attention_kv_model_native_quality__"
        "l2_decoder_attention_kv_model_native_quality_tinyllama_v1_r2.json"
    )
    return {
        "inputs": {
            "attention_kv_memory_out": out,
            "attention_kv_memory_report": report,
            "attention_kv_model_native_quality": native_quality,
            "attention_kv_model_native_recovery_scope": (
                "Sweep KV4 quantization scale granularity on the same trained native-GQA checkpoint. "
                "This is a recovery screen before full QAT: tensor-scale failure is already known; "
                "per-KV-head or per-token-vector recovery would move the next question to hardware scale metadata cost."
            ),
        },
        "commands": [
            {
                "name": "evaluate_decoder_attention_kv_model_native_recovery",
                "run": (
                    "bash npu/eval/run_hf_eval_python.sh "
                    "npu/eval/evaluate_llm_decoder_model_native_kv_quant.py "
                    "--expected-gqa-group-size 8 "
                    "--kv-bits-list 4 "
                    "--kv-granularity-list tensor,kv_head,token_vector "
                    "--max-prompts 8 "
                    "--generation-steps 8 "
                    "--topk 5 "
                    f"--out {out} "
                    f"--out-md {report}"
                ),
            },
        ],
        "expected_outputs": [out, report],
    }


def _decoder_output_projection_weight_store_feasibility_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    out = f"{base}/decoder_output_projection_weight_store_feasibility__{item_id}.json"
    report = f"{base}/decoder_output_projection_weight_store_feasibility__{item_id}.md"
    memory_hierarchy = (
        f"{base}/decoder_output_projection_producer_memory_hierarchy__"
        "l2_decoder_output_projection_producer_memory_hierarchy_v1.json"
    )
    return {
        "inputs": {
            "weight_store_feasibility_out": out,
            "weight_store_feasibility_report": report,
            "producer_memory_hierarchy": memory_hierarchy,
            "weight_store_feasibility_scope": (
                "Convert the resident output-projection producer weight requirement into a bounded "
                "banking, bandwidth, read-width, and proxy storage-area envelope before queueing "
                "a routed weight-store interface wrapper."
            ),
        },
        "commands": [
            {
                "name": "estimate_decoder_output_projection_weight_store_feasibility",
                "run": (
                    "python3 npu/eval/estimate_llm_decoder_output_projection_weight_store_feasibility.py "
                    f"--memory-hierarchy {memory_hierarchy} "
                    "--bank-capacity-mb-list 0.5,1,2,4,8 "
                    "--bank-read-width-bits-list 256,512,1024,2048 "
                    "--read-ports-per-bank-list 1,2 "
                    "--area-budget-mm2-list 25,100,400 "
                    f"--out {out} "
                    f"--out-md {report}"
                ),
            },
        ],
        "expected_outputs": [out, report],
    }


def _decoder_output_projection_weight_store_interface_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    out = f"{base}/decoder_output_projection_weight_store_interface__{item_id}.json"
    report = f"{base}/decoder_output_projection_weight_store_interface__{item_id}.md"
    feasibility = (
        f"{base}/decoder_output_projection_weight_store_feasibility__"
        "l2_decoder_output_projection_weight_store_feasibility_v1.json"
    )
    return {
        "inputs": {
            "weight_store_interface_out": out,
            "weight_store_interface_report": report,
            "weight_store_feasibility": feasibility,
            "weight_store_interface_scope": (
                "Check a bounded RTL/perf-sim contract for the sharded ready/valid "
                "weight-store read interface selected by the resident output-projection "
                "weight-store feasibility model. This intentionally scales down bank count "
                "for RTL simulation; full storage capacity and area remain proxy-modeled."
            ),
        },
        "commands": [
            {
                "name": "probe_decoder_output_projection_weight_store_interface",
                "run": (
                    "python3 npu/eval/probe_llm_decoder_output_projection_weight_store_interface.py "
                    f"--weight-store-feasibility {feasibility} "
                    "--max-representative-banks 64 "
                    "--read-latency-cycles-list 1,2,4,8 "
                    "--request-count 16 "
                    "--address-stride 5 "
                    f"--out {out} "
                    f"--out-md {report}"
                ),
            },
        ],
        "expected_outputs": [out, report],
    }


def _decoder_output_projection_weight_fetch_wrapper_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    out = f"{base}/decoder_output_projection_weight_fetch_wrapper__{item_id}.json"
    report = f"{base}/decoder_output_projection_weight_fetch_wrapper__{item_id}.md"
    feasibility = (
        f"{base}/decoder_output_projection_weight_store_feasibility__"
        "l2_decoder_output_projection_weight_store_feasibility_v1.json"
    )
    interface = (
        f"{base}/decoder_output_projection_weight_store_interface__"
        "l2_decoder_output_projection_weight_store_interface_v1_r2.json"
    )
    return {
        "inputs": {
            "weight_fetch_wrapper_out": out,
            "weight_fetch_wrapper_report": report,
            "weight_store_feasibility": feasibility,
            "weight_store_interface": interface,
            "weight_fetch_wrapper_scope": (
                "Check producer-side tile request cadence, outstanding request throttling, "
                "full-bank request masks, and response ordering against a cycle-level perf model. "
                "This is a control-contract RTL simulation; full resident storage remains modeled "
                "by the weight-store feasibility artifact."
            ),
        },
        "commands": [
            {
                "name": "probe_decoder_output_projection_weight_fetch_wrapper",
                "run": (
                    "python3 npu/eval/probe_llm_decoder_output_projection_weight_fetch_wrapper.py "
                    f"--weight-store-feasibility {feasibility} "
                    "--read-latency-cycles-list 1,4,8 "
                    "--outstanding-depth-list 1,4 "
                    "--request-count 12 "
                    "--address-stride 5 "
                    f"--out {out} "
                    f"--out-md {report}"
                ),
            },
        ],
        "expected_outputs": [out, report],
    }


def _decoder_producer_ranker_memory_integration_plan_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    out = f"{base}/decoder_producer_ranker_memory_integration_plan__{item_id}.json"
    report = f"{base}/decoder_producer_ranker_memory_integration_plan__{item_id}.md"
    frontier = (
        f"{base}/decoder_frontier_synthesis__"
        "l2_decoder_frontier_synthesis_nm16_physical_v1.json"
    )
    producer_ranker = (
        f"{base}/decoder_producer_ranker_coupled_noc__"
        "l2_decoder_frontier_synthesis_nm16_physical_v1.json"
    )
    producer_physical = (
        f"{base}/decoder_output_projection_producer_pnr_feasibility__"
        "l2_decoder_output_projection_producer_pnr_nm16_v1.json"
    )
    producer_config = "runs/designs/npu_blocks/npu_fp16_cpp_nm16_producer/config_nm16_producer.json"
    stream_contract = "npu/docs/decoder_logit_rank_streaming_hierarchy.md"
    return {
        "inputs": {
            "integration_plan_out": out,
            "integration_plan_report": report,
            "frontier_synthesis": frontier,
            "producer_ranker_coupled": producer_ranker,
            "producer_physical_boundary": producer_physical,
            "producer_config": producer_config,
            "stream_contract": stream_contract,
            "integration_plan_scope": (
                "Reconcile the nm16 measured producer MAC lanes with the W64/W128 "
                "producer/ranker frontier, shared memory assumptions, and ready-valid "
                "stream equivalence requirements before queueing an integrated RTL macro."
            ),
        },
        "commands": [
            {
                "name": "plan_decoder_producer_ranker_memory_integration",
                "run": (
                    "python3 npu/eval/plan_llm_decoder_producer_ranker_memory_integration.py "
                    f"--frontier-synthesis {frontier} "
                    f"--producer-ranker-coupled {producer_ranker} "
                    f"--producer-physical-boundary {producer_physical} "
                    f"--producer-config {producer_config} "
                    f"--stream-contract {stream_contract} "
                    f"--out {out} "
                    f"--out-md {report}"
                ),
            },
        ],
        "expected_outputs": [out, report],
    }


def _decoder_producer_ranker_ready_valid_equivalence_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    out = f"{base}/decoder_producer_ranker_ready_valid_equivalence__{item_id}.json"
    report = f"{base}/decoder_producer_ranker_ready_valid_equivalence__{item_id}.md"
    producer_config = "runs/designs/npu_blocks/npu_fp16_cpp_nm16_producer/config_nm16_producer.json"
    logit_rank_config = "runs/designs/activations/logit_rank_r64_l16_k1_wrapper/config_logit_rank_r64_l16_k1.json"
    merge_config = (
        "runs/designs/activations/candidate_stream_merge_fifo_k1_l16_t16_d16_wrapper/"
        "config_candidate_stream_merge_fifo_k1_l16_t16_d16.json"
    )
    integration_plan = (
        f"{base}/decoder_producer_ranker_memory_integration_plan__"
        "l2_decoder_producer_ranker_memory_integration_plan_v1_r2.json"
    )
    return {
        "inputs": {
            "ready_valid_equivalence_out": out,
            "ready_valid_equivalence_report": report,
            "producer_config": producer_config,
            "logit_rank_config": logit_rank_config,
            "candidate_merge_config": merge_config,
            "integration_plan": integration_plan,
            "ready_valid_equivalence_scope": (
                "Run a deterministic RTL ready-valid harness for the first r64/k1 "
                "producer-to-ranker integration target. The harness ties generated "
                "logit_rank_r64_l16_k1 to candidate_stream_merge_fifo_k1_l16_t16_d16, "
                "checks lower-token tie order, accepted beat count, FIFO observables, "
                "and final last-beat completion against a full-vocabulary reference."
            ),
        },
        "commands": [
            {
                "name": "build_generator",
                "run": "export PATH=/oss-cad-suite/bin:$PATH && cmake -S . -B build && cmake --build build --target rtlgen",
            },
            {
                "name": "probe_decoder_producer_ranker_ready_valid_equivalence",
                "run": (
                    "python3 npu/eval/probe_llm_decoder_producer_ranker_ready_valid_equivalence.py "
                    f"--producer-config {producer_config} "
                    f"--logit-rank-config {logit_rank_config} "
                    f"--merge-config {merge_config} "
                    f"--integration-plan {integration_plan} "
                    "--run-rtl-sim "
                    f"--out {out} "
                    f"--out-md {report}"
                ),
            },
        ],
        "expected_outputs": [out, report],
    }


def _decoder_producer_ranker_physical_wrapper_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    out = f"{base}/decoder_producer_ranker_physical_wrapper__{item_id}.json"
    report = f"{base}/decoder_producer_ranker_physical_wrapper__{item_id}.md"
    design_dir = "runs/designs/activations/decoder_r64_k1_producer_ranker_physical_wrapper"
    logit_rank_config = "runs/designs/activations/logit_rank_r64_l16_k1_wrapper/config_logit_rank_r64_l16_k1.json"
    merge_config = (
        "runs/designs/activations/candidate_stream_merge_fifo_k1_l16_t16_d16_wrapper/"
        "config_candidate_stream_merge_fifo_k1_l16_t16_d16.json"
    )
    ready_valid_equivalence = (
        f"{base}/decoder_producer_ranker_ready_valid_equivalence__"
        "l2_decoder_producer_ranker_ready_valid_equivalence_v1_r2.json"
    )
    sweep = "runs/campaigns/npu/decoder_producer_ranker_physical_wrapper/sweeps/nangate45_r64_k1_macro.json"
    top = "decoder_r64_k1_producer_ranker_physical_wrapper"
    return {
        "inputs": {
            "producer_ranker_physical_wrapper_out": out,
            "producer_ranker_physical_wrapper_report": report,
            "producer_ranker_physical_wrapper_design_dir": design_dir,
            "producer_ranker_physical_wrapper_sweep": sweep,
            "producer_ranker_physical_wrapper_make_target": "3_3_place_gp",
            "ready_valid_equivalence": ready_valid_equivalence,
            "logit_rank_config": logit_rank_config,
            "candidate_merge_config": merge_config,
            "producer_ranker_physical_wrapper_scope": (
                "Materialize and physically probe the first r64/k1 producer-to-ranker "
                "ready-valid wrapper after stream equivalence passed. The wrapper ties "
                "logit_rank_r64_l16_k1 to candidate_stream_merge_fifo_k1_l16_t16_d16 "
                "and records bounded macro-style PPA before scaling r/w or producer coupling."
            ),
        },
        "commands": [
            {
                "name": "build_generator",
                "run": "export PATH=/oss-cad-suite/bin:$PATH && cmake -S . -B build && cmake --build build --target rtlgen",
            },
            {
                "name": "probe_decoder_producer_ranker_physical_wrapper",
                "run": (
                    "python3 npu/eval/probe_llm_decoder_producer_ranker_physical_wrapper.py "
                    f"--logit-rank-config {logit_rank_config} "
                    f"--merge-config {merge_config} "
                    f"--ready-valid-equivalence {ready_valid_equivalence} "
                    f"--design-dir {design_dir} "
                    f"--top {top} "
                    f"--sweep {sweep} "
                    "--platform nangate45 "
                    "--make-target 3_3_place_gp "
                    "--timeout-seconds 1800 "
                    "--stall-timeout-seconds 900 "
                    f"--out {out} "
                    f"--out-md {report}"
                ),
            },
        ],
        "expected_outputs": [
            out,
            report,
            f"{design_dir}/metrics.csv",
            f"{design_dir}/config_decoder_r64_k1_producer_ranker_physical_wrapper.json",
            f"{design_dir}/verilog/{top}.v",
            f"{design_dir}/verilog/logit_rank_r64_l16_k1.v",
            f"{design_dir}/verilog/candidate_stream_merge_fifo_k1_l16_t16_d16.v",
        ],
    }


def _decoder_pipelined_ranker_architecture_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    out = f"{base}/decoder_pipelined_ranker_architecture__{item_id}.json"
    report = f"{base}/decoder_pipelined_ranker_architecture__{item_id}.md"
    merge_config = (
        "runs/designs/activations/candidate_stream_merge_fifo_k1_l16_t16_d16_wrapper/"
        "config_candidate_stream_merge_fifo_k1_l16_t16_d16.json"
    )
    ready_valid_equivalence = (
        f"{base}/decoder_producer_ranker_ready_valid_equivalence__"
        "l2_decoder_producer_ranker_ready_valid_equivalence_v1_r2.json"
    )
    physical_wrapper = (
        f"{base}/decoder_producer_ranker_physical_wrapper__"
        "l2_decoder_producer_ranker_physical_wrapper_v1.json"
    )
    sweep = "runs/campaigns/npu/decoder_pipelined_ranker_architecture/sweeps/nangate45_r64_pipe2.json"
    design_root = "runs/designs/activations"
    tops = [
        "decoder_r64_k1_rankseg8_pipe2_wrapper",
        "decoder_r64_k1_rankseg16_pipe2_wrapper",
        "decoder_r64_k1_rankseg32_pipe2_wrapper",
    ]
    return {
        "inputs": {
            "pipelined_ranker_architecture_out": out,
            "pipelined_ranker_architecture_report": report,
            "pipelined_ranker_architecture_sweep": sweep,
            "pipelined_ranker_architecture_make_target": "3_3_place_gp",
            "pipelined_ranker_architecture_local_lanes": [8, 16, 32],
            "candidate_merge_config": merge_config,
            "ready_valid_equivalence": ready_valid_equivalence,
            "unpipelined_physical_wrapper": physical_wrapper,
            "pipelined_ranker_architecture_scope": (
                "Explore segmented r64/k1 rankers after the unpipelined wrapper measured "
                "a 32 ns critical path. Variants split the 64-logit tile into local rankers "
                "of 8, 16, and 32 lanes, register local winners, register the global winner "
                "before the merge FIFO, and preserve II=1 ready-valid semantics."
            ),
        },
        "commands": [
            {
                "name": "build_generator",
                "run": "export PATH=/oss-cad-suite/bin:$PATH && cmake -S . -B build && cmake --build build --target rtlgen",
            },
            {
                "name": "probe_decoder_pipelined_ranker_architecture",
                "run": (
                    "python3 npu/eval/probe_llm_decoder_pipelined_ranker_architecture.py "
                    f"--merge-config {merge_config} "
                    f"--ready-valid-equivalence {ready_valid_equivalence} "
                    f"--design-root {design_root} "
                    "--local-lanes 8,16,32 "
                    f"--sweep {sweep} "
                    "--platform nangate45 "
                    "--make-target 3_3_place_gp "
                    "--timeout-seconds 1800 "
                    "--stall-timeout-seconds 900 "
                    f"--out {out} "
                    f"--out-md {report}"
                ),
            },
            {
                "name": "build_runs_index",
                "run": "python3 scripts/build_runs_index.py",
            },
        ],
        "expected_outputs": [
            out,
            report,
            "runs/index.csv",
            *[f"{design_root}/{top}/metrics.csv" for top in tops],
            *[f"{design_root}/{top}/verilog/{top}.v" for top in tops],
        ],
    }


def _decoder_rank_tree_architecture_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    out = f"{base}/decoder_rank_tree_architecture__{item_id}.json"
    report = f"{base}/decoder_rank_tree_architecture__{item_id}.md"
    merge_config = (
        "runs/designs/activations/candidate_stream_merge_fifo_k1_l16_t16_d16_wrapper/"
        "config_candidate_stream_merge_fifo_k1_l16_t16_d16.json"
    )
    ready_valid_equivalence = (
        f"{base}/decoder_producer_ranker_ready_valid_equivalence__"
        "l2_decoder_producer_ranker_ready_valid_equivalence_v1_r2.json"
    )
    pipelined_ranker = (
        f"{base}/decoder_pipelined_ranker_architecture__"
        "l2_decoder_pipelined_ranker_architecture_v1.json"
    )
    sweep = "runs/campaigns/npu/decoder_rank_tree_architecture/sweeps/nangate45_r64_ranktree.json"
    design_root = "runs/designs/activations"
    tops = [
        "decoder_r64_k1_ranktree_radix2_pipe6_wrapper",
        "decoder_r64_k1_ranktree_radix4_pipe3_wrapper",
        "decoder_r64_k1_ranktree_radix8_pipe2_wrapper",
    ]
    return {
        "inputs": {
            "rank_tree_architecture_out": out,
            "rank_tree_architecture_report": report,
            "rank_tree_architecture_sweep": sweep,
            "rank_tree_architecture_make_target": "3_3_place_gp",
            "rank_tree_architecture_radices": [2, 4, 8],
            "candidate_merge_config": merge_config,
            "ready_valid_equivalence": ready_valid_equivalence,
            "pipelined_ranker_architecture": pipelined_ranker,
            "rank_tree_architecture_scope": (
                "Explore deeper r64/k1 rank trees after the two-stage radix-8/local-lanes-8 "
                "wrapper measured a 6.6 ns critical path. Variants use radix 2, 4, and 8, "
                "register after every rank level, and preserve II=1 ready-valid semantics."
            ),
        },
        "commands": [
            {
                "name": "build_generator",
                "run": "export PATH=/oss-cad-suite/bin:$PATH && cmake -S . -B build && cmake --build build --target rtlgen",
            },
            {
                "name": "probe_decoder_rank_tree_architecture",
                "run": (
                    "python3 npu/eval/probe_llm_decoder_rank_tree_architecture.py "
                    f"--merge-config {merge_config} "
                    f"--ready-valid-equivalence {ready_valid_equivalence} "
                    f"--design-root {design_root} "
                    "--radices 2,4,8 "
                    f"--sweep {sweep} "
                    "--platform nangate45 "
                    "--make-target 3_3_place_gp "
                    "--timeout-seconds 1800 "
                    "--stall-timeout-seconds 900 "
                    f"--out {out} "
                    f"--out-md {report}"
                ),
            },
            {
                "name": "build_runs_index",
                "run": "python3 scripts/build_runs_index.py",
            },
        ],
        "expected_outputs": [
            out,
            report,
            "runs/index.csv",
            *[f"{design_root}/{top}/metrics.csv" for top in tops],
            *[f"{design_root}/{top}/verilog/{top}.v" for top in tops],
        ],
    }


def _decoder_serial_ranker_architecture_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    out = f"{base}/decoder_serial_ranker_architecture__{item_id}.json"
    report = f"{base}/decoder_serial_ranker_architecture__{item_id}.md"
    merge_config = (
        "runs/designs/activations/candidate_stream_merge_fifo_k1_l16_t16_d16_wrapper/"
        "config_candidate_stream_merge_fifo_k1_l16_t16_d16.json"
    )
    ready_valid_equivalence = (
        f"{base}/decoder_producer_ranker_ready_valid_equivalence__"
        "l2_decoder_producer_ranker_ready_valid_equivalence_v1_r2.json"
    )
    rank_tree = (
        f"{base}/decoder_rank_tree_architecture__"
        "l2_decoder_rank_tree_architecture_v1.json"
    )
    sweep = "runs/campaigns/npu/decoder_serial_ranker_architecture/sweeps/nangate45_r64_serial.json"
    design_root = "runs/designs/activations"
    lane_counts = [1, 2, 4, 8, 16]
    tops = [f"decoder_r64_k1_serial_rank_lpc{lanes}_wrapper" for lanes in lane_counts]
    return {
        "inputs": {
            "serial_ranker_architecture_out": out,
            "serial_ranker_architecture_report": report,
            "serial_ranker_architecture_sweep": sweep,
            "serial_ranker_architecture_make_target": "3_3_place_gp",
            "serial_ranker_architecture_lanes_per_cycle": lane_counts,
            "candidate_merge_config": merge_config,
            "ready_valid_equivalence": ready_valid_equivalence,
            "rank_tree_architecture": rank_tree,
            "serial_ranker_architecture_scope": (
                "Explore area-conservative r64/k1 running-best rankers after the fully parallel "
                "rank-tree sweep. Variants consume 1, 2, 4, 8, or 16 logits per cycle, "
                "backpressure during tile scan, and preserve deterministic top-1 ready-valid output."
            ),
        },
        "commands": [
            {
                "name": "build_generator",
                "run": "export PATH=/oss-cad-suite/bin:$PATH && cmake -S . -B build && cmake --build build --target rtlgen",
            },
            {
                "name": "probe_decoder_serial_ranker_architecture",
                "run": (
                    "python3 npu/eval/probe_llm_decoder_serial_ranker_architecture.py "
                    f"--merge-config {merge_config} "
                    f"--ready-valid-equivalence {ready_valid_equivalence} "
                    f"--design-root {design_root} "
                    "--lanes-per-cycle 1,2,4,8,16 "
                    f"--sweep {sweep} "
                    "--platform nangate45 "
                    "--make-target 3_3_place_gp "
                    "--timeout-seconds 1800 "
                    "--stall-timeout-seconds 900 "
                    f"--out {out} "
                    f"--out-md {report}"
                ),
            },
            {
                "name": "build_runs_index",
                "run": "python3 scripts/build_runs_index.py",
            },
        ],
        "expected_outputs": [
            out,
            report,
            "runs/index.csv",
            *[f"{design_root}/{top}/metrics.csv" for top in tops],
            *[f"{design_root}/{top}/verilog/{top}.v" for top in tops],
        ],
    }


def _decoder_output_projection_producer_synth_boundary_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    out = f"{base}/decoder_output_projection_producer_synth_boundary__{item_id}.json"
    report = f"{base}/decoder_output_projection_producer_synth_boundary__{item_id}.md"
    if "nm8_nm16" in item_id:
        configs = [
            "runs/designs/npu_blocks/npu_fp16_cpp_nm8_producer/config_nm8_producer.json",
            "runs/designs/npu_blocks/npu_fp16_cpp_nm16_producer/config_nm16_producer.json",
        ]
        scope = (
            "Extend the post-scoreboard decoder output-projection producer synthesis boundary "
            "by probing nm8 and nm16 with a synth-only target and explicit timeout before "
            "retrying full PnR."
        )
    else:
        configs = [
            "runs/designs/npu_blocks/npu_fp16_cpp_nm2_producer/config_nm2_producer.json",
            "runs/designs/npu_blocks/npu_fp16_cpp_nm3_producer/config_nm3_producer.json",
            "runs/designs/npu_blocks/npu_fp16_cpp_nm4_producer/config_nm4_producer.json",
        ]
        scope = (
            "Bound decoder output-projection producer synthesis by probing nm2, nm3, "
            "and nm4 with a synth-only target and explicit timeout before retrying full PnR."
        )
    sweep = "runs/campaigns/npu/output_projection_producer_scale/sweeps/nangate45_synth_boundary.json"
    return {
        "inputs": {
            "producer_synth_boundary_out": out,
            "producer_synth_boundary_report": report,
            "producer_synth_boundary_configs": configs,
            "producer_synth_boundary_sweep": sweep,
            "producer_synth_boundary_make_target": "1_2_yosys",
            "producer_synth_boundary_scope": scope,
        },
        "commands": [
            {
                "name": "probe_decoder_output_projection_producer_synth_boundary",
                "run": (
                    "python3 npu/eval/probe_decoder_producer_synth_boundary.py "
                    f"--configs {','.join(configs)} "
                    f"--sweep {sweep} "
                    "--platform nangate45 "
                    "--top npu_top "
                    "--make-target 1_2_yosys "
                    "--timeout-seconds 1800 "
                    "--stall-timeout-seconds 900 "
                    f"--out {out} "
                    f"--out-md {report}"
                ),
            },
        ],
        "expected_outputs": [out, report],
    }


def _decoder_output_projection_producer_pnr_feasibility_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    out = f"{base}/decoder_output_projection_producer_pnr_feasibility__{item_id}.json"
    report = f"{base}/decoder_output_projection_producer_pnr_feasibility__{item_id}.md"
    num_modules = 16 if "nm16" in item_id else 8
    configs = [
        f"runs/designs/npu_blocks/npu_fp16_cpp_nm{num_modules}_producer/config_nm{num_modules}_producer.json",
    ]
    sweep = "runs/campaigns/npu/output_projection_producer_scale/sweeps/nangate45_synth_boundary.json"
    return {
        "inputs": {
            "producer_synth_boundary_out": out,
            "producer_synth_boundary_report": report,
            "producer_synth_boundary_configs": configs,
            "producer_synth_boundary_sweep": sweep,
            "producer_synth_boundary_make_target": "3_3_place_gp",
            "producer_synth_boundary_scope": (
                f"Probe full physical implementation feasibility for the post-scoreboard nm{num_modules} "
                "decoder output-projection producer using the same bounded producer floorplan "
                "before attempting a larger or more integrated physical implementation."
            ),
        },
        "commands": [
            {
                "name": "probe_decoder_output_projection_producer_pnr_feasibility",
                "run": (
                    "python3 npu/eval/probe_decoder_producer_synth_boundary.py "
                    f"--configs {','.join(configs)} "
                    f"--sweep {sweep} "
                    "--platform nangate45 "
                    "--top npu_top "
                    "--make-target 3_3_place_gp "
                    "--timeout-seconds 3600 "
                    "--stall-timeout-seconds 1200 "
                    f"--out {out} "
                    f"--out-md {report}"
                ),
            },
        ],
        "expected_outputs": [out, report],
    }


def _decoder_output_projection_producer_isolated_synth_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    out = f"{base}/decoder_output_projection_producer_isolated_synth__{item_id}.json"
    report = f"{base}/decoder_output_projection_producer_isolated_synth__{item_id}.md"
    configs = [
        "runs/designs/npu_blocks/npu_fp16_cpp_nm1_producer/config_nm1_producer.json",
        "runs/designs/npu_blocks/npu_fp16_cpp_nm2_producer/config_nm2_producer.json",
        "runs/designs/npu_blocks/npu_fp16_cpp_nm3_producer/config_nm3_producer.json",
        "runs/designs/npu_blocks/npu_fp16_cpp_nm4_producer/config_nm4_producer.json",
    ]
    sweep = "runs/campaigns/npu/output_projection_producer_scale/sweeps/nangate45_isolated_synth.json"
    return {
        "inputs": {
            "producer_synth_boundary_out": out,
            "producer_synth_boundary_report": report,
            "producer_synth_boundary_configs": configs,
            "producer_synth_boundary_sweep": sweep,
            "producer_synth_boundary_make_target": "1_2_yosys",
            "producer_synth_boundary_top": "gemm_compute_array",
            "producer_synth_boundary_scope": (
                "Probe the isolated generated gemm_compute_array producer submodule for nm1 through "
                "nm4 with a clockless synth-only target, separating compute-array synthesis from "
                "npu_top control/MMIO/queue synthesis."
            ),
        },
        "commands": [
            {
                "name": "probe_decoder_output_projection_producer_isolated_synth",
                "run": (
                    "python3 npu/eval/probe_decoder_producer_synth_boundary.py "
                    f"--configs {','.join(configs)} "
                    f"--sweep {sweep} "
                    "--platform nangate45 "
                    "--top gemm_compute_array "
                    "--make-target 1_2_yosys "
                    "--timeout-seconds 1800 "
                    "--stall-timeout-seconds 900 "
                    f"--out {out} "
                    f"--out-md {report}"
                ),
            },
        ],
        "expected_outputs": [out, report],
    }


def _decoder_output_projection_producer_top_ablation_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    out = f"{base}/decoder_output_projection_producer_top_ablation__{item_id}.json"
    report = f"{base}/decoder_output_projection_producer_top_ablation__{item_id}.md"
    base_config = "runs/designs/npu_blocks/npu_fp16_cpp_nm2_producer/config_nm2_producer.json"
    sweep = "runs/campaigns/npu/output_projection_producer_scale/sweeps/nangate45_synth_boundary.json"
    return {
        "inputs": {
            "producer_top_ablation_out": out,
            "producer_top_ablation_report": report,
            "producer_top_ablation_base_config": base_config,
            "producer_top_ablation_sweep": sweep,
            "producer_top_ablation_make_target": "1_2_yosys",
            "producer_top_ablation_scope": (
                "Probe nm2 whole-top variants that progressively remove AXI-Lite wrapper files, "
                "SRAM side models, AXI ports, command-queue fetch/decode, and external ports while "
                "recording static RTL size signals and bounded synth status."
            ),
        },
        "commands": [
            {
                "name": "probe_decoder_output_projection_producer_top_ablation",
                "run": (
                    "python3 npu/eval/probe_decoder_producer_top_ablation.py "
                    f"--base-config {base_config} "
                    f"--sweep {sweep} "
                    "--platform nangate45 "
                    "--make-target 1_2_yosys "
                    "--timeout-seconds 1800 "
                    "--stall-timeout-seconds 900 "
                    "--continue-after-failure "
                    f"--out {out} "
                    f"--out-md {report}"
                ),
            },
        ],
        "expected_outputs": [out, report],
    }


def _decoder_output_projection_producer_cq_ablation_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    out = f"{base}/decoder_output_projection_producer_cq_ablation__{item_id}.json"
    report = f"{base}/decoder_output_projection_producer_cq_ablation__{item_id}.md"
    base_config = "runs/designs/npu_blocks/npu_fp16_cpp_nm2_producer/config_nm2_producer.json"
    sweep = "runs/campaigns/npu/output_projection_producer_scale/sweeps/nangate45_synth_boundary.json"
    return {
        "inputs": {
            "producer_cq_ablation_out": out,
            "producer_cq_ablation_report": report,
            "producer_cq_ablation_base_config": base_config,
            "producer_cq_ablation_sweep": sweep,
            "producer_cq_ablation_make_target": "1_2_yosys",
            "producer_cq_ablation_scope": (
                "Probe nm2 npu_top CQ subpaths with diagnostic generator modes: fetch-only, "
                "v0.1 header, DMA_COPY, GEMM issue, VEC validation, SOFTMAX/EVENT, and "
                "v0.2 extension GEMM. The default full CQ path remains unchanged."
            ),
        },
        "commands": [
            {
                "name": "probe_decoder_output_projection_producer_cq_ablation",
                "run": (
                    "python3 npu/eval/probe_decoder_producer_cq_ablation.py "
                    f"--base-config {base_config} "
                    f"--sweep {sweep} "
                    "--platform nangate45 "
                    "--make-target 1_2_yosys "
                    "--timeout-seconds 900 "
                    "--stall-timeout-seconds 450 "
                    "--continue-after-failure "
                    f"--out {out} "
                    f"--out-md {report}"
                ),
            },
        ],
        "expected_outputs": [out, report],
    }


def _decoder_output_projection_producer_softmax_event_ablation_evidence(*, item_id: str) -> dict[str, Any]:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
    out = f"{base}/decoder_output_projection_producer_softmax_event_ablation__{item_id}.json"
    report = f"{base}/decoder_output_projection_producer_softmax_event_ablation__{item_id}.md"
    base_config = "runs/designs/npu_blocks/npu_fp16_cpp_nm2_producer/config_nm2_producer.json"
    sweep = "runs/campaigns/npu/output_projection_producer_scale/sweeps/nangate45_synth_boundary.json"
    return {
        "inputs": {
            "producer_softmax_event_ablation_out": out,
            "producer_softmax_event_ablation_report": report,
            "producer_softmax_event_ablation_base_config": base_config,
            "producer_softmax_event_ablation_sweep": sweep,
            "producer_softmax_event_ablation_make_target": "1_2_yosys",
            "producer_softmax_event_ablation_scope": (
                "Probe the prior failing nm2 CQ SOFTMAX/EVENT slice with diagnostic generator "
                "modes for SOFTMAX checks, SOFTMAX issue, full SOFTMAX, EVENT_SIGNAL, "
                "EVENT_WAIT, dynamic event_state index/update, full EVENT, and combined guard."
            ),
        },
        "commands": [
            {
                "name": "probe_decoder_output_projection_producer_softmax_event_ablation",
                "run": (
                    "python3 npu/eval/probe_decoder_producer_softmax_event_ablation.py "
                    f"--base-config {base_config} "
                    f"--sweep {sweep} "
                    "--platform nangate45 "
                    "--make-target 1_2_yosys "
                    "--timeout-seconds 900 "
                    "--stall-timeout-seconds 450 "
                    "--continue-after-failure "
                    f"--out {out} "
                    f"--out-md {report}"
                ),
            },
        ],
        "expected_outputs": [out, report],
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
        "decoder_logit_rank_streaming_producer_integrated",
        "decoder_output_projection_service",
        "decoder_producer_ranker_coupled_noc",
        "decoder_producer_ranker_service_compatibility",
        "decoder_serial_ranker_producer_replay",
        "decoder_serial_lpc1_producer_coupled_wrapper",
        "decoder_output_projection_cadence_sensitivity",
        "decoder_resident_weight_ranker_fallback",
        "decoder_resident_ranktree_fallback_promotion",
        "decoder_output_projection_ranker_policy",
        "decoder_output_projection_ranker_wrapper_contract",
        "decoder_output_projection_ranker_wrapper_physical",
        "decoder_output_projection_producer_ranker_integration",
        "decoder_producer_ranker_policy_calibration",
        "decoder_stage_breakdown",
        "decoder_attention_kv_memory",
        "decoder_frontier_synthesis",
        "decoder_frontier_synthesis_integrated",
        "decoder_frontier_synthesis_policy_calibrated",
        "decoder_attention_kv_capacity_noc",
        "decoder_attention_kv_noc_scheduler",
        "decoder_attention_kv_spill_scheduler",
        "decoder_attention_kv_hbm_controller",
        "decoder_attention_kv_physical_hbm_frontier",
        "decoder_attention_kv_physical_hbm_quality_backed",
        "decoder_attention_kv_physical_hbm_memory_noc",
        "decoder_attention_kv_physical_hbm_compute_sensitivity",
        "decoder_attention_kv_compute_floor_gap",
        "decoder_attention_kv_compute_ceiling_envelope",
        "decoder_attention_kv_measured_compute",
        "decoder_attention_kv_dense_tile_measured_compute",
        "decoder_attention_kv_measured_compute_partition",
        "decoder_attention_kv_clustered_schedule",
        "decoder_attention_kv_clustered_schedule_overhead",
        "decoder_attention_kv_measured_l1_clustered_schedule",
        "decoder_attention_kv_full_value_l1_clustered_schedule",
        "decoder_attention_kv_all_measured_l1_clustered_schedule",
        "decoder_attention_kv_dense_tile_all_measured_l1_clustered_schedule",
        "decoder_attention_kv_dense_tile_reduction_noc_frontier",
        "decoder_attention_kv_dense_tile_topology_scheduler_pairs",
        "decoder_attention_kv_dense_tile_topology_derived_schedule",
        "decoder_attention_kv_sram_noc_constrained_schedule",
        "decoder_attention_sram_profile",
        "decoder_attention_noc_profile",
        "decoder_attention_kv_quality_gate",
        "decoder_attention_kv_quality_proxy",
        "decoder_attention_kv_native_gqa_proxy",
        "decoder_attention_kv_trace_calibration",
        "decoder_attention_kv_model_native_quality",
        "decoder_attention_kv_model_native_recovery",
        "decoder_output_projection_producer_memory_hierarchy",
        "decoder_output_projection_weight_store_feasibility",
        "decoder_output_projection_weight_store_interface",
        "decoder_output_projection_weight_fetch_wrapper",
        "decoder_producer_ranker_memory_integration_plan",
        "decoder_producer_ranker_ready_valid_equivalence",
        "decoder_producer_ranker_physical_wrapper",
        "decoder_pipelined_ranker_architecture",
        "decoder_rank_tree_architecture",
        "decoder_serial_ranker_architecture",
        "decoder_output_projection_producer_pnr_feasibility",
        "decoder_output_projection_producer_synth_boundary",
        "decoder_output_projection_producer_isolated_synth",
        "decoder_output_projection_producer_top_ablation",
        "decoder_output_projection_producer_cq_ablation",
        "decoder_output_projection_producer_softmax_event_ablation",
        "decoder_quantization_outline",
        "npu_compute_full_path_equivalence_guard",
    }:
        if abstraction_layer_name == "npu_compute_full_path_equivalence_guard":
            decoder_evidence = _npu_compute_full_path_equivalence_guard_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_quantization_outline":
            decoder_evidence = _decoder_quantization_outline_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_output_projection_producer_softmax_event_ablation":
            decoder_evidence = _decoder_output_projection_producer_softmax_event_ablation_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_output_projection_producer_cq_ablation":
            decoder_evidence = _decoder_output_projection_producer_cq_ablation_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_output_projection_producer_top_ablation":
            decoder_evidence = _decoder_output_projection_producer_top_ablation_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_output_projection_producer_isolated_synth":
            decoder_evidence = _decoder_output_projection_producer_isolated_synth_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_output_projection_producer_pnr_feasibility":
            decoder_evidence = _decoder_output_projection_producer_pnr_feasibility_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_output_projection_producer_synth_boundary":
            decoder_evidence = _decoder_output_projection_producer_synth_boundary_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_frontier_synthesis":
            decoder_evidence = _decoder_frontier_synthesis_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_frontier_synthesis_integrated":
            decoder_evidence = _decoder_frontier_synthesis_integrated_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_frontier_synthesis_policy_calibrated":
            decoder_evidence = _decoder_frontier_synthesis_policy_calibrated_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_attention_kv_capacity_noc":
            decoder_evidence = _decoder_attention_kv_capacity_noc_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_attention_kv_noc_scheduler":
            decoder_evidence = _decoder_attention_kv_noc_scheduler_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_attention_kv_spill_scheduler":
            decoder_evidence = _decoder_attention_kv_spill_scheduler_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_attention_kv_hbm_controller":
            decoder_evidence = _decoder_attention_kv_hbm_controller_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_attention_kv_physical_hbm_frontier":
            decoder_evidence = _decoder_attention_kv_physical_hbm_frontier_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_attention_kv_physical_hbm_quality_backed":
            decoder_evidence = _decoder_attention_kv_physical_hbm_quality_backed_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_attention_kv_physical_hbm_memory_noc":
            decoder_evidence = _decoder_attention_kv_physical_hbm_memory_noc_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_attention_kv_physical_hbm_compute_sensitivity":
            decoder_evidence = _decoder_attention_kv_physical_hbm_compute_sensitivity_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_attention_kv_compute_floor_gap":
            decoder_evidence = _decoder_attention_kv_compute_floor_gap_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_attention_kv_compute_ceiling_envelope":
            decoder_evidence = _decoder_attention_kv_compute_ceiling_envelope_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_attention_kv_measured_compute":
            decoder_evidence = _decoder_attention_kv_measured_compute_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_attention_kv_dense_tile_measured_compute":
            decoder_evidence = _decoder_attention_kv_dense_tile_measured_compute_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_attention_kv_measured_compute_partition":
            decoder_evidence = _decoder_attention_kv_measured_compute_partition_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_attention_kv_clustered_schedule":
            decoder_evidence = _decoder_attention_kv_clustered_schedule_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_attention_kv_clustered_schedule_overhead":
            decoder_evidence = _decoder_attention_kv_clustered_schedule_overhead_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_attention_kv_measured_l1_clustered_schedule":
            decoder_evidence = _decoder_attention_kv_measured_l1_clustered_schedule_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_attention_kv_full_value_l1_clustered_schedule":
            decoder_evidence = _decoder_attention_kv_full_value_l1_clustered_schedule_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_attention_kv_all_measured_l1_clustered_schedule":
            decoder_evidence = _decoder_attention_kv_all_measured_l1_clustered_schedule_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_attention_kv_dense_tile_all_measured_l1_clustered_schedule":
            decoder_evidence = _decoder_attention_kv_dense_tile_all_measured_l1_clustered_schedule_evidence(
                item_id=item_id,
            )
        elif abstraction_layer_name == "decoder_attention_kv_dense_tile_reduction_noc_frontier":
            decoder_evidence = _decoder_attention_kv_dense_tile_reduction_noc_frontier_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_attention_kv_dense_tile_topology_scheduler_pairs":
            decoder_evidence = _decoder_attention_kv_dense_tile_topology_scheduler_pairs_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_attention_kv_dense_tile_topology_derived_schedule":
            decoder_evidence = _decoder_attention_kv_dense_tile_topology_derived_schedule_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_attention_kv_sram_noc_constrained_schedule":
            decoder_evidence = _decoder_attention_kv_sram_noc_constrained_schedule_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_attention_sram_profile":
            decoder_evidence = _decoder_attention_sram_profile_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_attention_noc_profile":
            decoder_evidence = _decoder_attention_noc_profile_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_attention_kv_quality_gate":
            decoder_evidence = _decoder_attention_kv_quality_gate_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_attention_kv_quality_proxy":
            decoder_evidence = _decoder_attention_kv_quality_proxy_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_attention_kv_native_gqa_proxy":
            decoder_evidence = _decoder_attention_kv_native_gqa_proxy_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_attention_kv_trace_calibration":
            decoder_evidence = _decoder_attention_kv_trace_calibration_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_attention_kv_model_native_quality":
            decoder_evidence = _decoder_attention_kv_model_native_quality_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_attention_kv_model_native_recovery":
            decoder_evidence = _decoder_attention_kv_model_native_recovery_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_output_projection_producer_memory_hierarchy":
            decoder_evidence = _decoder_output_projection_producer_memory_hierarchy_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_output_projection_weight_store_feasibility":
            decoder_evidence = _decoder_output_projection_weight_store_feasibility_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_output_projection_weight_store_interface":
            decoder_evidence = _decoder_output_projection_weight_store_interface_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_output_projection_weight_fetch_wrapper":
            decoder_evidence = _decoder_output_projection_weight_fetch_wrapper_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_producer_ranker_memory_integration_plan":
            decoder_evidence = _decoder_producer_ranker_memory_integration_plan_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_producer_ranker_ready_valid_equivalence":
            decoder_evidence = _decoder_producer_ranker_ready_valid_equivalence_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_producer_ranker_physical_wrapper":
            decoder_evidence = _decoder_producer_ranker_physical_wrapper_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_pipelined_ranker_architecture":
            decoder_evidence = _decoder_pipelined_ranker_architecture_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_rank_tree_architecture":
            decoder_evidence = _decoder_rank_tree_architecture_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_serial_ranker_architecture":
            decoder_evidence = _decoder_serial_ranker_architecture_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_attention_kv_memory":
            decoder_evidence = _decoder_attention_kv_memory_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_stage_breakdown":
            decoder_evidence = _decoder_stage_breakdown_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_producer_ranker_coupled_noc":
            decoder_evidence = _decoder_producer_ranker_coupled_noc_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_producer_ranker_service_compatibility":
            decoder_evidence = _decoder_producer_ranker_service_compatibility_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_serial_ranker_producer_replay":
            decoder_evidence = _decoder_serial_ranker_producer_replay_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_serial_lpc1_producer_coupled_wrapper":
            decoder_evidence = _decoder_serial_lpc1_producer_coupled_wrapper_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_output_projection_cadence_sensitivity":
            decoder_evidence = _decoder_output_projection_cadence_sensitivity_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_resident_weight_ranker_fallback":
            decoder_evidence = _decoder_resident_weight_ranker_fallback_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_resident_ranktree_fallback_promotion":
            decoder_evidence = _decoder_resident_ranktree_fallback_promotion_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_output_projection_ranker_policy":
            decoder_evidence = _decoder_output_projection_ranker_policy_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_output_projection_ranker_wrapper_contract":
            decoder_evidence = _decoder_output_projection_ranker_wrapper_contract_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_output_projection_ranker_wrapper_physical":
            decoder_evidence = _decoder_output_projection_ranker_wrapper_physical_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_output_projection_producer_ranker_integration":
            decoder_evidence = _decoder_output_projection_producer_ranker_integration_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_producer_ranker_policy_calibration":
            decoder_evidence = _decoder_producer_ranker_policy_calibration_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_output_projection_service":
            decoder_evidence = _decoder_output_projection_service_evidence(item_id=item_id)
        elif abstraction_layer_name == "decoder_logit_rank_streaming_producer_integrated":
            decoder_evidence = _decoder_logit_rank_streaming_producer_integrated_evidence(item_id=item_id)
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
    payload["source_requirement"] = build_source_requirement(
        repo_root=repo_root,
        required_sha=source_commit,
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
