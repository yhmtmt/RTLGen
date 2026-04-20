#!/usr/bin/env python3
"""Generate candidate decoder fixtures for llm_decoder_eval_tiny_v1."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Dict, List

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.eval.llm_decoder_quality import (
    build_decoder_candidate_doc,
    load_json,
    load_jsonl,
    load_vocab,
    resolve_decoder_backend_config,
)


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _resolve_repo_path(path: str | Path) -> Path:
    p = Path(path)
    if p.is_absolute():
        return p
    return REPO_ROOT / p


def _portable_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset-manifest', default='runs/datasets/llm_decoder_eval_tiny_v1/manifest.json')
    parser.add_argument('--out-dir', default='runs/datasets/llm_decoder_eval_tiny_v1/candidate')
    parser.add_argument('--out-manifest', default='runs/datasets/llm_decoder_eval_tiny_v1/candidate_manifest.json')
    args = parser.parse_args()

    dataset_manifest_path = _resolve_repo_path(args.dataset_manifest)
    dataset_manifest = load_json(dataset_manifest_path)
    sample_file = _resolve_repo_path(dataset_manifest['sample_file'])
    tokenizer_manifest_path = _resolve_repo_path(dataset_manifest['tokenizer_manifest'])
    model_contract_path = _resolve_repo_path(dataset_manifest['model_contract'])
    tokenizer_manifest = load_json(tokenizer_manifest_path)
    model_contract = load_json(model_contract_path)
    vocab = load_vocab(_resolve_repo_path(tokenizer_manifest['vocab_json']))
    samples = load_jsonl(sample_file)
    backend_config = resolve_decoder_backend_config(dataset_manifest, model_contract, role='candidate')

    out_dir = _resolve_repo_path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest_samples: List[Dict[str, object]] = []
    candidate_semantics = ''
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
        )
        candidate_semantics = str(doc.get('candidate_semantics', candidate_semantics))
        out_path = out_dir / f"{sample['sample_id']}.json"
        raw = (json.dumps(doc, indent=2, sort_keys=True) + '\n').encode('utf-8')
        out_path.write_bytes(raw)
        manifest_samples.append({
            'sample_id': sample['sample_id'],
            'candidate_json': _portable_path(out_path),
            'candidate_sha256': _sha256_bytes(raw),
        })

    manifest_doc = {
        'version': 0.1,
        'dataset_id': dataset_manifest['dataset_id'],
        'task': dataset_manifest['task'],
        'tokenizer_manifest': _portable_path(tokenizer_manifest_path),
        'model_contract': _portable_path(model_contract_path),
        'backend_config': backend_config,
        'candidate_semantics': candidate_semantics,
        'samples': manifest_samples,
    }
    out_manifest = _resolve_repo_path(args.out_manifest)
    out_manifest.write_text(json.dumps(manifest_doc, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
