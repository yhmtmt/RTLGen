#!/usr/bin/env python3
"""Run a decoder next-token candidate step from a command_json_v1 request.

This runner is the first approximation-aware candidate side for decoder-quality
evaluation. It shares the exact tokenizer/model contract with the ONNX reference
runner, then applies a deterministic approximation to the logits before argmax.
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
    _topk_pairs,
)
from npu.eval.llm_decoder_quality import load_json, load_tokenizer_bundle

JsonDict = Dict[str, Any]


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


def _build_result(*, request: JsonDict, vocab: Dict[str, int], next_token_id: int, logits: Sequence[float], topk: int, tokenizer_runtime: Any | None = None, prompt_doc: JsonDict, ort_version: str, approximation: JsonDict, candidate_semantics: str) -> JsonDict:
    backend_config = request['backend_config']
    next_token_text = _decode_token(next_token_id, vocab, tokenizer_runtime=tokenizer_runtime)
    topk_pairs = list(_topk_pairs(logits, k=topk))
    top_logit = float(topk_pairs[0][1]) if topk_pairs else float(logits[next_token_id])
    runner = {
        'runner': 'onnx_candidate_v1',
        'runtime_target': backend_config.get('runtime_target', 'software_emulation'),
        'library': 'onnxruntime',
        'onnxruntime_version': ort_version,
        'logits_rank': 1,
        'approximation': approximation,
    }
    return {
        'prompt': prompt_doc,
        'candidate': {
            'next_token_text': next_token_text,
            'next_token_id': next_token_id,
            'confidence': top_logit,
            'topk': [
                {
                    'token_id': token_id,
                    'token_text': _decode_token(token_id, vocab, tokenizer_runtime=tokenizer_runtime),
                    'logit': logit,
                }
                for token_id, logit in topk_pairs
            ],
        },
        'candidate_semantics': candidate_semantics,
        'backend_runtime': runner,
        'notes': 'ONNX Runtime decoder candidate runner result using quantized logits.',
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
    bits = int(backend_config.get('logit_quant_bits', 4))
    candidate_semantics = str(backend_config.get('candidate_semantics', f'onnx_logits_symmetric_quant_q{bits}'))
    model_config = _load_model_config(model_path=model_path, backend_config=backend_config)
    feeds = _build_feeds(prompt_token_ids=prompt_doc['token_ids'], model_config=model_config)

    sess = ort.InferenceSession(str(_resolve_repo_path(model_path)))
    outputs = sess.run([output_name] if output_name else None, feeds)
    if not outputs:
        raise SystemExit('onnx runtime returned no outputs')
    logits = _extract_next_token_logits(outputs[0])
    approx_logits, approximation = _quantize_logits_symmetric(logits, bits=bits)
    next_token_id = max(range(len(approx_logits)), key=lambda idx: float(approx_logits[idx]))
    result = _build_result(
        request=request,
        vocab=vocab,
        next_token_id=next_token_id,
        logits=approx_logits,
        topk=topk,
        tokenizer_runtime=tokenizer_runtime,
        prompt_doc=prompt_doc,
        ort_version=str(ort.__version__),
        approximation=approximation,
        candidate_semantics=candidate_semantics,
    )
    json.dump(result, sys.stdout)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
