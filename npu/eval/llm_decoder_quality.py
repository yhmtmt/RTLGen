#!/usr/bin/env python3
"""Decoder-quality scaffolding utilities for the tiny LLM decoder stage."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Sequence

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


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
) -> JsonDict:
    prompt = str(sample['prompt'])
    continuation = str(sample['expected_continuation'])
    prompt_tokens = tokenize_space_prefix_words(prompt)
    continuation_tokens = tokenize_space_prefix_words(continuation)
    if len(continuation_tokens) != 1:
        raise ValueError(
            f"sample {sample['sample_id']} must tokenize to exactly one next token; "
            f"got {continuation_tokens!r}"
        )

    prompt_token_ids = encode_tokens(prompt_tokens, vocab)
    next_token = continuation_tokens[0]
    next_token_id = encode_tokens([next_token], vocab)[0]

    return {
        'version': 0.1,
        'dataset_id': dataset_manifest['dataset_id'],
        'sample_id': sample['sample_id'],
        'task': dataset_manifest['task'],
        'decode_policy': {
            'strategy': 'greedy',
            'max_new_tokens': 1,
        },
        'dataset_manifest': dataset_manifest_path,
        'tokenizer': {
            'tokenizer_id': tokenizer_manifest['tokenizer_id'],
            'kind': tokenizer_manifest['kind'],
            'manifest_path': tokenizer_manifest_path,
        },
        'model_binding': {
            'model_id': model_contract['model_id'],
            'status': model_contract['status'],
            'contract_path': model_contract_path,
            'execution_backend': model_contract['execution_backend'],
        },
        'prompt': {
            'text': prompt,
            'tokens': prompt_tokens,
            'token_ids': prompt_token_ids,
            'token_count': len(prompt_tokens),
        },
        'reference': {
            'expected_continuation': continuation,
            'next_token_text': next_token,
            'next_token_id': next_token_id,
            'next_token_rank': 1,
            'selected_tensors': [],
        },
        'notes': 'Reference-only placeholder decoder fixture. No trained model inference yet.',
    }


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
