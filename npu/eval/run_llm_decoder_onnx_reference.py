#!/usr/bin/env python3
"""Run a decoder next-token reference step from a command_json_v1 request.

This runner is the exact-reference side for decoder-quality evaluation.
It is intentionally external to `decoder_backend.py`: the backend adapter only
speaks JSON over stdin/stdout, while this script owns the ONNX Runtime-specific
execution details.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.eval.llm_decoder_quality import (
    encode_tokens_for_bundle,
    load_json,
    load_tokenizer_bundle,
    tokenize_decoder_text,
)

JsonDict = Dict[str, Any]


def _resolve_repo_path(path: str | Path) -> Path:
    p = Path(path)
    if p.is_absolute():
        return p
    return REPO_ROOT / p


def _load_request() -> JsonDict:
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        raise SystemExit(f'invalid command_json_v1 request: {exc}')


def _load_onnxruntime():
    try:
        import onnxruntime as ort  # type: ignore
    except ModuleNotFoundError as exc:
        raise SystemExit(
            'onnxruntime is not installed; this runner is scaffolded but not usable until the runtime is pinned'
        ) from exc
    return ort


def _to_nested_list(raw_output: Any) -> Any:
    if hasattr(raw_output, 'tolist'):
        return raw_output.tolist()
    return raw_output


def _infer_rank(value: Any) -> int:
    rank = 0
    cur = value
    while isinstance(cur, (list, tuple)):
        rank += 1
        cur = cur[0] if cur else []
    return rank


def _extract_next_token_logits(raw_output: Any) -> list[float]:
    value = _to_nested_list(raw_output)
    rank = _infer_rank(value)
    if rank == 1:
        return [float(v) for v in value]
    if rank == 2:
        return [float(v) for v in value[-1]]
    if rank == 3:
        return [float(v) for v in value[0][-1]]
    raise ValueError(f'unsupported logits rank: {rank}')


def _topk_pairs(logits: Sequence[float], *, k: int) -> Iterable[Tuple[int, float]]:
    if k <= 0:
        return []
    order = sorted(range(len(logits)), key=lambda idx: float(logits[idx]), reverse=True)[:k]
    return [(int(idx), float(logits[idx])) for idx in order]


def _decode_token(token_id: int, vocab: Dict[str, int]) -> str:
    inv_vocab = {idx: token for token, idx in vocab.items()}
    if token_id not in inv_vocab:
        raise ValueError(f'token id not present in vocab: {token_id}')
    return inv_vocab[token_id]


def _prepare_input_ids(sample: JsonDict, tokenizer_bundle: JsonDict) -> list[list[int]]:
    prompt = str(sample['prompt'])
    try:
        prompt_tokens = tokenize_decoder_text(prompt, tokenizer_bundle)
    except ValueError as exc:
        raise SystemExit(f'unsupported tokenizer for ONNX reference runner: {exc}') from exc
    prompt_token_ids = encode_tokens_for_bundle(prompt_tokens, tokenizer_bundle, allow_unk=True)
    return [prompt_token_ids]


def _build_result(*, request: JsonDict, vocab: Dict[str, int], next_token_id: int, logits: Sequence[float], topk: int) -> JsonDict:
    sample = request['sample']
    backend_config = request['backend_config']
    next_token_text = _decode_token(next_token_id, vocab)
    topk_pairs = list(_topk_pairs(logits, k=topk))
    return {
        'decode_policy': {
            'strategy': 'greedy',
            'max_new_tokens': 1,
        },
        'reference': {
            'expected_continuation': str(sample.get('expected_continuation', next_token_text)),
            'next_token_text': next_token_text,
            'next_token_id': next_token_id,
            'next_token_rank': 1,
            'selected_tensors': [],
            'topk': [
                {
                    'token_id': token_id,
                    'token_text': _decode_token(token_id, vocab),
                    'logit': logit,
                }
                for token_id, logit in topk_pairs
            ],
        },
        'backend_runtime': {
            'runner': 'onnx_reference_v1',
            'runtime_target': backend_config.get('runtime_target', 'cpu_reference'),
            'logits_rank': 1,
        },
        'notes': 'ONNX Runtime decoder reference runner result.',
    }


def main() -> int:
    request = _load_request()
    backend_config = dict(request.get('backend_config', {}))
    if str(request.get('role', '')) != 'reference':
        raise SystemExit('run_llm_decoder_onnx_reference.py only supports role=reference')

    tokenizer_manifest_path = _resolve_repo_path(request['paths']['tokenizer_manifest_path'])
    tokenizer_manifest = load_json(tokenizer_manifest_path)
    tokenizer_bundle = load_tokenizer_bundle(tokenizer_manifest, manifest_path=tokenizer_manifest_path)
    vocab = dict(tokenizer_bundle['vocab'])

    input_ids = _prepare_input_ids(request['sample'], tokenizer_bundle)
    ort = _load_onnxruntime()

    model_path = str(backend_config.get('onnx_model_path', '')).strip()
    if not model_path:
        raise SystemExit('backend_config.onnx_model_path is required for command_json_v1 ONNX reference runs')
    input_name = str(backend_config.get('input_name', 'input_ids'))
    output_name = str(backend_config.get('output_name', '')).strip() or None
    topk = int(backend_config.get('topk', 5))

    sess = ort.InferenceSession(str(_resolve_repo_path(model_path)))
    outputs = sess.run([output_name] if output_name else None, {input_name: input_ids})
    if not outputs:
        raise SystemExit('onnx runtime returned no outputs')
    logits = _extract_next_token_logits(outputs[0])
    next_token_id = max(range(len(logits)), key=lambda idx: float(logits[idx]))
    result = _build_result(
        request=request,
        vocab=vocab,
        next_token_id=next_token_id,
        logits=logits,
        topk=topk,
    )
    json.dump(result, sys.stdout)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
