#!/usr/bin/env python3
"""Compare decoder candidate artifacts against decoder reference artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.eval.llm_decoder_quality import compare_decoder_reference_docs, load_json


JsonDict = Dict[str, Any]


def _resolve_repo_path(path: str | Path) -> Path:
    p = Path(path)
    if p.is_absolute():
        return p
    return REPO_ROOT / p


def _tensor_key(tensor_doc: JsonDict) -> Tuple[str, int]:
    return (str(tensor_doc.get('name', '')), int(tensor_doc.get('step', 0)))


def _compare_selected_tensors(reference_doc: JsonDict, candidate_doc: JsonDict) -> JsonDict:
    ref_tensors = {
        _tensor_key(entry): entry
        for entry in reference_doc.get('reference', {}).get('selected_tensors', [])
        if isinstance(entry, dict)
    }
    cand_tensors = {
        _tensor_key(entry): entry
        for entry in candidate_doc.get('candidate', {}).get('selected_tensors', [])
        if isinstance(entry, dict)
    }
    ref_keys = set(ref_tensors)
    cand_keys = set(cand_tensors)
    common_keys = sorted(ref_keys & cand_keys)
    missing_in_reference = [
        {'name': name, 'step': step}
        for name, step in sorted(cand_keys - ref_keys)
    ]
    missing_in_candidate = [
        {'name': name, 'step': step}
        for name, step in sorted(ref_keys - cand_keys)
    ]

    compared: List[JsonDict] = []
    shape_match_count = 0
    for key in common_keys:
        ref_tensor = ref_tensors[key]
        cand_tensor = cand_tensors[key]
        ref_shape = [int(v) for v in ref_tensor.get('shape', [])]
        cand_shape = [int(v) for v in cand_tensor.get('shape', [])]
        shape_match = int(ref_shape == cand_shape)
        shape_match_count += shape_match
        compared.append({
            'name': key[0],
            'step': key[1],
            'shape_match': shape_match,
            'reference_shape': ref_shape,
            'candidate_shape': cand_shape,
            'deltas': {
                'min_abs_delta': abs(float(ref_tensor.get('min', 0.0)) - float(cand_tensor.get('min', 0.0))),
                'max_abs_delta': abs(float(ref_tensor.get('max', 0.0)) - float(cand_tensor.get('max', 0.0))),
                'mean_abs_delta': abs(float(ref_tensor.get('mean', 0.0)) - float(cand_tensor.get('mean', 0.0))),
                'std_abs_delta': abs(float(ref_tensor.get('std', 0.0)) - float(cand_tensor.get('std', 0.0))),
            },
            'candidate_quantization': cand_tensor.get('quantization'),
        })

    return {
        'compared_tensors': compared,
        'aggregate': {
            'reference_tensor_count': len(ref_tensors),
            'candidate_tensor_count': len(cand_tensors),
            'matched_tensor_count': len(common_keys),
            'shape_match_count': shape_match_count,
            'shape_match_rate': (float(shape_match_count) / float(len(common_keys))) if common_keys else 0.0,
            'missing_in_reference_count': len(missing_in_reference),
            'missing_in_candidate_count': len(missing_in_candidate),
        },
        'missing_in_reference': missing_in_reference,
        'missing_in_candidate': missing_in_candidate,
    }


def compare_decoder_manifests(reference_manifest: JsonDict, candidate_manifest: JsonDict) -> JsonDict:
    if reference_manifest.get('dataset_id') != candidate_manifest.get('dataset_id'):
        raise ValueError('dataset_id mismatch between reference and candidate manifests')
    if reference_manifest.get('task') != candidate_manifest.get('task'):
        raise ValueError('task mismatch between reference and candidate manifests')

    ref_samples = {
        str(entry['sample_id']): entry
        for entry in reference_manifest.get('samples', [])
    }
    cand_samples = {
        str(entry['sample_id']): entry
        for entry in candidate_manifest.get('samples', [])
    }
    if set(ref_samples) != set(cand_samples):
        missing_ref = sorted(set(cand_samples) - set(ref_samples))
        missing_cand = sorted(set(ref_samples) - set(cand_samples))
        raise ValueError(
            f'sample_id mismatch between manifests: missing_in_reference={missing_ref} '
            f'missing_in_candidate={missing_cand}'
        )

    sample_metrics: List[JsonDict] = []
    id_match_count = 0
    text_match_count = 0
    for sample_id in sorted(ref_samples):
        ref_doc = load_json(_resolve_repo_path(ref_samples[sample_id]['reference_json']))
        cand_doc = load_json(_resolve_repo_path(cand_samples[sample_id]['candidate_json']))
        metrics = compare_decoder_reference_docs(ref_doc, cand_doc)
        metrics['selected_tensor_trace'] = _compare_selected_tensors(ref_doc, cand_doc)
        sample_metrics.append(metrics)
        id_match_count += int(metrics['aggregate']['next_token_id_match'])
        text_match_count += int(metrics['aggregate']['next_token_text_match'])

    total = len(sample_metrics)
    total_matched_tensors = sum(
        int(sample['selected_tensor_trace']['aggregate']['matched_tensor_count'])
        for sample in sample_metrics
    )
    total_shape_match_count = sum(
        int(sample['selected_tensor_trace']['aggregate']['shape_match_count'])
        for sample in sample_metrics
    )
    total_missing_in_reference = sum(
        int(sample['selected_tensor_trace']['aggregate']['missing_in_reference_count'])
        for sample in sample_metrics
    )
    total_missing_in_candidate = sum(
        int(sample['selected_tensor_trace']['aggregate']['missing_in_candidate_count'])
        for sample in sample_metrics
    )
    return {
        'dataset_id': reference_manifest['dataset_id'],
        'task': reference_manifest['task'],
        'candidate_semantics': candidate_manifest.get('candidate_semantics', ''),
        'samples': sample_metrics,
        'aggregate': {
            'sample_count': total,
            'next_token_id_match_count': id_match_count,
            'next_token_text_match_count': text_match_count,
            'next_token_id_match_rate': (float(id_match_count) / float(total)) if total else 0.0,
            'next_token_text_match_rate': (float(text_match_count) / float(total)) if total else 0.0,
            'selected_tensor_trace': {
                'matched_tensor_count': total_matched_tensors,
                'shape_match_count': total_shape_match_count,
                'shape_match_rate': (float(total_shape_match_count) / float(total_matched_tensors)) if total_matched_tensors else 0.0,
                'missing_in_reference_count': total_missing_in_reference,
                'missing_in_candidate_count': total_missing_in_candidate,
            },
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser(description='Compare decoder candidate outputs against decoder reference fixtures.')
    ap.add_argument('--reference-manifest', required=True, help='Reference manifest json path')
    ap.add_argument('--candidate-manifest', required=True, help='Candidate manifest json path')
    ap.add_argument('--out', help='Optional metrics json output path')
    args = ap.parse_args()

    metrics = compare_decoder_manifests(
        load_json(_resolve_repo_path(args.reference_manifest)),
        load_json(_resolve_repo_path(args.candidate_manifest)),
    )
    text = json.dumps(metrics, indent=2) + '\n'
    if args.out:
        Path(args.out).write_text(text, encoding='utf-8')
    else:
        print(text, end='')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
