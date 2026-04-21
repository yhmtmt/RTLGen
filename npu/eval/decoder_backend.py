#!/usr/bin/env python3
"""Pluggable decoder backend interface for decoder-quality evaluation."""

from __future__ import annotations

import copy
import json
import os
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Protocol, Sequence

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.eval.llm_decoder_quality import (
    encode_tokens_for_bundle,
    tokenize_decoder_text,
)

JsonDict = Dict[str, Any]


@dataclass(frozen=True)
class DecoderBackendContext:
    dataset_manifest: JsonDict
    tokenizer_manifest: JsonDict
    tokenizer_bundle: JsonDict
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
        prompt_tokens = tokenize_decoder_text(prompt, context.tokenizer_bundle)
        continuation_tokens = tokenize_decoder_text(continuation, context.tokenizer_bundle)
        if len(continuation_tokens) != 1:
            raise ValueError(
                f"sample {sample['sample_id']} must tokenize to exactly one next token; got {continuation_tokens!r}"
            )
        prompt_token_ids = encode_tokens_for_bundle(prompt_tokens, context.tokenizer_bundle, allow_unk=True)
        next_token = continuation_tokens[0]
        next_token_id = encode_tokens_for_bundle([next_token], context.tokenizer_bundle, allow_unk=False)[0]
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
                'status': context.tokenizer_bundle.get('status', context.tokenizer_manifest.get('status', 'unknown')),
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
        tokenizer_kind = str(context.tokenizer_bundle.get('kind', 'space_prefix_words'))
        if tokenizer_kind == 'space_prefix_words':
            doc['candidate_semantics'] = 'space_prefix_placeholder_last_token_plus_parity_shift'
        elif tokenizer_kind == 'wordpiece_stub':
            doc['candidate_semantics'] = 'wordpiece_stub_placeholder_last_token_plus_parity_shift'
        else:
            doc['candidate_semantics'] = 'placeholder_last_token_plus_parity_shift'
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


class ReplayV1Backend:
    backend_id = 'replay_v1'

    def _normalize_config(self, backend_config: JsonDict, *, role: str) -> JsonDict:
        normalized = {
            'backend_id': self.backend_id,
            'role': role,
            'runtime_target': 'software_reference_replay' if role == 'reference' else 'software_emulation_replay',
            'equivalence_group': 'replay_v1',
            'replay_manifest': '',
            'interface': 'decoder_backend_v1',
            'replay_mode': 'frozen_artifact',
        }
        normalized.update(dict(backend_config or {}))
        normalized['backend_id'] = self.backend_id
        normalized['role'] = role
        normalized['interface'] = 'decoder_backend_v1'
        return normalized

    def _resolve_repo_path(self, path: str | Path) -> Path:
        p = Path(path)
        if p.is_absolute():
            return p
        repo_root = Path(__file__).resolve().parents[2]
        return repo_root / p

    def _load_json(self, path: Path) -> JsonDict:
        with path.open('r', encoding='utf-8') as f:
            return json.load(f)

    def _load_replay_doc(self, *, sample_id: str, backend_config: JsonDict, role: str) -> tuple[JsonDict, JsonDict, JsonDict, str]:
        replay_manifest_path = str(backend_config.get('replay_manifest', '')).strip()
        if not replay_manifest_path:
            raise ValueError(f'{self.backend_id} requires replay_manifest for role={role}')
        manifest_doc = self._load_json(self._resolve_repo_path(replay_manifest_path))
        samples = manifest_doc.get('samples', []) or []
        sample_entry = next((entry for entry in samples if entry.get('sample_id') == sample_id), None)
        if sample_entry is None:
            raise ValueError(f'{self.backend_id} manifest {replay_manifest_path} has no sample {sample_id!r}')
        doc_field = str(backend_config.get('replay_doc_field') or ('reference_json' if role == 'reference' else 'candidate_json'))
        doc_path = str(sample_entry.get(doc_field, '')).strip()
        if not doc_path:
            raise ValueError(f'{self.backend_id} manifest {replay_manifest_path} sample {sample_id!r} has no {doc_field}')
        replay_doc = self._load_json(self._resolve_repo_path(doc_path))
        return manifest_doc, sample_entry, replay_doc, doc_path

    def _append_note(self, doc: JsonDict, note: str) -> None:
        existing = str(doc.get('notes', '')).strip()
        doc['notes'] = f'{existing} {note}'.strip() if existing else note

    def _rebuild_doc(self, *, context: DecoderBackendContext, sample: JsonDict, backend_config: JsonDict, role: str) -> JsonDict:
        normalized = self._normalize_config(backend_config, role=role)
        manifest_doc, sample_entry, replay_doc, replay_doc_path = self._load_replay_doc(
            sample_id=str(sample['sample_id']),
            backend_config=normalized,
            role=role,
        )
        doc = copy.deepcopy(replay_doc)
        source_backend = copy.deepcopy(doc.get('backend', {}))
        doc['backend'] = normalized
        doc['replay_source'] = {
            'replay_manifest': str(normalized['replay_manifest']),
            'replay_doc': replay_doc_path,
            'source_backend': source_backend,
            'source_manifest_backend': copy.deepcopy(manifest_doc.get('backend_config', {})),
            'sample_entry': copy.deepcopy(sample_entry),
        }
        doc['dataset_id'] = context.dataset_manifest['dataset_id']
        doc['dataset_manifest'] = context.dataset_manifest_path
        doc['task'] = context.dataset_manifest['task']
        if 'tokenizer' in doc and isinstance(doc['tokenizer'], dict):
            doc['tokenizer']['manifest_path'] = context.tokenizer_manifest_path
        if 'model_binding' in doc and isinstance(doc['model_binding'], dict):
            doc['model_binding']['contract_path'] = context.model_contract_path
            doc['model_binding']['execution_backend'] = context.model_contract['execution_backend']
        self._append_note(doc, 'Replay-backed decoder fixture loaded from frozen artifacts.')
        return doc

    def build_reference_doc(self, *, context: DecoderBackendContext, sample: JsonDict, backend_config: JsonDict) -> JsonDict:
        return self._rebuild_doc(context=context, sample=sample, backend_config=backend_config, role='reference')

    def build_candidate_doc(self, *, context: DecoderBackendContext, sample: JsonDict, backend_config: JsonDict) -> JsonDict:
        return self._rebuild_doc(context=context, sample=sample, backend_config=backend_config, role='candidate')


class CommandJsonV1Backend:
    backend_id = 'command_json_v1'

    def _normalize_config(self, backend_config: JsonDict, *, role: str) -> JsonDict:
        normalized = {
            'backend_id': self.backend_id,
            'role': role,
            'runtime_target': 'external_reference' if role == 'reference' else 'external_emulation',
            'equivalence_group': 'command_json_v1',
            'command': [],
            'cwd': '',
            'timeout_s': 30.0,
            'request_schema': 'decoder_backend_command_v1',
            'interface': 'decoder_backend_v1',
        }
        normalized.update(dict(backend_config or {}))
        normalized['backend_id'] = self.backend_id
        normalized['role'] = role
        normalized['interface'] = 'decoder_backend_v1'
        return normalized

    def _default_prompt(self, *, context: DecoderBackendContext, sample: JsonDict) -> JsonDict:
        prompt = str(sample['prompt'])
        prompt_tokens = tokenize_decoder_text(prompt, context.tokenizer_bundle)
        prompt_token_ids = encode_tokens_for_bundle(prompt_tokens, context.tokenizer_bundle, allow_unk=True)
        return {
            'text': prompt,
            'tokens': prompt_tokens,
            'token_ids': prompt_token_ids,
            'token_count': len(prompt_tokens),
        }

    def _default_tokenizer(self, *, context: DecoderBackendContext) -> JsonDict:
        return {
            'tokenizer_id': context.tokenizer_manifest['tokenizer_id'],
            'kind': context.tokenizer_manifest['kind'],
            'manifest_path': context.tokenizer_manifest_path,
            'status': context.tokenizer_bundle.get('status', context.tokenizer_manifest.get('status', 'unknown')),
        }

    def _default_model_binding(self, *, context: DecoderBackendContext) -> JsonDict:
        return {
            'model_id': context.model_contract['model_id'],
            'status': context.model_contract['status'],
            'contract_path': context.model_contract_path,
            'execution_backend': context.model_contract['execution_backend'],
        }

    def _command_argv(self, command: Any) -> list[str]:
        if isinstance(command, str):
            argv = shlex.split(command)
        elif isinstance(command, list):
            argv = [str(part) for part in command]
        else:
            raise ValueError(f'{self.backend_id} command must be string or list')
        if not argv:
            raise ValueError(f'{self.backend_id} requires a non-empty command')
        return argv

    def _run_command(self, *, context: DecoderBackendContext, sample: JsonDict, normalized: JsonDict) -> JsonDict:
        argv = self._command_argv(normalized.get('command', []))
        env = os.environ.copy()
        env_overrides = normalized.get('env', {}) or {}
        for key, value in dict(env_overrides).items():
            env[str(key)] = str(value)
        request = {
            'schema': str(normalized.get('request_schema', 'decoder_backend_command_v1')),
            'role': normalized['role'],
            'dataset_manifest': context.dataset_manifest,
            'tokenizer_manifest': context.tokenizer_manifest,
            'model_contract': context.model_contract,
            'backend_config': normalized,
            'sample': sample,
            'paths': {
                'dataset_manifest_path': context.dataset_manifest_path,
                'tokenizer_manifest_path': context.tokenizer_manifest_path,
                'model_contract_path': context.model_contract_path,
            },
        }
        proc = subprocess.run(
            argv,
            input=json.dumps(request),
            text=True,
            capture_output=True,
            cwd=str(normalized.get('cwd', '')).strip() or None,
            env=env,
            timeout=float(normalized.get('timeout_s', 30.0)),
            check=False,
        )
        if proc.returncode != 0:
            stderr = proc.stderr.strip()
            raise ValueError(f'{self.backend_id} command failed rc={proc.returncode}: {stderr}')
        stdout = proc.stdout.strip()
        if not stdout:
            raise ValueError(f'{self.backend_id} command produced empty stdout')
        try:
            payload = json.loads(stdout)
        except json.JSONDecodeError as exc:
            raise ValueError(f'{self.backend_id} command stdout was not valid JSON') from exc
        return payload

    def _build_doc(self, *, context: DecoderBackendContext, sample: JsonDict, backend_config: JsonDict, role: str) -> JsonDict:
        normalized = self._normalize_config(backend_config, role=role)
        payload = self._run_command(context=context, sample=sample, normalized=normalized)
        tokenizer_doc = payload.get('tokenizer')
        if tokenizer_doc is None:
            tokenizer_doc = self._default_tokenizer(context=context)
        model_binding_doc = payload.get('model_binding')
        if model_binding_doc is None:
            model_binding_doc = self._default_model_binding(context=context)
        prompt_doc = payload.get('prompt')
        if prompt_doc is None:
            prompt_doc = self._default_prompt(context=context, sample=sample)
        doc = {
            'version': 0.1,
            'dataset_id': context.dataset_manifest['dataset_id'],
            'sample_id': sample['sample_id'],
            'task': context.dataset_manifest['task'],
            'decode_policy': payload.get('decode_policy', {'strategy': 'greedy', 'max_new_tokens': 1}),
            'dataset_manifest': context.dataset_manifest_path,
            'tokenizer': tokenizer_doc,
            'model_binding': model_binding_doc,
            'backend': normalized,
            'prompt': prompt_doc,
            'backend_invocation': {
                'command': self._command_argv(normalized.get('command', [])),
                'cwd': str(normalized.get('cwd', '')).strip(),
                'request_schema': str(normalized.get('request_schema', 'decoder_backend_command_v1')),
                'result_schema': 'decoder_backend_command_result_v1',
            },
        }
        if 'reference' in payload:
            doc['reference'] = payload['reference']
        if 'candidate' in payload:
            doc['candidate'] = payload['candidate']
        if role == 'reference' and 'reference' not in doc:
            raise ValueError(f'{self.backend_id} reference role requires reference in command result')
        if role == 'candidate' and 'candidate' not in doc:
            raise ValueError(f'{self.backend_id} candidate role requires candidate in command result')
        if 'candidate_semantics' in payload:
            doc['candidate_semantics'] = payload['candidate_semantics']
        if 'backend_runtime' in payload:
            doc['backend_runtime'] = payload['backend_runtime']
        if 'replay_source' in payload:
            doc['replay_source'] = payload['replay_source']
        if 'notes' in payload:
            doc['notes'] = str(payload['notes'])
        return doc

    def build_reference_doc(self, *, context: DecoderBackendContext, sample: JsonDict, backend_config: JsonDict) -> JsonDict:
        return self._build_doc(context=context, sample=sample, backend_config=backend_config, role='reference')

    def build_candidate_doc(self, *, context: DecoderBackendContext, sample: JsonDict, backend_config: JsonDict) -> JsonDict:
        return self._build_doc(context=context, sample=sample, backend_config=backend_config, role='candidate')


_BACKENDS: Dict[str, DecoderBackend] = {
    'placeholder_v1': PlaceholderV1Backend(),
    'replay_v1': ReplayV1Backend(),
    'command_json_v1': CommandJsonV1Backend(),
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
