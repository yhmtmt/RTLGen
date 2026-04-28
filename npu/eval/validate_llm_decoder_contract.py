#!/usr/bin/env python3
"""Validate the tiny LLM decoder accuracy-stage artifact contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.eval.compare_llm_decoder_quality import compare_decoder_manifests

JsonDict = Dict[str, Any]


def _repo_path(path: str | Path) -> Path:
    p = Path(path)
    if p.is_absolute():
        return p
    return REPO_ROOT / p


def _load_json(path: str | Path) -> JsonDict:
    with _repo_path(path).open('r', encoding='utf-8') as f:
        return json.load(f)


def _load_jsonl(path: str | Path) -> List[JsonDict]:
    rows: List[JsonDict] = []
    with _repo_path(path).open('r', encoding='utf-8') as f:
        for line_no, raw in enumerate(f, start=1):
            line = raw.strip()
            if not line:
                continue
            try:
                doc = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f'{path}:{line_no}: invalid JSONL row: {exc}') from exc
            if not isinstance(doc, dict):
                raise ValueError(f'{path}:{line_no}: sample row must be an object')
            rows.append(doc)
    return rows


def _sha256(path: str | Path) -> str:
    h = hashlib.sha256()
    with _repo_path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def _require(condition: bool, errors: List[str], message: str) -> None:
    if not condition:
        errors.append(message)


def _require_non_empty_string(doc: JsonDict, key: str, errors: List[str], where: str) -> None:
    _require(isinstance(doc.get(key), str) and bool(str(doc.get(key)).strip()), errors, f'{where}.{key} must be a non-empty string')


def _require_file(doc: JsonDict, key: str, errors: List[str], where: str) -> None:
    _require_non_empty_string(doc, key, errors, where)
    value = doc.get(key)
    if isinstance(value, str) and value.strip():
        _require(_repo_path(value).is_file(), errors, f'{where}.{key} does not exist: {value}')


def _sample_ids(samples: Iterable[JsonDict], *, where: str, errors: List[str]) -> List[str]:
    ids: List[str] = []
    seen: set[str] = set()
    for idx, sample in enumerate(samples):
        sid = sample.get('sample_id')
        _require(isinstance(sid, str) and bool(str(sid).strip()), errors, f'{where}[{idx}].sample_id must be a non-empty string')
        if isinstance(sid, str):
            _require(sid not in seen, errors, f'{where}[{idx}].sample_id is duplicated: {sid}')
            ids.append(sid)
            seen.add(sid)
    return ids


def _validate_topk(entries: Any, errors: List[str], where: str, *, score_key: str) -> None:
    _require(isinstance(entries, list) and bool(entries), errors, f'{where} must be a non-empty array')
    if not isinstance(entries, list):
        return
    for idx, entry in enumerate(entries):
        ewhere = f'{where}[{idx}]'
        _require(isinstance(entry, dict), errors, f'{ewhere} must be an object')
        if not isinstance(entry, dict):
            continue
        _require(isinstance(entry.get('token_id'), int), errors, f'{ewhere}.token_id must be an integer')
        _require_non_empty_string(entry, 'token_text', errors, ewhere)
        _require(isinstance(entry.get(score_key), (int, float)), errors, f'{ewhere}.{score_key} must be numeric')


def _validate_selected_tensors(entries: Any, errors: List[str], where: str) -> None:
    _require(isinstance(entries, list), errors, f'{where} must be an array')
    if not isinstance(entries, list):
        return
    for idx, entry in enumerate(entries):
        ewhere = f'{where}[{idx}]'
        _require(isinstance(entry, dict), errors, f'{ewhere} must be an object')
        if not isinstance(entry, dict):
            continue
        _require_non_empty_string(entry, 'name', errors, ewhere)
        _require(isinstance(entry.get('step'), int), errors, f'{ewhere}.step must be an integer')
        shape = entry.get('shape')
        _require(isinstance(shape, list) and all(isinstance(v, int) and v > 0 for v in shape), errors, f'{ewhere}.shape must be positive integer dimensions')
        for key in ('min', 'max', 'mean', 'std'):
            _require(isinstance(entry.get(key), (int, float)), errors, f'{ewhere}.{key} must be numeric')


def _validate_decoder_doc(doc: JsonDict, sample: JsonDict, errors: List[str], where: str, *, role: str) -> None:
    role_key = 'reference' if role == 'reference' else 'candidate'
    _require(doc.get('sample_id') == sample.get('sample_id'), errors, f'{where}.sample_id must match prompt sample_id')
    _require(doc.get('dataset_id') == 'llm_decoder_eval_tiny_v1', errors, f'{where}.dataset_id must be llm_decoder_eval_tiny_v1')
    _require(doc.get('task') == 'greedy_next_token', errors, f'{where}.task must be greedy_next_token')
    _require(isinstance(doc.get('prompt'), dict), errors, f'{where}.prompt must be an object')
    if isinstance(doc.get('prompt'), dict):
        prompt = doc['prompt']
        _require(prompt.get('text') == sample.get('prompt'), errors, f'{where}.prompt.text must match sample prompt')
        _require(isinstance(prompt.get('token_ids'), list) and all(isinstance(v, int) for v in prompt.get('token_ids', [])), errors, f'{where}.prompt.token_ids must be integer tokens')
        _require(isinstance(prompt.get('tokens'), list), errors, f'{where}.prompt.tokens must be an array')
        _require(isinstance(prompt.get('token_count'), int), errors, f'{where}.prompt.token_count must be an integer')
    _require(isinstance(doc.get(role_key), dict), errors, f'{where}.{role_key} must be an object')
    if not isinstance(doc.get(role_key), dict):
        return
    result = doc[role_key]
    _require(isinstance(result.get('next_token_id'), int), errors, f'{where}.{role_key}.next_token_id must be an integer')
    _require_non_empty_string(result, 'next_token_text', errors, f'{where}.{role_key}')
    if role == 'reference':
        _require(result.get('expected_continuation') == sample.get('expected_continuation'), errors, f'{where}.reference.expected_continuation must match prompt sample')
        _require(isinstance(result.get('next_token_rank'), int), errors, f'{where}.reference.next_token_rank must be an integer')
        _validate_topk(result.get('topk'), errors, f'{where}.reference.topk', score_key='logit')
    else:
        _require_non_empty_string(doc, 'candidate_semantics', errors, where)
        _require(isinstance(result.get('confidence'), (int, float)), errors, f'{where}.candidate.confidence must be numeric')
        _validate_topk(result.get('topk'), errors, f'{where}.candidate.topk', score_key='score')
    _validate_selected_tensors(result.get('selected_tensors', []), errors, f'{where}.{role_key}.selected_tensors')
    if result.get('selected_tensors'):
        _require_non_empty_string(result, 'selected_tensors_sha256', errors, f'{where}.{role_key}')


def validate_decoder_contract(dataset_manifest_path: str | Path) -> JsonDict:
    errors: List[str] = []
    manifest = _load_json(dataset_manifest_path)
    where = str(dataset_manifest_path)
    for key in (
        'dataset_id',
        'task',
        'sample_file',
        'reference_manifest',
        'candidate_manifest',
        'tokenizer_manifest',
        'model_contract',
    ):
        _require_non_empty_string(manifest, key, errors, where)
    _require(manifest.get('dataset_id') == 'llm_decoder_eval_tiny_v1', errors, f'{where}.dataset_id must be llm_decoder_eval_tiny_v1')
    _require(manifest.get('task') == 'greedy_next_token', errors, f'{where}.task must be greedy_next_token')
    for key in ('sample_file', 'reference_manifest', 'candidate_manifest', 'tokenizer_manifest', 'model_contract'):
        _require_file(manifest, key, errors, where)

    samples = _load_jsonl(str(manifest.get('sample_file', ''))) if isinstance(manifest.get('sample_file'), str) else []
    prompt_ids = _sample_ids(samples, where='samples', errors=errors)
    for idx, sample in enumerate(samples):
        swhere = f'samples[{idx}]'
        _require_non_empty_string(sample, 'prompt', errors, swhere)
        _require_non_empty_string(sample, 'expected_continuation', errors, swhere)
        _require_non_empty_string(sample, 'category', errors, swhere)
    _require(manifest.get('sample_count') == len(samples), errors, f'{where}.sample_count must equal samples.jsonl row count')

    reference_manifest = _load_json(str(manifest.get('reference_manifest', ''))) if isinstance(manifest.get('reference_manifest'), str) else {}
    candidate_manifest = _load_json(str(manifest.get('candidate_manifest', ''))) if isinstance(manifest.get('candidate_manifest'), str) else {}
    for label, artifact_manifest in (('reference_manifest', reference_manifest), ('candidate_manifest', candidate_manifest)):
        awhere = label
        _require(artifact_manifest.get('dataset_id') == manifest.get('dataset_id'), errors, f'{awhere}.dataset_id must match dataset manifest')
        _require(artifact_manifest.get('task') == manifest.get('task'), errors, f'{awhere}.task must match dataset manifest')
        _require(artifact_manifest.get('tokenizer_manifest') == manifest.get('tokenizer_manifest'), errors, f'{awhere}.tokenizer_manifest must match dataset manifest')
        _require(artifact_manifest.get('model_contract') == manifest.get('model_contract'), errors, f'{awhere}.model_contract must match dataset manifest')
        _require(isinstance(artifact_manifest.get('samples'), list), errors, f'{awhere}.samples must be an array')

    ref_entries = reference_manifest.get('samples', []) if isinstance(reference_manifest.get('samples'), list) else []
    cand_entries = candidate_manifest.get('samples', []) if isinstance(candidate_manifest.get('samples'), list) else []
    ref_ids = _sample_ids(ref_entries, where='reference_manifest.samples', errors=errors)
    cand_ids = _sample_ids(cand_entries, where='candidate_manifest.samples', errors=errors)
    _require(set(ref_ids) == set(prompt_ids), errors, 'reference_manifest samples must match prompt sample_ids')
    _require(set(cand_ids) == set(prompt_ids), errors, 'candidate_manifest samples must match prompt sample_ids')

    samples_by_id = {str(sample['sample_id']): sample for sample in samples if isinstance(sample.get('sample_id'), str)}
    for entry in ref_entries:
        _require_file(entry, 'reference_json', errors, f"reference_manifest.samples[{entry.get('sample_id', '?')}]")
        if isinstance(entry.get('reference_json'), str):
            actual = _sha256(entry['reference_json'])
            _require(entry.get('reference_sha256') == actual, errors, f"{entry['reference_json']} sha256 mismatch")
            _validate_decoder_doc(_load_json(entry['reference_json']), samples_by_id.get(str(entry.get('sample_id')), {}), errors, str(entry['reference_json']), role='reference')
    for entry in cand_entries:
        _require_file(entry, 'candidate_json', errors, f"candidate_manifest.samples[{entry.get('sample_id', '?')}]")
        if isinstance(entry.get('candidate_json'), str):
            actual = _sha256(entry['candidate_json'])
            _require(entry.get('candidate_sha256') == actual, errors, f"{entry['candidate_json']} sha256 mismatch")
            _validate_decoder_doc(_load_json(entry['candidate_json']), samples_by_id.get(str(entry.get('sample_id')), {}), errors, str(entry['candidate_json']), role='candidate')

    metrics = compare_decoder_manifests(reference_manifest, candidate_manifest)
    aggregate = metrics.get('aggregate', {})
    for key in (
        'sample_count',
        'next_token_id_match_rate',
        'next_token_text_match_rate',
        'topk_contains_reference_id_rate',
        'topk_contains_reference_text_rate',
        'selected_tensor_trace',
    ):
        _require(key in aggregate, errors, f'metrics.aggregate.{key} is required')

    return {
        'ok': not errors,
        'errors': errors,
        'dataset_id': manifest.get('dataset_id', ''),
        'sample_count': len(samples),
        'metrics': metrics,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description='Validate the LLM decoder accuracy-stage dataset/reference/candidate contract.')
    parser.add_argument(
        '--dataset-manifest',
        default='runs/datasets/llm_decoder_eval_tiny_v1/manifest.json',
        help='Dataset manifest to validate.',
    )
    parser.add_argument('--out', help='Optional JSON path for validation summary and comparison metrics.')
    args = parser.parse_args()

    result = validate_decoder_contract(args.dataset_manifest)
    text = json.dumps(result, indent=2, sort_keys=True) + '\n'
    if args.out:
        Path(args.out).write_text(text, encoding='utf-8')
    if not result['ok']:
        print(text, file=sys.stderr, end='')
        return 1
    print(text, end='')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
