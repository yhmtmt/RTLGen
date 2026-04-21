#!/usr/bin/env python3
"""Run a decoder next-token candidate step from a command_json_v1 request.

This runner is the first approximation-aware candidate side for decoder-quality
evaluation. It shares the exact tokenizer/model contract with the ONNX reference
runner, then applies explicit softmax and normalization choices before argmax.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.eval.run_llm_decoder_onnx_reference import (
    _build_feeds,
    _decode_token,
    _extract_next_token_logits,
    _load_model_config,
    _load_onnxruntime,
    _load_request,
    _load_tokenizer_runtime,
    _prepare_prompt,
    _resolve_repo_path,
)
from npu.eval.llm_decoder_quality import load_json, load_tokenizer_bundle

JsonDict = Dict[str, Any]


def _topk_pairs(values: Sequence[float], *, k: int) -> Iterable[Tuple[int, float]]:
    if k <= 0:
        return []
    order = sorted(range(len(values)), key=lambda idx: float(values[idx]), reverse=True)[:k]
    return [(int(idx), float(values[idx])) for idx in order]


def _quantize_logits_symmetric(logits: Sequence[float], *, bits: int) -> Tuple[list[float], JsonDict]:
    if bits < 2:
        raise SystemExit('backend_config.logit_quant_bits must be >= 2')
    values = [float(v) for v in logits]
    if not values:
        raise SystemExit('candidate runner received empty logits')
    max_abs = max(abs(v) for v in values)
    levels = (1 << (bits - 1)) - 1
    if max_abs == 0.0 or levels <= 0:
        return list(values), {
            'mode': 'symmetric_logit_quant',
            'bits': bits,
            'levels': levels,
            'scale': 1.0,
            'max_abs': max_abs,
        }
    scale = max_abs / float(levels)
    quantized = []
    for value in values:
        q = int(round(value / scale))
        q = max(-levels, min(levels, q))
        quantized.append(float(q) * scale)
    return quantized, {
        'mode': 'symmetric_logit_quant',
        'bits': bits,
        'levels': levels,
        'scale': scale,
        'max_abs': max_abs,
    }


def _softmax_exact(logits: Sequence[float]) -> Tuple[list[float], JsonDict]:
    values = [float(v) for v in logits]
    if not values:
        raise SystemExit('softmax_exact received empty logits')
    max_logit = max(values)
    shifted = [value - max_logit for value in values]
    weights = [math.exp(value) for value in shifted]
    return weights, {
        'mode': 'softmax_exact',
        'max_logit': max_logit,
        'shifted_min': min(shifted),
    }


def _approx_exp_pwl(shifted_logit: float) -> float:
    x = float(shifted_logit)
    if x >= 0.0:
        return 1.0
    if x <= -8.0:
        return 0.0
    anchors = [
        (-8.0, math.exp(-8.0)),
        (-4.0, math.exp(-4.0)),
        (-2.0, math.exp(-2.0)),
        (0.0, 1.0),
    ]
    for (x0, y0), (x1, y1) in zip(anchors[:-1], anchors[1:]):
        if x0 <= x <= x1:
            t = (x - x0) / (x1 - x0)
            return y0 + t * (y1 - y0)
    return 0.0


def _softmax_approx_pwl(logits: Sequence[float]) -> Tuple[list[float], JsonDict]:
    values = [float(v) for v in logits]
    if not values:
        raise SystemExit('softmax_approx_pwl received empty logits')
    max_logit = max(values)
    shifted = [value - max_logit for value in values]
    weights = [_approx_exp_pwl(value) for value in shifted]
    return weights, {
        'mode': 'softmax_approx_pwl',
        'max_logit': max_logit,
        'shifted_min': min(shifted),
        'anchors': [-8.0, -4.0, -2.0, 0.0],
    }


def _normalize_exact(weights: Sequence[float]) -> Tuple[list[float], JsonDict]:
    values = [max(0.0, float(v)) for v in weights]
    total = sum(values)
    if total <= 0.0:
        raise SystemExit('normalize_exact received zero total weight')
    return [value / total for value in values], {
        'mode': 'normalize_exact',
        'sum_weights': total,
    }


def _normalize_reciprocal_quantized(weights: Sequence[float], *, reciprocal_bits: int) -> Tuple[list[float], JsonDict]:
    if reciprocal_bits < 2:
        raise SystemExit('backend_config.normalization_reciprocal_bits must be >= 2')
    values = [max(0.0, float(v)) for v in weights]
    total = sum(values)
    if total <= 0.0:
        raise SystemExit('normalize_reciprocal_quantized received zero total weight')
    reciprocal = 1.0 / total
    mantissa, exponent = math.frexp(reciprocal)
    levels = (1 << reciprocal_bits) - 1
    mantissa_q = round(mantissa * levels) / float(levels)
    reciprocal_q = math.ldexp(mantissa_q, exponent)
    return [value * reciprocal_q for value in values], {
        'mode': 'normalize_reciprocal_quantized',
        'sum_weights': total,
        'reciprocal_bits': reciprocal_bits,
        'reciprocal': reciprocal,
        'reciprocal_quantized': reciprocal_q,
        'mantissa': mantissa,
        'mantissa_quantized': mantissa_q,
        'exponent': exponent,
    }


def _quantize_probabilities_unsigned(probabilities: Sequence[float], *, bits: int) -> Tuple[list[float], JsonDict]:
    if bits < 2:
        raise SystemExit('backend_config.probability_quant_bits must be >= 2')
    values = [max(0.0, min(1.0, float(v))) for v in probabilities]
    levels = (1 << bits) - 1
    quantized = [round(value * levels) / float(levels) for value in values]
    return quantized, {
        'mode': 'unsigned_probability_quant',
        'bits': bits,
        'levels': levels,
    }


def _apply_logit_path(logits: Sequence[float], backend_config: JsonDict) -> Tuple[list[float], JsonDict]:
    bits = int(backend_config.get('logit_quant_bits', 0) or 0)
    if bits > 0:
        return _quantize_logits_symmetric(logits, bits=bits)
    return [float(v) for v in logits], {
        'mode': 'identity_logits',
    }


def _apply_softmax_path(logits: Sequence[float], backend_config: JsonDict) -> Tuple[list[float], JsonDict]:
    mode = str(backend_config.get('softmax_mode', 'exact'))
    if mode == 'exact':
        return _softmax_exact(logits)
    if mode == 'approx_pwl':
        return _softmax_approx_pwl(logits)
    raise SystemExit(f'unsupported backend_config.softmax_mode: {mode}')


def _apply_normalization_path(weights: Sequence[float], backend_config: JsonDict) -> Tuple[list[float], JsonDict]:
    mode = str(backend_config.get('normalization_mode', 'exact'))
    if mode == 'exact':
        return _normalize_exact(weights)
    if mode == 'reciprocal_quantized':
        reciprocal_bits = int(backend_config.get('normalization_reciprocal_bits', 10))
        return _normalize_reciprocal_quantized(weights, reciprocal_bits=reciprocal_bits)
    raise SystemExit(f'unsupported backend_config.normalization_mode: {mode}')


def _apply_probability_quantization(probabilities: Sequence[float], backend_config: JsonDict) -> Tuple[list[float], JsonDict]:
    bits = int(backend_config.get('probability_quant_bits', 0) or 0)
    if bits > 0:
        return _quantize_probabilities_unsigned(probabilities, bits=bits)
    return [float(v) for v in probabilities], {
        'mode': 'identity_probabilities',
    }


def _derive_candidate_semantics(backend_config: JsonDict) -> str:
    if str(backend_config.get('candidate_semantics', '')).strip():
        return str(backend_config['candidate_semantics'])
    parts = ['onnx']
    logit_bits = int(backend_config.get('logit_quant_bits', 0) or 0)
    parts.append(f'logits_q{logit_bits}' if logit_bits > 0 else 'logits_fp')
    softmax_mode = str(backend_config.get('softmax_mode', 'exact'))
    parts.append(f'softmax_{softmax_mode}')
    norm_mode = str(backend_config.get('normalization_mode', 'exact'))
    if norm_mode == 'reciprocal_quantized':
        norm_bits = int(backend_config.get('normalization_reciprocal_bits', 10))
        parts.append(f'norm_recip_q{norm_bits}')
    else:
        parts.append(f'norm_{norm_mode}')
    prob_bits = int(backend_config.get('probability_quant_bits', 0) or 0)
    parts.append(f'prob_q{prob_bits}' if prob_bits > 0 else 'prob_fp')
    return '_'.join(parts)


def _build_result(*, request: JsonDict, vocab: Dict[str, int], next_token_id: int, scores: Sequence[float], topk: int, tokenizer_runtime: Any | None = None, prompt_doc: JsonDict, ort_version: str, approximation: JsonDict, candidate_semantics: str) -> JsonDict:
    backend_config = request['backend_config']
    next_token_text = _decode_token(next_token_id, vocab, tokenizer_runtime=tokenizer_runtime)
    topk_pairs = list(_topk_pairs(scores, k=topk))
    top_score = float(topk_pairs[0][1]) if topk_pairs else float(scores[next_token_id])
    runner = {
        'runner': 'onnx_candidate_v1',
        'runtime_target': backend_config.get('runtime_target', 'software_emulation'),
        'library': 'onnxruntime',
        'onnxruntime_version': ort_version,
        'score_rank': 1,
        'approximation': approximation,
    }
    return {
        'prompt': prompt_doc,
        'candidate': {
            'next_token_text': next_token_text,
            'next_token_id': next_token_id,
            'confidence': top_score,
            'topk': [
                {
                    'token_id': token_id,
                    'token_text': _decode_token(token_id, vocab, tokenizer_runtime=tokenizer_runtime),
                    'score': score,
                }
                for token_id, score in topk_pairs
            ],
        },
        'candidate_semantics': candidate_semantics,
        'backend_runtime': runner,
        'notes': 'ONNX Runtime decoder candidate runner result using explicit softmax and normalization paths.',
    }


def main() -> int:
    request = _load_request()
    backend_config = dict(request.get('backend_config', {}))
    if str(request.get('role', '')) != 'candidate':
        raise SystemExit('run_llm_decoder_onnx_candidate.py only supports role=candidate')

    tokenizer_manifest_path = _resolve_repo_path(request['paths']['tokenizer_manifest_path'])
    tokenizer_manifest = load_json(tokenizer_manifest_path)
    tokenizer_bundle = load_tokenizer_bundle(tokenizer_manifest, manifest_path=tokenizer_manifest_path)
    vocab = dict(tokenizer_bundle['vocab'])
    tokenizer_runtime = _load_tokenizer_runtime(tokenizer_bundle)
    prompt_doc = _prepare_prompt(request['sample'], tokenizer_bundle, tokenizer_runtime=tokenizer_runtime)

    ort = _load_onnxruntime()
    model_path = str(backend_config.get('onnx_model_path', '')).strip()
    if not model_path:
        raise SystemExit('backend_config.onnx_model_path is required for command_json_v1 ONNX candidate runs')
    output_name = str(backend_config.get('output_name', '')).strip() or None
    topk = int(backend_config.get('topk', 5))
    candidate_semantics = _derive_candidate_semantics(backend_config)
    model_config = _load_model_config(model_path=model_path, backend_config=backend_config)
    feeds = _build_feeds(prompt_token_ids=prompt_doc['token_ids'], model_config=model_config)

    sess = ort.InferenceSession(str(_resolve_repo_path(model_path)))
    outputs = sess.run([output_name] if output_name else None, feeds)
    if not outputs:
        raise SystemExit('onnx runtime returned no outputs')
    logits = _extract_next_token_logits(outputs[0])
    logit_values, logit_meta = _apply_logit_path(logits, backend_config)
    softmax_weights, softmax_meta = _apply_softmax_path(logit_values, backend_config)
    normalized_probs, normalization_meta = _apply_normalization_path(softmax_weights, backend_config)
    score_values, probability_meta = _apply_probability_quantization(normalized_probs, backend_config)
    next_token_id = max(range(len(score_values)), key=lambda idx: float(score_values[idx]))
    result = _build_result(
        request=request,
        vocab=vocab,
        next_token_id=next_token_id,
        scores=score_values,
        topk=topk,
        tokenizer_runtime=tokenizer_runtime,
        prompt_doc=prompt_doc,
        ort_version=str(ort.__version__),
        approximation={
            'logits': logit_meta,
            'softmax': softmax_meta,
            'normalization': normalization_meta,
            'probabilities': probability_meta,
        },
        candidate_semantics=candidate_semantics,
    )
    json.dump(result, sys.stdout)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
