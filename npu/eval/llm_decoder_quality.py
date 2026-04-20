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


def load_vocab(path: str | Path) -> Dict[str, int]:
    doc = load_json(path)
    tokens = doc.get('tokens', [])
    if not isinstance(tokens, list):
        raise ValueError('tokenizer vocab tokens must be a list')
    vocab: Dict[str, int] = {}
    for idx, token in enumerate(tokens):
        if token in vocab:
            raise ValueError(f'duplicate tokenizer token: {token!r}')
        vocab[str(token)] = idx
    return vocab


def encode_tokens(tokens: Sequence[str], vocab: Dict[str, int]) -> List[int]:
    out: List[int] = []
    for token in tokens:
        if token not in vocab:
            raise ValueError(f'token not present in vocab: {token!r}')
        out.append(int(vocab[token]))
    return out


def resolve_decoder_backend_config(dataset_manifest: JsonDict, model_contract: JsonDict, *, role: str) -> JsonDict:
    from npu.eval.decoder_backend import resolve_decoder_backend_config as _resolve

    return _resolve(dataset_manifest, model_contract, role=role)


def _build_backend_context(
    *,
    dataset_manifest: JsonDict,
    tokenizer_manifest: JsonDict,
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
) -> JsonDict:
    from npu.eval.decoder_backend import load_decoder_backend

    context = _build_backend_context(
        dataset_manifest=dataset_manifest,
        tokenizer_manifest=tokenizer_manifest,
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
) -> JsonDict:
    from npu.eval.decoder_backend import load_decoder_backend

    context = _build_backend_context(
        dataset_manifest=dataset_manifest,
        tokenizer_manifest=tokenizer_manifest,
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
