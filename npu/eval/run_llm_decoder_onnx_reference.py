#!/usr/bin/env python3
"""Run a decoder next-token reference step from a command_json_v1 request.

This runner is the exact-reference side for decoder-quality evaluation.
It is intentionally external to `decoder_backend.py`: the backend adapter only
speaks JSON over stdin/stdout, while this script owns the ONNX Runtime-specific
execution details.
"""

from __future__ import annotations

import fnmatch
import hashlib
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


def _load_tokenizers():
    try:
        from tokenizers import Tokenizer  # type: ignore
    except ModuleNotFoundError as exc:
        raise SystemExit('tokenizers is not installed; GPT-2 BPE exact-reference runs are not usable yet') from exc
    return Tokenizer


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


def _build_output_map(*, sess: Any, outputs: Sequence[Any]) -> JsonDict:
    output_defs = list(sess.get_outputs())
    output_names = [str(defn.name) for defn in output_defs]
    if len(output_names) != len(outputs):
        raise ValueError('onnx output count mismatch')
    return {name: value for name, value in zip(output_names, outputs)}


def _matches_trace_pattern(name: str, patterns: Sequence[str]) -> bool:
    return any(fnmatch.fnmatch(name, pattern) for pattern in patterns)


def _tensor_summary(raw_output: Any, *, name: str, step: int, quantization: JsonDict | None = None) -> JsonDict:
    import numpy as np

    array = np.asarray(raw_output, dtype=np.float32)
    summary: JsonDict = {
        'name': name,
        'step': int(step),
        'shape': [int(dim) for dim in array.shape],
        'dtype': str(array.dtype),
        'min': float(array.min()) if array.size else 0.0,
        'max': float(array.max()) if array.size else 0.0,
        'mean': float(array.mean()) if array.size else 0.0,
        'std': float(array.std()) if array.size else 0.0,
    }
    if quantization is not None:
        summary['quantization'] = quantization
    return summary


def _trace_selected_outputs(*, outputs_by_name: JsonDict, trace_patterns: Sequence[str], step: int) -> list[JsonDict]:
    if not trace_patterns:
        return []
    traced: list[JsonDict] = []
    for name in sorted(outputs_by_name):
        if _matches_trace_pattern(name, trace_patterns):
            traced.append(_tensor_summary(outputs_by_name[name], name=name, step=step))
    return traced


def _canonical_json_sha256(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode('utf-8')
    return hashlib.sha256(payload).hexdigest()


def _selected_tensor_trace_hash(selected_tensors: Sequence[JsonDict] | None) -> str:
    return _canonical_json_sha256(list(selected_tensors or []))


def _topk_pairs(logits: Sequence[float], *, k: int) -> Iterable[Tuple[int, float]]:
    if k <= 0:
        return []
    order = sorted(range(len(logits)), key=lambda idx: float(logits[idx]), reverse=True)[:k]
    return [(int(idx), float(logits[idx])) for idx in order]


def _decode_token(token_id: int, vocab: Dict[str, int], *, tokenizer_runtime: Any | None = None) -> str:
    if tokenizer_runtime is not None:
        return str(tokenizer_runtime.decode([int(token_id)]))
    inv_vocab = {idx: token for token, idx in vocab.items()}
    if token_id not in inv_vocab:
        raise ValueError(f'token id not present in vocab: {token_id}')
    return inv_vocab[token_id]


def _load_tokenizer_runtime(tokenizer_bundle: JsonDict):
    kind = str(tokenizer_bundle.get('kind', 'space_prefix_words'))
    if kind == 'space_prefix_words' or kind == 'wordpiece_stub':
        return None
    if kind == 'gpt2_bpe':
        tokenizer_json_path = str(tokenizer_bundle.get('tokenizer_json_path', '')).strip()
        if not tokenizer_json_path:
            raise SystemExit('gpt2_bpe tokenizer bundle is missing tokenizer_json_path')
        Tokenizer = _load_tokenizers()
        return Tokenizer.from_file(tokenizer_json_path)
    raise SystemExit(f'unsupported tokenizer for ONNX reference runner: unsupported tokenizer kind: {kind}')


def _prepare_prompt(sample: JsonDict, tokenizer_bundle: JsonDict, *, tokenizer_runtime: Any | None = None) -> JsonDict:
    prompt = str(sample['prompt'])
    if tokenizer_runtime is not None:
        encoded = tokenizer_runtime.encode(prompt)
        return {
            'text': prompt,
            'tokens': [str(token) for token in encoded.tokens],
            'token_ids': [int(v) for v in encoded.ids],
            'token_count': len(encoded.ids),
        }
    try:
        prompt_tokens = tokenize_decoder_text(prompt, tokenizer_bundle)
    except ValueError as exc:
        raise SystemExit(f'unsupported tokenizer for ONNX reference runner: {exc}') from exc
    prompt_token_ids = encode_tokens_for_bundle(prompt_tokens, tokenizer_bundle, allow_unk=True)
    return {
        'text': prompt,
        'tokens': prompt_tokens,
        'token_ids': prompt_token_ids,
        'token_count': len(prompt_tokens),
    }


def _load_model_config(*, model_path: str, backend_config: JsonDict) -> JsonDict:
    config_path = str(backend_config.get('model_config_path', '')).strip()
    if config_path:
        return load_json(_resolve_repo_path(config_path))
    inferred = _resolve_repo_path(model_path).resolve().parents[1] / 'config.json'
    if inferred.exists():
        return load_json(inferred)
    raise SystemExit('backend_config.model_config_path is required for GPT-2 ONNX reference runs')


def _build_feeds(*, prompt_token_ids: Sequence[int], model_config: JsonDict) -> JsonDict:
    import numpy as np

    batch_size = 1
    seq_len = len(prompt_token_ids)
    if seq_len <= 0:
        raise SystemExit('prompt tokenization produced zero tokens')
    n_layer = int(model_config['n_layer'])
    n_head = int(model_config['n_head'])
    n_embd = int(model_config['n_embd'])
    if n_embd % n_head != 0:
        raise SystemExit('model config has n_embd not divisible by n_head')
    head_dim = n_embd // n_head

    input_ids = np.asarray([list(int(v) for v in prompt_token_ids)], dtype=np.int64)
    attention_mask = np.ones((batch_size, seq_len), dtype=np.int64)
    position_ids = np.arange(seq_len, dtype=np.int64).reshape(1, seq_len)
    feeds: JsonDict = {
        'input_ids': input_ids,
        'attention_mask': attention_mask,
        'position_ids': position_ids,
    }
    for layer_idx in range(n_layer):
        feeds[f'past_key_values.{layer_idx}.key'] = np.zeros((batch_size, n_head, 0, head_dim), dtype=np.float32)
        feeds[f'past_key_values.{layer_idx}.value'] = np.zeros((batch_size, n_head, 0, head_dim), dtype=np.float32)
    return feeds


def _build_result(*, request: JsonDict, vocab: Dict[str, int], next_token_id: int, logits: Sequence[float], topk: int, tokenizer_runtime: Any | None = None, prompt_doc: JsonDict, ort_version: str, selected_tensors: Sequence[JsonDict] | None = None) -> JsonDict:
    sample = request['sample']
    backend_config = request['backend_config']
    next_token_text = _decode_token(next_token_id, vocab, tokenizer_runtime=tokenizer_runtime)
    topk_pairs = list(_topk_pairs(logits, k=topk))
    return {
        'prompt': prompt_doc,
        'reference': {
            'expected_continuation': str(sample.get('expected_continuation', next_token_text)),
            'next_token_text': next_token_text,
            'next_token_id': next_token_id,
            'next_token_rank': 1,
            'selected_tensors': list(selected_tensors or []),
            'selected_tensors_sha256': _selected_tensor_trace_hash(selected_tensors),
            'topk': [
                {
                    'token_id': token_id,
                    'token_text': _decode_token(token_id, vocab, tokenizer_runtime=tokenizer_runtime),
                    'logit': logit,
                }
                for token_id, logit in topk_pairs
            ],
        },
        'backend_runtime': {
            'runner': 'onnx_reference_v1',
            'runtime_target': backend_config.get('runtime_target', 'cpu_reference'),
            'library': 'onnxruntime',
            'onnxruntime_version': ort_version,
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
    tokenizer_runtime = _load_tokenizer_runtime(tokenizer_bundle)
    prompt_doc = _prepare_prompt(request['sample'], tokenizer_bundle, tokenizer_runtime=tokenizer_runtime)

    ort = _load_onnxruntime()

    model_path = str(backend_config.get('onnx_model_path', '')).strip()
    if not model_path:
        raise SystemExit('backend_config.onnx_model_path is required for command_json_v1 ONNX reference runs')
    output_name = str(backend_config.get('output_name', '')).strip() or None
    topk = int(backend_config.get('topk', 5))
    trace_patterns = [str(v) for v in (backend_config.get('trace_output_patterns') or []) if str(v).strip()]
    model_config = _load_model_config(model_path=model_path, backend_config=backend_config)
    feeds = _build_feeds(prompt_token_ids=prompt_doc['token_ids'], model_config=model_config)

    sess = ort.InferenceSession(str(_resolve_repo_path(model_path)))
    outputs = sess.run(None, feeds)
    if not outputs:
        raise SystemExit('onnx runtime returned no outputs')
    outputs_by_name = _build_output_map(sess=sess, outputs=outputs)
    logits_name = output_name or 'logits'
    if logits_name not in outputs_by_name:
        raise SystemExit(f'onnx runtime did not return requested logits output: {logits_name}')
    logits = _extract_next_token_logits(outputs_by_name[logits_name])
    next_token_id = max(range(len(logits)), key=lambda idx: float(logits[idx]))
    result = _build_result(
        request=request,
        vocab=vocab,
        next_token_id=next_token_id,
        logits=logits,
        topk=topk,
        tokenizer_runtime=tokenizer_runtime,
        prompt_doc=prompt_doc,
        ort_version=str(ort.__version__),
        selected_tensors=_trace_selected_outputs(outputs_by_name=outputs_by_name, trace_patterns=trace_patterns, step=0),
    )
    json.dump(result, sys.stdout)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
