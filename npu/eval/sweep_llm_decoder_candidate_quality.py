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


def _aggregate_row(template_name: str, manifest_path: Path, quality_path: Path, metrics: JsonDict) -> JsonDict:
    aggregate = dict(metrics.get("aggregate", {}) or {})
    tensor = dict(aggregate.get("selected_tensor_trace", {}) or {})
    return {
        "template": template_name,
        "candidate_semantics": metrics.get("candidate_semantics", ""),
        "candidate_manifest": _portable_path(manifest_path),
        "quality_json": _portable_path(quality_path),
        "sample_count": aggregate.get("sample_count"),
        "next_token_id_match_rate": aggregate.get("next_token_id_match_rate"),
        "next_token_text_match_rate": aggregate.get("next_token_text_match_rate"),
        "topk_contains_reference_id_rate": aggregate.get("topk_contains_reference_id_rate"),
        "topk_contains_reference_text_rate": aggregate.get("topk_contains_reference_text_rate"),
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
        results.append(_aggregate_row(template_name, manifest_path, quality_path, metrics))

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
