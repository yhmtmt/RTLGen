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
    _build_output_map,
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
from npu.eval.tensor_trace_summary import (
    matches_trace_pattern as _matches_trace_pattern,
    selected_tensor_trace_hash as _selected_tensor_trace_hash,
    tensor_summary as _tensor_summary,
)

JsonDict = Dict[str, Any]


def _topk_pairs(values: Sequence[float], *, k: int) -> Iterable[Tuple[int, float]]:
    if k <= 0:
        return []
    order = sorted(range(len(values)), key=lambda idx: float(values[idx]), reverse=True)[:k]
    return [(int(idx), float(values[idx])) for idx in order]


def _score_distribution_stats(scores: Sequence[float], *, topk: int) -> JsonDict:
    values = [max(0.0, float(v)) for v in scores]
    if not values:
        raise SystemExit('distribution stats received empty scores')
    order = sorted(range(len(values)), key=lambda idx: values[idx], reverse=True)
    top1 = values[order[0]]
    top2 = values[order[1]] if len(order) > 1 else top1
    total = sum(values)
    normalized = [value / total for value in values] if total > 0.0 else [0.0 for _ in values]
    entropy = -sum(prob * math.log(prob) for prob in normalized if prob > 0.0)
    top_count = max(1, min(int(topk), len(values)))
    top_indices = order[:top_count]
    top_scores = [values[idx] for idx in top_indices]
    return {
        'vocab_size': len(values),
        'score_sum': total,
        'nonzero_score_count': sum(1 for value in values if value > 0.0),
        'entropy_nats': entropy,
        'effective_vocab_size': math.exp(entropy),
        'top1_score': top1,
        'top2_score': top2,
        'top1_top2_score_margin': top1 - top2,
        'top1_probability': normalized[order[0]],
        'top2_probability': normalized[order[1]] if len(order) > 1 else normalized[order[0]],
        'topk_score_mass': sum(top_scores),
    }


def _quantize_symmetric(values: Sequence[float], *, bits: int, mode: str) -> Tuple[list[float], JsonDict]:
    if bits < 2:
        raise SystemExit(f'{mode} bits must be >= 2')
    quant_values = [float(v) for v in values]
    if not quant_values:
        raise SystemExit(f'{mode} received empty values')
    max_abs = max(abs(v) for v in quant_values)
    levels = (1 << (bits - 1)) - 1
    if max_abs == 0.0 or levels <= 0:
        return list(quant_values), {
            'mode': mode,
            'bits': bits,
            'levels': levels,
            'scale': 1.0,
            'max_abs': max_abs,
        }
    scale = max_abs / float(levels)
    quantized = []
    for value in quant_values:
        q = int(round(value / scale))
        q = max(-levels, min(levels, q))
        quantized.append(float(q) * scale)
    return quantized, {
        'mode': mode,
        'bits': bits,
        'levels': levels,
        'scale': scale,
        'max_abs': max_abs,
    }


def _quantize_logits_symmetric(logits: Sequence[float], *, bits: int) -> Tuple[list[float], JsonDict]:
    return _quantize_symmetric(logits, bits=bits, mode='symmetric_logit_quant')


_FLOAT_FORMATS: dict[str, tuple[int, int]] = {
    'fp16': (5, 10),
    'bf16': (8, 7),
    'fp8_e4m3': (4, 3),
    'fp8_e5m2': (5, 2),
}


def _quantize_float_like(values: Sequence[float], *, format_name: str, mode: str) -> Tuple[list[float], JsonDict]:
    fmt = str(format_name).strip().lower()
    if fmt not in _FLOAT_FORMATS:
        raise SystemExit(f'unsupported {mode} float format: {format_name}')
    exponent_bits, mantissa_bits = _FLOAT_FORMATS[fmt]
    exponent_bias = (1 << (exponent_bits - 1)) - 1
    min_normal_exp = 1 - exponent_bias
    max_exp = ((1 << exponent_bits) - 2) - exponent_bias
    max_finite = (2.0 - (2.0 ** (-mantissa_bits))) * (2.0 ** max_exp)
    min_subnormal = 2.0 ** (min_normal_exp - mantissa_bits)
    quantized: list[float] = []
    underflow_count = 0
    overflow_count = 0
    for raw in values:
        value = float(raw)
        if value == 0.0:
            quantized.append(0.0)
            continue
        if not math.isfinite(value):
            quantized.append(value)
            continue
        sign = -1.0 if value < 0.0 else 1.0
        ax = abs(value)
        if ax < min_subnormal / 2.0:
            quantized.append(0.0)
            underflow_count += 1
            continue
        if ax > max_finite:
            quantized.append(sign * max_finite)
            overflow_count += 1
            continue
        exponent = math.floor(math.log2(ax))
        if exponent < min_normal_exp:
            subnormal_steps = int(round(ax / min_subnormal))
            quantized.append(sign * float(subnormal_steps) * min_subnormal)
            continue
        significand = ax / (2.0 ** exponent)
        fraction = significand - 1.0
        fraction_steps = int(round(fraction * (1 << mantissa_bits)))
        if fraction_steps == (1 << mantissa_bits):
            fraction_steps = 0
            exponent += 1
        if exponent > max_exp:
            quantized.append(sign * max_finite)
            overflow_count += 1
            continue
        quantized.append(sign * (1.0 + fraction_steps / float(1 << mantissa_bits)) * (2.0 ** exponent))
    return quantized, {
        'mode': mode,
        'format': fmt,
        'exponent_bits': exponent_bits,
        'mantissa_bits': mantissa_bits,
        'min_subnormal': min_subnormal,
        'max_finite': max_finite,
        'underflow_count': underflow_count,
        'overflow_count': overflow_count,
    }


def _quantize_unsigned(values: Sequence[float], *, bits: int, mode: str) -> Tuple[list[float], JsonDict]:
    if bits < 2:
        raise SystemExit(f'{mode} bits must be >= 2')
    quant_values = [max(0.0, float(v)) for v in values]
    if not quant_values:
        raise SystemExit(f'{mode} received empty values')
    max_value = max(quant_values)
    levels = (1 << bits) - 1
    if max_value == 0.0 or levels <= 0:
        return list(quant_values), {
            'mode': mode,
            'bits': bits,
            'levels': levels,
            'scale': 1.0,
            'max_value': max_value,
        }
    scale = max_value / float(levels)
    quantized = []
    for value in quant_values:
        q = int(round(value / scale))
        q = max(0, min(levels, q))
        quantized.append(float(q) * scale)
    return quantized, {
        'mode': mode,
        'bits': bits,
        'levels': levels,
        'scale': scale,
        'max_value': max_value,
    }


def _softmax_exact(logits: Sequence[float], *, input_float_format: str = '', weight_float_format: str = '') -> Tuple[list[float], JsonDict]:
    values = [float(v) for v in logits]
    if not values:
        raise SystemExit('softmax_exact received empty logits')
    max_logit = max(values)
    shifted = [value - max_logit for value in values]
    shifted_used = list(shifted)
    input_float = None
    if input_float_format:
        shifted_used, input_float = _quantize_float_like(
            shifted_used,
            format_name=input_float_format,
            mode='softmax_input_float_quant',
        )
    weights = [math.exp(value) for value in shifted_used]
    weights_used = list(weights)
    weight_float = None
    if weight_float_format:
        weights_used, weight_float = _quantize_float_like(
            weights_used,
            format_name=weight_float_format,
            mode='softmax_weight_float_quant',
        )
    return weights_used, {
        'mode': 'softmax_exact',
        'max_logit': max_logit,
        'shifted_min': min(shifted),
        'input_float_quant': input_float,
        'weight_float_quant': weight_float,
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


def _softmax_approx_pwl(logits: Sequence[float], *, input_quant_bits: int = 0, weight_quant_bits: int = 0, input_float_format: str = '', weight_float_format: str = '') -> Tuple[list[float], JsonDict]:
    values = [float(v) for v in logits]
    if not values:
        raise SystemExit('softmax_approx_pwl received empty logits')
    max_logit = max(values)
    shifted = [value - max_logit for value in values]
    shifted_used = list(shifted)
    input_quant = None
    input_float = None
    if input_float_format:
        shifted_used, input_float = _quantize_float_like(
            shifted_used,
            format_name=input_float_format,
            mode='softmax_input_float_quant',
        )
    if input_quant_bits > 0:
        shifted_used, input_quant = _quantize_symmetric(
            shifted_used,
            bits=input_quant_bits,
            mode='softmax_input_quant',
        )
    weights = [_approx_exp_pwl(value) for value in shifted_used]
    weights_used = list(weights)
    weight_quant = None
    weight_float = None
    if weight_float_format:
        weights_used, weight_float = _quantize_float_like(
            weights_used,
            format_name=weight_float_format,
            mode='softmax_weight_float_quant',
        )
    if weight_quant_bits > 0:
        weights_used, weight_quant = _quantize_unsigned(
            weights_used,
            bits=weight_quant_bits,
            mode='softmax_weight_quant',
        )
    return weights_used, {
        'mode': 'softmax_approx_pwl',
        'max_logit': max_logit,
        'shifted_min': min(shifted),
        'anchors': [-8.0, -4.0, -2.0, 0.0],
        'input_quant': input_quant,
        'input_float_quant': input_float,
        'weight_quant': weight_quant,
        'weight_float_quant': weight_float,
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


def _normalize_reciprocal_float(weights: Sequence[float], *, float_format: str) -> Tuple[list[float], JsonDict]:
    values = [max(0.0, float(v)) for v in weights]
    total = sum(values)
    if total <= 0.0:
        raise SystemExit('normalize_reciprocal_float received zero total weight')
    reciprocal = 1.0 / total
    reciprocal_values, quant = _quantize_float_like(
        [reciprocal],
        format_name=float_format,
        mode='normalization_reciprocal_float_quant',
    )
    reciprocal_q = reciprocal_values[0]
    return [value * reciprocal_q for value in values], {
        'mode': 'normalize_reciprocal_float',
        'sum_weights': total,
        'reciprocal': reciprocal,
        'reciprocal_quantized': reciprocal_q,
        'reciprocal_float_quant': quant,
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
    logit_values = [float(v) for v in logits]
    transforms: list[JsonDict] = []
    bits = int(backend_config.get('logit_quant_bits', 0) or 0)
    if bits > 0:
        logit_values, meta = _quantize_logits_symmetric(logit_values, bits=bits)
        transforms.append(meta)
    fmt = str(backend_config.get('logit_float_format', '') or '').strip()
    if fmt:
        logit_values, meta = _quantize_float_like(logit_values, format_name=fmt, mode='logit_float_quant')
        transforms.append(meta)
    if transforms:
        return logit_values, {'mode': 'logit_transform_chain', 'transforms': transforms}
    return logit_values, {'mode': 'identity_logits'}


def _apply_softmax_path(logits: Sequence[float], backend_config: JsonDict) -> Tuple[list[float], JsonDict]:
    mode = str(backend_config.get('softmax_mode', 'exact'))
    input_float_format = str(backend_config.get('softmax_input_float_format', '') or '').strip()
    weight_float_format = str(backend_config.get('softmax_weight_float_format', '') or '').strip()
    if mode == 'exact':
        return _softmax_exact(
            logits,
            input_float_format=input_float_format,
            weight_float_format=weight_float_format,
        )
    if mode == 'approx_pwl':
        input_quant_bits = int(backend_config.get('softmax_input_quant_bits', 0) or 0)
        weight_quant_bits = int(backend_config.get('softmax_weight_quant_bits', 0) or 0)
        return _softmax_approx_pwl(
            logits,
            input_quant_bits=input_quant_bits,
            weight_quant_bits=weight_quant_bits,
            input_float_format=input_float_format,
            weight_float_format=weight_float_format,
        )
    raise SystemExit(f'unsupported backend_config.softmax_mode: {mode}')


def _apply_normalization_path(weights: Sequence[float], backend_config: JsonDict) -> Tuple[list[float], JsonDict]:
    mode = str(backend_config.get('normalization_mode', 'exact'))
    if mode == 'exact':
        return _normalize_exact(weights)
    if mode == 'reciprocal_quantized':
        reciprocal_bits = int(backend_config.get('normalization_reciprocal_bits', 10))
        return _normalize_reciprocal_quantized(weights, reciprocal_bits=reciprocal_bits)
    if mode == 'reciprocal_float':
        fmt = str(backend_config.get('normalization_reciprocal_float_format', '') or '').strip()
        if not fmt:
            raise SystemExit('backend_config.normalization_reciprocal_float_format is required for reciprocal_float')
        return _normalize_reciprocal_float(weights, float_format=fmt)
    raise SystemExit(f'unsupported backend_config.normalization_mode: {mode}')


def _apply_probability_quantization(probabilities: Sequence[float], backend_config: JsonDict) -> Tuple[list[float], JsonDict]:
    bits = int(backend_config.get('probability_quant_bits', 0) or 0)
    if bits > 0:
        return _quantize_probabilities_unsigned(probabilities, bits=bits)
    fmt = str(backend_config.get('probability_float_format', '') or '').strip()
    if fmt:
        return _quantize_float_like(probabilities, format_name=fmt, mode='probability_float_quant')
    return [float(v) for v in probabilities], {
        'mode': 'identity_probabilities',
    }


def _quantize_tensor_trace_symmetric(raw_output: Any, *, bits: int) -> Tuple[Any, JsonDict]:
    import numpy as np

    if bits < 2:
        raise SystemExit('backend_config.trace_tensor_quant_bits must be >= 2')
    array = np.asarray(raw_output, dtype=np.float32)
    flat = array.reshape(-1)
    quantized, meta = _quantize_symmetric(flat.tolist(), bits=bits, mode='trace_tensor_quant')
    return np.asarray(quantized, dtype=np.float32).reshape(array.shape), meta


def _trace_selected_outputs_candidate(*, outputs_by_name: JsonDict, trace_patterns: Sequence[str], step: int, trace_tensor_quant_bits: int = 0) -> list[JsonDict]:
    if not trace_patterns:
        return []
    traced: list[JsonDict] = []
    for name in sorted(outputs_by_name):
        if _matches_trace_pattern(name, trace_patterns):
            raw_output = outputs_by_name[name]
            quantization = None
            if trace_tensor_quant_bits > 0:
                raw_output, quantization = _quantize_tensor_trace_symmetric(raw_output, bits=trace_tensor_quant_bits)
            traced.append(_tensor_summary(raw_output, name=name, step=step, quantization=quantization))
    return traced


def _derive_candidate_semantics(backend_config: JsonDict) -> str:
    if str(backend_config.get('candidate_semantics', '')).strip():
        return str(backend_config['candidate_semantics'])
    parts = ['onnx']
    logit_bits = int(backend_config.get('logit_quant_bits', 0) or 0)
    logit_float_format = str(backend_config.get('logit_float_format', '') or '').strip()
    if logit_bits > 0:
        parts.append(f'logits_q{logit_bits}')
    elif logit_float_format:
        parts.append(f'logits_{logit_float_format}')
    else:
        parts.append('logits_fp')
    softmax_mode = str(backend_config.get('softmax_mode', 'exact'))
    parts.append(f'softmax_{softmax_mode}')
    softmax_input_bits = int(backend_config.get('softmax_input_quant_bits', 0) or 0)
    if softmax_input_bits > 0:
        parts.append(f'in_q{softmax_input_bits}')
    softmax_input_float = str(backend_config.get('softmax_input_float_format', '') or '').strip()
    if softmax_input_float:
        parts.append(f'in_{softmax_input_float}')
    softmax_weight_bits = int(backend_config.get('softmax_weight_quant_bits', 0) or 0)
    if softmax_weight_bits > 0:
        parts.append(f'w_q{softmax_weight_bits}')
    softmax_weight_float = str(backend_config.get('softmax_weight_float_format', '') or '').strip()
    if softmax_weight_float:
        parts.append(f'w_{softmax_weight_float}')
    norm_mode = str(backend_config.get('normalization_mode', 'exact'))
    if norm_mode == 'reciprocal_quantized':
        norm_bits = int(backend_config.get('normalization_reciprocal_bits', 10))
        parts.append(f'norm_recip_q{norm_bits}')
    elif norm_mode == 'reciprocal_float':
        norm_float = str(backend_config.get('normalization_reciprocal_float_format', '') or '').strip()
        parts.append(f'norm_recip_{norm_float}' if norm_float else 'norm_recip_float')
    else:
        parts.append(f'norm_{norm_mode}')
    prob_bits = int(backend_config.get('probability_quant_bits', 0) or 0)
    prob_float = str(backend_config.get('probability_float_format', '') or '').strip()
    if prob_bits > 0:
        parts.append(f'prob_q{prob_bits}')
    elif prob_float:
        parts.append(f'prob_{prob_float}')
    else:
        parts.append('prob_fp')
    return '_'.join(parts)


def _build_result(*, request: JsonDict, vocab: Dict[str, int], next_token_id: int, scores: Sequence[float], topk: int, tokenizer_runtime: Any | None = None, prompt_doc: JsonDict, ort_version: str, approximation: JsonDict, candidate_semantics: str, selected_tensors: Sequence[JsonDict] | None = None) -> JsonDict:
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
            'distribution': _score_distribution_stats(scores, topk=topk),
            'selected_tensors': list(selected_tensors or []),
            'selected_tensors_sha256': _selected_tensor_trace_hash(selected_tensors),
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

    model_path = str(backend_config.get('onnx_model_path', '')).strip()
    if not model_path:
        raise SystemExit('backend_config.onnx_model_path is required for command_json_v1 ONNX candidate runs')
    resolved_model_path = _resolve_repo_path(model_path)
    if not resolved_model_path.is_file():
        raise SystemExit(f'NoSuchFile: ONNX model path does not exist: {resolved_model_path}')
    output_name = str(backend_config.get('output_name', '')).strip() or None
    topk = int(backend_config.get('topk', 5))
    trace_patterns = [str(v) for v in (backend_config.get('trace_output_patterns') or []) if str(v).strip()]
    trace_tensor_quant_bits = int(backend_config.get('trace_tensor_quant_bits', 0) or 0)
    candidate_semantics = _derive_candidate_semantics(backend_config)
    model_config = _load_model_config(model_path=model_path, backend_config=backend_config)
    feeds = _build_feeds(prompt_token_ids=prompt_doc['token_ids'], model_config=model_config)

    ort = _load_onnxruntime()
    sess = ort.InferenceSession(str(resolved_model_path))
    outputs = sess.run(None, feeds)
    if not outputs:
        raise SystemExit('onnx runtime returned no outputs')
    outputs_by_name = _build_output_map(sess=sess, outputs=outputs)
    logits_name = output_name or 'logits'
    if logits_name not in outputs_by_name:
        raise SystemExit(f'onnx runtime did not return requested logits output: {logits_name}')
    logits = _extract_next_token_logits(outputs_by_name[logits_name])
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
        selected_tensors=_trace_selected_outputs_candidate(
            outputs_by_name=outputs_by_name,
            trace_patterns=trace_patterns,
            step=0,
            trace_tensor_quant_bits=trace_tensor_quant_bits,
        ),
    )
    json.dump(result, sys.stdout)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
