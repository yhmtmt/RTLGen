#!/usr/bin/env python3
"""Decoder-quality scaffolding utilities for the tiny LLM decoder stage."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Sequence

JsonDict = Dict[str, Any]


def load_json(path: str | Path) -> JsonDict:
    with Path(path).open('r', encoding='utf-8') as f:
        return json.load(f)


def load_jsonl(path: str | Path) -> List[JsonDict]:
    out: List[JsonDict] = []
    with Path(path).open('r', encoding='utf-8') as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            out.append(json.loads(line))
    return out


def tokenize_space_prefix_words(text: str) -> List[str]:
    tokens: List[str] = []
    idx = 0
    n = len(text)
    while idx < n:
        start = idx
        while idx < n and text[idx].isspace():
            idx += 1
        if idx >= n:
            break
        while idx < n and not text[idx].isspace():
            idx += 1
        tokens.append(text[start:idx])
    return tokens


def tokenize_wordpiece_stub(text: str) -> List[str]:
    return [piece for piece in text.strip().split() if piece]


def _load_tokenizers_tokenizer():
    try:
        from tokenizers import Tokenizer  # type: ignore
    except ModuleNotFoundError as exc:
        raise ValueError('tokenizers is not installed for gpt2_bpe bundle support') from exc
    return Tokenizer


def tokenize_gpt2_bpe(text: str, tokenizer_bundle: JsonDict) -> List[str]:
    tokenizer_json_path = str(tokenizer_bundle.get('tokenizer_json_path', '')).strip()
    if not tokenizer_json_path:
        raise ValueError('gpt2_bpe tokenizer bundle is missing tokenizer_json_path')
    tokenizer_runtime = _load_tokenizers_tokenizer().from_file(tokenizer_json_path)
    encoded = tokenizer_runtime.encode(text)
    return [str(token) for token in encoded.tokens]


def _extract_vocab_tokens(doc: JsonDict) -> List[str]:
    tokens = doc.get('tokens', [])
    if isinstance(tokens, list) and tokens:
        return [str(token) for token in tokens]
    if isinstance(tokens, list) and not tokens and all(isinstance(k, str) for k in doc.keys()):
        pass
    if all(isinstance(k, str) for k in doc.keys()) and all(isinstance(v, int) for v in doc.values()):
        ordered = sorted(((str(token), int(idx)) for token, idx in doc.items()), key=lambda item: item[1])
        expected = list(range(len(ordered)))
        actual = [idx for _, idx in ordered]
        if actual != expected:
            raise ValueError('tokenizer vocab mapping must contain contiguous ids starting at 0')
        return [token for token, _ in ordered]
    if not isinstance(tokens, list):
        raise ValueError('tokenizer vocab tokens must be a list or token->id mapping')
    return [str(token) for token in tokens]


def _resolve_asset_file(asset_path: str | Path, *, manifest_path: str | Path | None = None) -> Path:
    manifest_dir = Path(manifest_path).resolve().parent if manifest_path is not None else None
    asset_file = Path(asset_path)
    if not asset_file.is_absolute() and manifest_dir is not None:
        asset_file = manifest_dir / asset_file
    return asset_file


def _load_merge_rules(path: str | Path) -> List[str]:
    rules: List[str] = []
    with Path(path).open('r', encoding='utf-8') as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith('#'):
                continue
            rules.append(line)
    return rules


def load_vocab(path: str | Path) -> Dict[str, int]:
    doc = load_json(path)
    tokens = _extract_vocab_tokens(doc)
    vocab: Dict[str, int] = {}
    for idx, token in enumerate(tokens):
        if token in vocab:
            raise ValueError(f'duplicate tokenizer token: {token!r}')
        vocab[token] = idx
    return vocab


def build_tokenizer_bundle(
    tokenizer_manifest: JsonDict,
    *,
    vocab: Dict[str, int],
    manifest_path: str | Path | None = None,
    tokens: Sequence[str] | None = None,
    merges: Sequence[str] | None = None,
) -> JsonDict:
    token_list = [str(token) for token in tokens] if tokens is not None else [token for token, _ in sorted(vocab.items(), key=lambda item: item[1])]
    specials_raw = tokenizer_manifest.get('special_tokens', {}) or {}
    if not isinstance(specials_raw, dict):
        raise ValueError('tokenizer manifest special_tokens must be an object')
    special_tokens: Dict[str, Dict[str, Any]] = {}
    for name, token in specials_raw.items():
        token_text = str(token)
        token_id = vocab.get(token_text)
        special_tokens[str(name)] = {
            'token': token_text,
            'id': token_id,
            'present_in_vocab': token_id is not None,
        }
    vocab_file = ''
    vocab_path = tokenizer_manifest.get('vocab_json')
    if isinstance(vocab_path, str) and vocab_path.strip():
        vocab_file = str(_resolve_asset_file(vocab_path, manifest_path=manifest_path))
    merges_file = ''
    merges_path = tokenizer_manifest.get('merges_txt')
    if isinstance(merges_path, str) and merges_path.strip():
        merges_file = str(_resolve_asset_file(merges_path, manifest_path=manifest_path))
    tokenizer_json_file = ''
    tokenizer_json_path = tokenizer_manifest.get('tokenizer_json')
    if isinstance(tokenizer_json_path, str) and tokenizer_json_path.strip():
        tokenizer_json_file = str(_resolve_asset_file(tokenizer_json_path, manifest_path=manifest_path))
    tokenizer_config_file = ''
    tokenizer_config_path = tokenizer_manifest.get('tokenizer_config_json')
    if isinstance(tokenizer_config_path, str) and tokenizer_config_path.strip():
        tokenizer_config_file = str(_resolve_asset_file(tokenizer_config_path, manifest_path=manifest_path))
    special_tokens_map_file = ''
    special_tokens_map_path = tokenizer_manifest.get('special_tokens_map_json')
    if isinstance(special_tokens_map_path, str) and special_tokens_map_path.strip():
        special_tokens_map_file = str(_resolve_asset_file(special_tokens_map_path, manifest_path=manifest_path))
    return {
        'tokenizer_id': str(tokenizer_manifest['tokenizer_id']),
        'kind': str(tokenizer_manifest['kind']),
        'family': str(tokenizer_manifest.get('family', tokenizer_manifest.get('kind', 'unknown'))),
        'manifest_path': str(manifest_path) if manifest_path is not None else '',
        'vocab_path': vocab_file,
        'merges_path': merges_file,
        'tokenizer_json_path': tokenizer_json_file,
        'tokenizer_config_path': tokenizer_config_file,
        'special_tokens_map_path': special_tokens_map_file,
        'tokens': token_list,
        'vocab': dict(vocab),
        'merge_rules': [str(rule) for rule in (merges or [])],
        'merge_count': len(list(merges or [])),
        'special_tokens': special_tokens,
        'status': str(tokenizer_manifest.get('status', 'unknown')),
        'backend_interface': str(tokenizer_manifest.get('backend_interface', 'decoder_tokenizer_v1')),
        'unk_supported': bool(tokenizer_manifest.get('unk_supported', False)),
        'pretokenization': dict(tokenizer_manifest.get('pretokenization', {}) or {}),
        'normalization': dict(tokenizer_manifest.get('normalization', {}) or {}),
    }


def load_tokenizer_bundle(tokenizer_manifest: JsonDict, *, manifest_path: str | Path | None = None) -> JsonDict:
    vocab_path = tokenizer_manifest.get('vocab_json')
    if not isinstance(vocab_path, str) or not vocab_path.strip():
        raise ValueError('tokenizer manifest must define non-empty vocab_json')
    vocab_file = _resolve_asset_file(vocab_path, manifest_path=manifest_path)
    vocab_doc = load_json(vocab_file)
    tokens = _extract_vocab_tokens(vocab_doc)
    vocab: Dict[str, int] = {}
    for idx, token in enumerate(tokens):
        if token in vocab:
            raise ValueError(f'duplicate tokenizer token: {token!r}')
        vocab[token] = idx
    merges: List[str] = []
    merges_path = tokenizer_manifest.get('merges_txt')
    if isinstance(merges_path, str) and merges_path.strip():
        merges_file = _resolve_asset_file(merges_path, manifest_path=manifest_path)
        merges = _load_merge_rules(merges_file)
    return build_tokenizer_bundle(
        tokenizer_manifest,
        vocab=vocab,
        manifest_path=manifest_path,
        tokens=tokens,
        merges=merges,
    )


def tokenize_decoder_text(text: str, tokenizer_bundle: JsonDict) -> List[str]:
    kind = str(tokenizer_bundle.get('kind', 'space_prefix_words'))
    if kind == 'space_prefix_words':
        return tokenize_space_prefix_words(text)
    if kind == 'wordpiece_stub':
        return tokenize_wordpiece_stub(text)
    if kind == 'gpt2_bpe':
        return tokenize_gpt2_bpe(text, tokenizer_bundle)
    raise ValueError(f'unsupported tokenizer kind: {kind}')


def encode_tokens(tokens: Sequence[str], vocab: Dict[str, int]) -> List[int]:
    out: List[int] = []
    for token in tokens:
        if token not in vocab:
            raise ValueError(f'token not present in vocab: {token!r}')
        out.append(int(vocab[token]))
    return out


def encode_tokens_for_bundle(tokens: Sequence[str], tokenizer_bundle: JsonDict, *, allow_unk: bool | None = None) -> List[int]:
    vocab = dict(tokenizer_bundle['vocab'])
    if allow_unk is None:
        allow_unk = bool(tokenizer_bundle.get('unk_supported', False))
    unk_entry = dict((tokenizer_bundle.get('special_tokens') or {}).get('unk', {}))
    unk_id = unk_entry.get('id')
    out: List[int] = []
    for token in tokens:
        if token in vocab:
            out.append(int(vocab[token]))
            continue
        if allow_unk and unk_id is not None:
            out.append(int(unk_id))
            continue
        raise ValueError(f'token not present in tokenizer bundle: {token!r}')
    return out


def resolve_decoder_backend_config(dataset_manifest: JsonDict, model_contract: JsonDict, *, role: str) -> JsonDict:
    from npu.eval.decoder_backend import resolve_decoder_backend_config as _resolve

    return _resolve(dataset_manifest, model_contract, role=role)


def _build_backend_context(
    *,
    dataset_manifest: JsonDict,
    tokenizer_manifest: JsonDict,
    tokenizer_bundle: JsonDict,
    vocab: Dict[str, int],
    model_contract: JsonDict,
    dataset_manifest_path: str,
    tokenizer_manifest_path: str,
    model_contract_path: str,
):
    from npu.eval.decoder_backend import DecoderBackendContext

    return DecoderBackendContext(
        dataset_manifest=dataset_manifest,
        tokenizer_manifest=tokenizer_manifest,
        tokenizer_bundle=tokenizer_bundle,
        model_contract=model_contract,
        vocab=vocab,
        dataset_manifest_path=dataset_manifest_path,
        tokenizer_manifest_path=tokenizer_manifest_path,
        model_contract_path=model_contract_path,
    )


def build_decoder_reference_doc(
    *,
    dataset_manifest: JsonDict,
    sample: JsonDict,
    tokenizer_manifest: JsonDict,
    vocab: Dict[str, int],
    model_contract: JsonDict,
    dataset_manifest_path: str,
    tokenizer_manifest_path: str,
    model_contract_path: str,
    backend_config: JsonDict | None = None,
    tokenizer_bundle: JsonDict | None = None,
) -> JsonDict:
    from npu.eval.decoder_backend import load_decoder_backend

    bundle = tokenizer_bundle or build_tokenizer_bundle(
        tokenizer_manifest,
        vocab=vocab,
        manifest_path=tokenizer_manifest_path,
    )
    context = _build_backend_context(
        dataset_manifest=dataset_manifest,
        tokenizer_manifest=tokenizer_manifest,
        tokenizer_bundle=bundle,
        vocab=vocab,
        model_contract=model_contract,
        dataset_manifest_path=dataset_manifest_path,
        tokenizer_manifest_path=tokenizer_manifest_path,
        model_contract_path=model_contract_path,
    )
    config = dict(backend_config or {'backend_id': 'placeholder_v1'})
    backend = load_decoder_backend(config)
    return backend.build_reference_doc(context=context, sample=sample, backend_config=config)


def build_decoder_candidate_doc(
    *,
    dataset_manifest: JsonDict,
    sample: JsonDict,
    tokenizer_manifest: JsonDict,
    vocab: Dict[str, int],
    model_contract: JsonDict,
    dataset_manifest_path: str,
    tokenizer_manifest_path: str,
    model_contract_path: str,
    backend_config: JsonDict | None = None,
    tokenizer_bundle: JsonDict | None = None,
) -> JsonDict:
    from npu.eval.decoder_backend import load_decoder_backend

    bundle = tokenizer_bundle or build_tokenizer_bundle(
        tokenizer_manifest,
        vocab=vocab,
        manifest_path=tokenizer_manifest_path,
    )
    context = _build_backend_context(
        dataset_manifest=dataset_manifest,
        tokenizer_manifest=tokenizer_manifest,
        tokenizer_bundle=bundle,
        vocab=vocab,
        model_contract=model_contract,
        dataset_manifest_path=dataset_manifest_path,
        tokenizer_manifest_path=tokenizer_manifest_path,
        model_contract_path=model_contract_path,
    )
    config = dict(backend_config or {'backend_id': 'placeholder_v1'})
    backend = load_decoder_backend(config)
    return backend.build_candidate_doc(context=context, sample=sample, backend_config=config)


def compare_decoder_reference_docs(reference_doc: JsonDict, candidate_doc: JsonDict) -> JsonDict:
    ref = reference_doc['reference']
    cand = candidate_doc.get('candidate', {})
    next_token_id_match = int(ref['next_token_id'] == cand.get('next_token_id'))
    next_token_text_match = int(ref['next_token_text'] == cand.get('next_token_text'))
    return {
        'sample_id': reference_doc['sample_id'],
        'aggregate': {
            'next_token_id_match': next_token_id_match,
            'next_token_text_match': next_token_text_match,
        },
    }
