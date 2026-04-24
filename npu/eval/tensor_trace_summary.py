#!/usr/bin/env python3
"""Canonical tensor trace summaries for strict equivalence checks."""

from __future__ import annotations

import fnmatch
import hashlib
import json
import shlex
from pathlib import Path
from typing import Any, Dict, Sequence

JsonDict = Dict[str, Any]


def canonical_json_sha256(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode('utf-8')
    return hashlib.sha256(payload).hexdigest()


def selected_tensor_trace_hash(selected_tensors: Sequence[JsonDict] | None) -> str:
    return canonical_json_sha256(list(selected_tensors or []))


def tensor_summary(raw_output: Any, *, name: str, step: int, quantization: JsonDict | None = None) -> JsonDict:
    import numpy as np

    array = np.asarray(raw_output, dtype=np.float32)
    summary: JsonDict = {
        'name': str(name),
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


def matches_trace_pattern(name: str, patterns: Sequence[str]) -> bool:
    return any(fnmatch.fnmatch(name, pattern) for pattern in patterns)


def trace_selected_outputs(*, outputs_by_name: JsonDict, trace_patterns: Sequence[str], step: int) -> list[JsonDict]:
    if not trace_patterns:
        return []
    traced: list[JsonDict] = []
    for name in sorted(outputs_by_name):
        if matches_trace_pattern(name, trace_patterns):
            traced.append(tensor_summary(outputs_by_name[name], name=name, step=step))
    return traced


def _parse_shape(value: str) -> list[int]:
    text = value.strip()
    if not text:
        return []
    return [int(part) for part in text.split(',') if part.strip()]


def _parse_quantization(value: str) -> JsonDict:
    text = value.strip()
    if not text or text == 'none':
        return {}
    loaded = json.loads(text)
    if not isinstance(loaded, dict):
        raise ValueError('TENSOR_TRACE quantization must decode to a JSON object')
    return loaded


def _parse_tensor_trace_line(line: str) -> JsonDict | None:
    if 'TENSOR_TRACE' not in line:
        return None
    parts = shlex.split(line.strip())
    try:
        start = parts.index('TENSOR_TRACE') + 1
    except ValueError:
        return None
    fields: dict[str, str] = {}
    for part in parts[start:]:
        if '=' not in part:
            continue
        key, value = part.split('=', 1)
        fields[key] = value

    required = ('name', 'step', 'shape', 'dtype', 'min', 'max', 'mean', 'std')
    missing = [key for key in required if key not in fields]
    if missing:
        raise ValueError(f'TENSOR_TRACE missing required fields: {",".join(missing)}')

    summary: JsonDict = {
        'name': fields['name'],
        'step': int(fields['step']),
        'shape': _parse_shape(fields['shape']),
        'dtype': fields['dtype'],
        'min': float(fields['min']),
        'max': float(fields['max']),
        'mean': float(fields['mean']),
        'std': float(fields['std']),
    }
    if 'quantization' in fields:
        quantization = _parse_quantization(fields['quantization'])
        if quantization:
            summary['quantization'] = quantization
    return summary


def parse_rtl_tensor_trace_log(path: str | Path) -> list[JsonDict]:
    traces: list[JsonDict] = []
    with Path(path).open('r', encoding='utf-8') as f:
        for line in f:
            parsed = _parse_tensor_trace_line(line)
            if parsed is not None:
                traces.append(parsed)
    return sorted(traces, key=lambda entry: (int(entry.get('step', 0)), str(entry.get('name', ''))))
