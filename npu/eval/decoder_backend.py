#!/usr/bin/env python3
"""Pluggable decoder backend interface for decoder-quality evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Protocol, Sequence

from npu.eval.llm_decoder_quality import encode_tokens, tokenize_space_prefix_words

JsonDict = Dict[str, Any]


@dataclass(frozen=True)
class DecoderBackendContext:
    dataset_manifest: JsonDict
    tokenizer_manifest: JsonDict
    model_contract: JsonDict
    vocab: Dict[str, int]
    dataset_manifest_path: str
    tokenizer_manifest_path: str
    model_contract_path: str


class DecoderBackend(Protocol):
    backend_id: str

    def build_reference_doc(self, *, context: DecoderBackendContext, sample: JsonDict, backend_config: JsonDict) -> JsonDict:
        ...

    def build_candidate_doc(self, *, context: DecoderBackendContext, sample: JsonDict, backend_config: JsonDict) -> JsonDict:
        ...


class PlaceholderV1Backend:
    backend_id = 'placeholder_v1'

    def _normalize_config(self, backend_config: JsonDict, *, role: str) -> JsonDict:
        normalized = {
            'backend_id': self.backend_id,
            'role': role,
            'runtime_target': 'software_reference' if role == 'reference' else 'software_emulation',
            'equivalence_group': 'placeholder_v1',
            'candidate_rule': 'last_token_plus_parity_shift',
            'interface': 'decoder_backend_v1',
        }
        normalized.update(dict(backend_config or {}))
        normalized['backend_id'] = self.backend_id
        normalized['role'] = role
        normalized['interface'] = 'decoder_backend_v1'
        return normalized

    def _build_prompt_and_reference(self, *, context: DecoderBackendContext, sample: JsonDict, backend_config: JsonDict) -> JsonDict:
        prompt = str(sample['prompt'])
        continuation = str(sample['expected_continuation'])
        prompt_tokens = tokenize_space_prefix_words(prompt)
        continuation_tokens = tokenize_space_prefix_words(continuation)
        if len(continuation_tokens) != 1:
            raise ValueError(
                f"sample {sample['sample_id']} must tokenize to exactly one next token; got {continuation_tokens!r}"
            )
        prompt_token_ids = encode_tokens(prompt_tokens, context.vocab)
        next_token = continuation_tokens[0]
        next_token_id = encode_tokens([next_token], context.vocab)[0]
        return {
            'version': 0.1,
            'dataset_id': context.dataset_manifest['dataset_id'],
            'sample_id': sample['sample_id'],
            'task': context.dataset_manifest['task'],
            'decode_policy': {
                'strategy': 'greedy',
                'max_new_tokens': 1,
            },
            'dataset_manifest': context.dataset_manifest_path,
            'tokenizer': {
                'tokenizer_id': context.tokenizer_manifest['tokenizer_id'],
                'kind': context.tokenizer_manifest['kind'],
                'manifest_path': context.tokenizer_manifest_path,
            },
            'model_binding': {
                'model_id': context.model_contract['model_id'],
                'status': context.model_contract['status'],
                'contract_path': context.model_contract_path,
                'execution_backend': context.model_contract['execution_backend'],
            },
            'backend': backend_config,
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
        }

    def build_reference_doc(self, *, context: DecoderBackendContext, sample: JsonDict, backend_config: JsonDict) -> JsonDict:
        normalized = self._normalize_config(backend_config, role='reference')
        doc = self._build_prompt_and_reference(context=context, sample=sample, backend_config=normalized)
        doc['notes'] = 'Reference-only placeholder decoder fixture. No trained model inference yet.'
        return doc

    def _deterministic_candidate_next_token_id(self, prompt_token_ids: Sequence[int], vocab_size: int, rule: str) -> int:
        if vocab_size <= 0:
            raise ValueError('vocab size must be positive')
        if not prompt_token_ids:
            return 0
        if rule != 'last_token_plus_parity_shift':
            raise ValueError(f'unsupported placeholder candidate rule: {rule}')
        base = int(prompt_token_ids[-1])
        shift = 0 if (sum(int(v) for v in prompt_token_ids) % 2 == 0) else 1
        return (base + shift) % vocab_size

    def build_candidate_doc(self, *, context: DecoderBackendContext, sample: JsonDict, backend_config: JsonDict) -> JsonDict:
        normalized = self._normalize_config(backend_config, role='candidate')
        doc = self._build_prompt_and_reference(context=context, sample=sample, backend_config=normalized)
        inv_vocab = {idx: token for token, idx in context.vocab.items()}
        prompt_token_ids = doc['prompt']['token_ids']
        predicted_id = self._deterministic_candidate_next_token_id(
            prompt_token_ids,
            len(context.vocab),
            str(normalized.get('candidate_rule', 'last_token_plus_parity_shift')),
        )
        predicted_token = inv_vocab[predicted_id]
        doc['candidate_semantics'] = 'space_prefix_placeholder_last_token_plus_parity_shift'
        doc['candidate'] = {
            'next_token_id': predicted_id,
            'next_token_text': predicted_token,
            'confidence': 1.0,
        }
        doc['notes'] = (
            'Candidate-only placeholder decoder fixture. No trained model inference yet; '
            'predictions come from a deterministic synthetic rule.'
        )
        return doc


_BACKENDS: Dict[str, DecoderBackend] = {
    'placeholder_v1': PlaceholderV1Backend(),
}


def load_decoder_backend(backend_config: JsonDict | None) -> DecoderBackend:
    cfg = dict(backend_config or {})
    backend_id = str(cfg.get('backend_id', 'placeholder_v1'))
    if backend_id not in _BACKENDS:
        raise ValueError(f'unknown decoder backend: {backend_id}')
    return _BACKENDS[backend_id]


def _default_backend_config(*, role: str) -> JsonDict:
    return {
        'backend_id': 'placeholder_v1',
        'role': role,
        'runtime_target': 'software_reference' if role == 'reference' else 'software_emulation',
        'equivalence_group': 'placeholder_v1',
        'candidate_rule': 'last_token_plus_parity_shift',
        'interface': 'decoder_backend_v1',
    }


def resolve_decoder_backend_config(dataset_manifest: JsonDict, model_contract: JsonDict, *, role: str) -> JsonDict:
    dataset_cfgs = dataset_manifest.get('decoder_backend_configs', {}) or {}
    model_cfgs = model_contract.get('backend_configs', {}) or {}
    config = dict(_default_backend_config(role=role))
    if role in model_cfgs:
        config.update(dict(model_cfgs[role]))
    if role in dataset_cfgs:
        config.update(dict(dataset_cfgs[role]))
    config['role'] = role
    config['interface'] = 'decoder_backend_v1'
    return config
