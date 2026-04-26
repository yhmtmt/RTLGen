#!/usr/bin/env python3
"""Generate deterministic candidate fixtures for LLM attention-proxy model sets."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List

from llm_reference import build_candidate_fixture

REPO_ROOT = Path(__file__).resolve().parents[2]


def _repo_friendly(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description='Generate deterministic LLM attention-proxy candidate fixtures.')
    ap.add_argument('--manifest', required=True, help='Model-set manifest.json path')
    ap.add_argument('--out-dir', help='Fixture output directory (default: <manifest_dir>/candidate)')
    ap.add_argument('--out-manifest', help='Optional candidate_manifest.json path')
    args = ap.parse_args()

    manifest_path = Path(args.manifest)
    model_manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    model_set_id = str(model_manifest.get('model_set_id', '')).strip() or manifest_path.parent.name
    out_dir = Path(args.out_dir) if args.out_dir else manifest_path.parent / 'candidate'
    out_dir.mkdir(parents=True, exist_ok=True)
    out_manifest = Path(args.out_manifest) if args.out_manifest else manifest_path.parent / 'candidate_manifest.json'

    entries: List[Dict[str, Any]] = []
    for model in model_manifest.get('models', []):
        model_id = str(model.get('model_id', '')).strip()
        onnx_path = REPO_ROOT / str(model.get('onnx_path', '')).strip()
        fixture = build_candidate_fixture(onnx_path, model_id=model_id)
        fixture_path = out_dir / f'{model_id}.json'
        fixture_path.write_text(json.dumps(fixture, indent=2) + '\n', encoding='utf-8')
        entries.append(
            {
                'model_id': model_id,
                'onnx_path': str(model.get('onnx_path', '')).strip(),
                'candidate_json': _repo_friendly(fixture_path),
                'candidate_sha256': _sha256(fixture_path),
                'candidate_semantics': fixture['candidate_semantics'],
                'input_shape': fixture['input']['shape'],
                'output_tensors': sorted(fixture['outputs'].keys()),
            }
        )

    doc = {
        'version': 0.1,
        'model_set_id': model_set_id,
        'description': f'Deterministic candidate fixtures for {model_set_id} attention-proxy models using current int8 placeholder semantics.',
        'models': entries,
    }
    out_manifest.write_text(json.dumps(doc, indent=2) + '\n', encoding='utf-8')
    print(f'gen_llm_candidate_suite: wrote {len(entries)} fixtures to {out_dir}')
    print(f'gen_llm_candidate_suite: wrote manifest to {out_manifest}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
