#!/usr/bin/env python3
"""Run decoder-quality comparisons for candidate backend templates."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.eval.compare_llm_decoder_quality import compare_decoder_manifests
from npu.eval.llm_decoder_quality import (
    build_decoder_candidate_doc,
    load_json,
    load_jsonl,
    load_tokenizer_bundle,
)


JsonDict = Dict[str, Any]


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _resolve_repo_path(path: str | Path) -> Path:
    p = Path(path)
    if p.is_absolute():
        return p
    return REPO_ROOT / p


def _portable_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _candidate_templates(model_contract: JsonDict, requested: List[str]) -> Dict[str, JsonDict]:
    templates = model_contract.get("backend_templates", {}) or {}
    if not isinstance(templates, dict):
        raise ValueError("model_contract.backend_templates must be an object")
    names = requested or sorted(name for name in templates if str(name).startswith("candidate_"))
    out: Dict[str, JsonDict] = {}
    for name in names:
        if name not in templates:
            raise ValueError(f"candidate backend template not found: {name}")
        cfg = dict(templates[name])
        cfg["role"] = "candidate"
        cfg["interface"] = "decoder_backend_v1"
        out[name] = cfg
    if not out:
        raise ValueError("no candidate backend templates selected")
    return out


def _candidate_template(model_contract: JsonDict, name: str) -> JsonDict:
    templates = model_contract.get("backend_templates", {}) or {}
    if not isinstance(templates, dict):
        raise ValueError("model_contract.backend_templates must be an object")
    if name not in templates:
        raise ValueError(f"candidate backend template not found: {name}")
    cfg = dict(templates[name])
    cfg["role"] = "candidate"
    cfg["interface"] = "decoder_backend_v1"
    return cfg


def _named_grid_point(base: JsonDict, name: str, **updates: Any) -> tuple[str, JsonDict]:
    cfg = dict(base)
    cfg.pop("candidate_semantics", None)
    for key, value in updates.items():
        if value is None:
            cfg.pop(key, None)
        else:
            cfg[key] = value
    return name, cfg


def _rough_grid_templates(model_contract: JsonDict, grid_name: str) -> Dict[str, JsonDict]:
    if grid_name not in {"decoder_probability_broad_v1", "decoder_probability_fp_formats_v1"}:
        raise ValueError(f"unsupported rough grid: {grid_name}")
    exact = _candidate_template(model_contract, "candidate_onnx_softmax_exact")
    approx = _candidate_template(model_contract, "candidate_onnx_softmax_approx")
    if grid_name == "decoder_probability_fp_formats_v1":
        points = [
            ("candidate_onnx_softmax_exact", exact),
            _named_grid_point(exact, "grid_logits_fp16", logit_float_format="fp16"),
            _named_grid_point(exact, "grid_logits_bf16", logit_float_format="bf16"),
            _named_grid_point(exact, "grid_logits_fp8_e5m2", logit_float_format="fp8_e5m2"),
            _named_grid_point(exact, "grid_logits_fp8_e4m3", logit_float_format="fp8_e4m3"),
            _named_grid_point(exact, "grid_softmax_input_fp16", softmax_input_float_format="fp16"),
            _named_grid_point(exact, "grid_softmax_input_bf16", softmax_input_float_format="bf16"),
            _named_grid_point(exact, "grid_softmax_weight_fp16", softmax_weight_float_format="fp16"),
            _named_grid_point(exact, "grid_softmax_weight_bf16", softmax_weight_float_format="bf16"),
            _named_grid_point(
                exact,
                "grid_norm_recip_fp16",
                normalization_mode="reciprocal_float",
                normalization_reciprocal_float_format="fp16",
            ),
            _named_grid_point(
                exact,
                "grid_norm_recip_bf16",
                normalization_mode="reciprocal_float",
                normalization_reciprocal_float_format="bf16",
            ),
            _named_grid_point(exact, "grid_prob_fp16", probability_float_format="fp16"),
            _named_grid_point(exact, "grid_prob_bf16", probability_float_format="bf16"),
            _named_grid_point(exact, "grid_prob_fp8_e5m2", probability_float_format="fp8_e5m2"),
            _named_grid_point(exact, "grid_prob_fp8_e4m3", probability_float_format="fp8_e4m3"),
            _named_grid_point(
                approx,
                "grid_approx_pwl_fp16_path",
                softmax_input_quant_bits=None,
                softmax_weight_quant_bits=None,
                softmax_input_float_format="fp16",
                softmax_weight_float_format="fp16",
                normalization_mode="reciprocal_float",
                normalization_reciprocal_bits=None,
                normalization_reciprocal_float_format="fp16",
            ),
            _named_grid_point(
                approx,
                "grid_approx_pwl_bf16_path",
                softmax_input_quant_bits=None,
                softmax_weight_quant_bits=None,
                softmax_input_float_format="bf16",
                softmax_weight_float_format="bf16",
                normalization_mode="reciprocal_float",
                normalization_reciprocal_bits=None,
                normalization_reciprocal_float_format="bf16",
            ),
        ]
        return {name: cfg for name, cfg in points}
    points = [
        ("candidate_onnx_softmax_exact", exact),
        _named_grid_point(exact, "grid_exact_logits_q8", logit_quant_bits=8),
        _named_grid_point(exact, "grid_exact_logits_q6", logit_quant_bits=6),
        _named_grid_point(exact, "grid_exact_logits_q4", logit_quant_bits=4),
        _named_grid_point(exact, "grid_exact_prob_q8", probability_quant_bits=8),
        _named_grid_point(
            approx,
            "grid_approx_pwl_float_norm_exact",
            softmax_input_quant_bits=None,
            softmax_weight_quant_bits=None,
            normalization_mode="exact",
            normalization_reciprocal_bits=None,
        ),
        _named_grid_point(
            approx,
            "grid_approx_pwl_in_q8_w_fp_norm_exact",
            softmax_input_quant_bits=8,
            softmax_weight_quant_bits=None,
            normalization_mode="exact",
            normalization_reciprocal_bits=None,
        ),
        _named_grid_point(
            approx,
            "grid_approx_pwl_in_fp_w_q8_norm_exact",
            softmax_input_quant_bits=None,
            softmax_weight_quant_bits=8,
            normalization_mode="exact",
            normalization_reciprocal_bits=None,
        ),
        _named_grid_point(
            approx,
            "grid_approx_pwl_in_q8_w_q8_norm_exact",
            softmax_input_quant_bits=8,
            softmax_weight_quant_bits=8,
            normalization_mode="exact",
            normalization_reciprocal_bits=None,
        ),
        _named_grid_point(
            approx,
            "grid_approx_pwl_in_q6_w_q6_norm_exact",
            softmax_input_quant_bits=6,
            softmax_weight_quant_bits=6,
            normalization_mode="exact",
            normalization_reciprocal_bits=None,
        ),
        _named_grid_point(
            approx,
            "grid_approx_pwl_in_q4_w_q4_norm_exact",
            softmax_input_quant_bits=4,
            softmax_weight_quant_bits=4,
            normalization_mode="exact",
            normalization_reciprocal_bits=None,
        ),
        _named_grid_point(
            approx,
            "grid_approx_pwl_float_norm_recip_q10",
            softmax_input_quant_bits=None,
            softmax_weight_quant_bits=None,
            normalization_mode="reciprocal_quantized",
            normalization_reciprocal_bits=10,
        ),
        _named_grid_point(
            approx,
            "grid_approx_pwl_in_q8_w_q8_norm_recip_q12",
            softmax_input_quant_bits=8,
            softmax_weight_quant_bits=8,
            normalization_mode="reciprocal_quantized",
            normalization_reciprocal_bits=12,
        ),
        _named_grid_point(
            approx,
            "grid_approx_pwl_in_q6_w_q6_norm_recip_q10",
            softmax_input_quant_bits=6,
            softmax_weight_quant_bits=6,
            normalization_mode="reciprocal_quantized",
            normalization_reciprocal_bits=10,
        ),
        _named_grid_point(
            approx,
            "grid_approx_pwl_in_q4_w_q4_norm_recip_q8",
            softmax_input_quant_bits=4,
            softmax_weight_quant_bits=4,
            normalization_mode="reciprocal_quantized",
            normalization_reciprocal_bits=8,
        ),
        _named_grid_point(
            approx,
            "grid_approx_pwl_in_q8_w_q8_norm_recip_q12_prob_q8",
            softmax_input_quant_bits=8,
            softmax_weight_quant_bits=8,
            normalization_mode="reciprocal_quantized",
            normalization_reciprocal_bits=12,
            probability_quant_bits=8,
        ),
    ]
    return {name: cfg for name, cfg in points}


def _generate_candidate_manifest(
    *,
    dataset_manifest: JsonDict,
    dataset_manifest_path: Path,
    tokenizer_manifest: JsonDict,
    tokenizer_manifest_path: Path,
    tokenizer_bundle: JsonDict,
    model_contract: JsonDict,
    model_contract_path: Path,
    samples: List[JsonDict],
    backend_config: JsonDict,
    out_dir: Path,
) -> JsonDict:
    out_dir.mkdir(parents=True, exist_ok=True)
    vocab = dict(tokenizer_bundle["vocab"])
    manifest_samples: List[JsonDict] = []
    candidate_semantics = ""
    for sample in samples:
        doc = build_decoder_candidate_doc(
            dataset_manifest=dataset_manifest,
            sample=sample,
            tokenizer_manifest=tokenizer_manifest,
            vocab=vocab,
            model_contract=model_contract,
            dataset_manifest_path=_portable_path(dataset_manifest_path),
            tokenizer_manifest_path=_portable_path(tokenizer_manifest_path),
            model_contract_path=_portable_path(model_contract_path),
            backend_config=backend_config,
            tokenizer_bundle=tokenizer_bundle,
        )
        candidate_semantics = str(doc.get("candidate_semantics", candidate_semantics))
        out_path = out_dir / f"{sample['sample_id']}.json"
        raw = (json.dumps(doc, indent=2, sort_keys=True) + "\n").encode("utf-8")
        out_path.write_bytes(raw)
        manifest_samples.append(
            {
                "sample_id": sample["sample_id"],
                "candidate_json": _portable_path(out_path),
                "candidate_sha256": _sha256_bytes(raw),
            }
        )

    return {
        "version": 0.1,
        "dataset_id": dataset_manifest["dataset_id"],
        "task": dataset_manifest["task"],
        "tokenizer_manifest": _portable_path(tokenizer_manifest_path),
        "model_contract": _portable_path(model_contract_path),
        "backend_config": backend_config,
        "candidate_semantics": candidate_semantics,
        "samples": manifest_samples,
    }


def _aggregate_row(template_name: str, manifest_path: Path, quality_path: Path, backend_config: JsonDict, metrics: JsonDict) -> JsonDict:
    aggregate = dict(metrics.get("aggregate", {}) or {})
    tensor = dict(aggregate.get("selected_tensor_trace", {}) or {})
    mismatch_sample_ids = [
        str(sample.get("sample_id", ""))
        for sample in metrics.get("samples", []) or []
        if not int((sample.get("aggregate", {}) or {}).get("next_token_id_match", 0))
    ]
    topk_miss_sample_ids = [
        str(sample.get("sample_id", ""))
        for sample in metrics.get("samples", []) or []
        if not int((sample.get("aggregate", {}) or {}).get("topk_contains_reference_id", 0))
    ]
    return {
        "template": template_name,
        "candidate_semantics": metrics.get("candidate_semantics", ""),
        "candidate_manifest": _portable_path(manifest_path),
        "quality_json": _portable_path(quality_path),
        "logit_quant_bits": backend_config.get("logit_quant_bits", 0),
        "logit_float_format": backend_config.get("logit_float_format", ""),
        "softmax_mode": backend_config.get("softmax_mode", "exact"),
        "softmax_input_quant_bits": backend_config.get("softmax_input_quant_bits", 0),
        "softmax_input_float_format": backend_config.get("softmax_input_float_format", ""),
        "softmax_weight_quant_bits": backend_config.get("softmax_weight_quant_bits", 0),
        "softmax_weight_float_format": backend_config.get("softmax_weight_float_format", ""),
        "normalization_mode": backend_config.get("normalization_mode", "exact"),
        "normalization_reciprocal_bits": backend_config.get("normalization_reciprocal_bits", 0),
        "normalization_reciprocal_float_format": backend_config.get("normalization_reciprocal_float_format", ""),
        "probability_quant_bits": backend_config.get("probability_quant_bits", 0),
        "probability_float_format": backend_config.get("probability_float_format", ""),
        "sample_count": aggregate.get("sample_count"),
        "next_token_id_match_rate": aggregate.get("next_token_id_match_rate"),
        "next_token_text_match_rate": aggregate.get("next_token_text_match_rate"),
        "topk_contains_reference_id_rate": aggregate.get("topk_contains_reference_id_rate"),
        "topk_contains_reference_text_rate": aggregate.get("topk_contains_reference_text_rate"),
        "next_token_mismatch_sample_ids": mismatch_sample_ids,
        "topk_miss_sample_ids": topk_miss_sample_ids,
        "selected_tensor_shape_match_rate": tensor.get("shape_match_rate"),
        "selected_tensor_trace_sha256_match_rate": tensor.get("trace_sha256_match_rate"),
        "selected_tensor_delta_rollups": tensor.get("delta_rollups", {}),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dataset-manifest", default="runs/datasets/llm_decoder_eval_tiny_v1/manifest.json")
    ap.add_argument(
        "--template",
        action="append",
        default=[],
        help="Candidate backend template name. Defaults to all model_contract backend_templates starting with candidate_.",
    )
    ap.add_argument(
        "--rough-grid",
        default="",
        help="Generate a built-in rough approximation grid, e.g. decoder_probability_broad_v1 or decoder_probability_fp_formats_v1.",
    )
    ap.add_argument("--out-dir", default="runs/datasets/llm_decoder_eval_tiny_v1/candidate_sweeps/local")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    dataset_manifest_path = _resolve_repo_path(args.dataset_manifest)
    dataset_manifest = load_json(dataset_manifest_path)
    sample_file = _resolve_repo_path(dataset_manifest["sample_file"])
    tokenizer_manifest_path = _resolve_repo_path(dataset_manifest["tokenizer_manifest"])
    model_contract_path = _resolve_repo_path(dataset_manifest["model_contract"])
    reference_manifest_path = _resolve_repo_path(dataset_manifest["reference_manifest"])
    tokenizer_manifest = load_json(tokenizer_manifest_path)
    model_contract = load_json(model_contract_path)
    reference_manifest = load_json(reference_manifest_path)
    tokenizer_bundle = load_tokenizer_bundle(tokenizer_manifest, manifest_path=tokenizer_manifest_path)
    samples = load_jsonl(sample_file)
    if args.rough_grid:
        if args.template:
            raise ValueError("--template cannot be combined with --rough-grid")
        templates = _rough_grid_templates(model_contract, str(args.rough_grid))
    else:
        templates = _candidate_templates(model_contract, [str(v) for v in args.template])

    out_dir = _resolve_repo_path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    results: List[JsonDict] = []
    for template_name, backend_config in templates.items():
        template_dir = out_dir / template_name
        candidate_dir = template_dir / "candidate"
        candidate_manifest = _generate_candidate_manifest(
            dataset_manifest=dataset_manifest,
            dataset_manifest_path=dataset_manifest_path,
            tokenizer_manifest=tokenizer_manifest,
            tokenizer_manifest_path=tokenizer_manifest_path,
            tokenizer_bundle=tokenizer_bundle,
            model_contract=model_contract,
            model_contract_path=model_contract_path,
            samples=samples,
            backend_config=backend_config,
            out_dir=candidate_dir,
        )
        manifest_path = template_dir / "candidate_manifest.json"
        manifest_path.write_text(json.dumps(candidate_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        metrics = compare_decoder_manifests(reference_manifest, candidate_manifest)
        quality_path = template_dir / "quality.json"
        quality_path.write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        results.append(_aggregate_row(template_name, manifest_path, quality_path, backend_config, metrics))

    best = sorted(
        results,
        key=lambda row: (
            -float(row.get("next_token_id_match_rate") or 0.0),
            -float(row.get("topk_contains_reference_id_rate") or 0.0),
            str(row.get("template") or ""),
        ),
    )[0]
    doc = {
        "version": 0.1,
        "dataset_id": dataset_manifest["dataset_id"],
        "task": dataset_manifest["task"],
        "reference_manifest": _portable_path(reference_manifest_path),
        "rough_grid": str(args.rough_grid),
        "scope_note": (
            "Approximation sensitivity is distribution-dependent. This sweep is a coarse map for the pinned "
            "llm_decoder_eval_tiny_v1 prompt/model/tokenizer setup and must not be treated as general "
            "acceptance evidence without broader datasets. Floating-point-like formats preserve dynamic "
            "range differently from fixed integer probability quantization, so compare rank/top-k behavior "
            "rather than only final probability values."
        ),
        "template_count": len(results),
        "templates": results,
        "best_template": best,
    }
    text = json.dumps(doc, indent=2, sort_keys=True) + "\n"
    if args.out:
        out_path = _resolve_repo_path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
