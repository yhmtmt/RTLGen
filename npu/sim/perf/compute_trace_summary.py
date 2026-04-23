#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


def _format_vec_hex(value: int, *, lanes: int) -> str:
    width = max(2, int(lanes) * 2)
    mask = (1 << (int(lanes) * 8)) - 1 if int(lanes) < 8 else 0xFFFF_FFFF_FFFF_FFFF
    return f"0x{(int(value) & mask):0{width}x}"


def build_rtl_compute_summary(path: str | Path) -> dict[str, Any]:
    gemm_pat = re.compile(r"\bGEMM_TIMING\b.*\boffset=(-?\d+)\b.*\baccum=(-?\d+)\b")
    vec_pat = re.compile(r"\bVEC_DONE\b.*\boffset=(-?\d+)\b.*\bresult=0x([0-9a-fA-F]+)\b")

    gemm = {}
    vec = {}
    with Path(path).open('r', encoding='utf-8') as f:
        for line in f:
            gm = gemm_pat.search(line)
            if gm:
                offset = int(gm.group(1))
                if offset in gemm:
                    raise ValueError(f'duplicate GEMM completion offset in RTL log: {offset}')
                gemm[offset] = int(gm.group(2))
                continue
            vm = vec_pat.search(line)
            if vm:
                offset = int(vm.group(1))
                if offset in vec:
                    raise ValueError(f'duplicate VEC completion offset in RTL log: {offset}')
                raw_hex = vm.group(2)
                lanes = max(1, len(raw_hex) // 2)
                vec[offset] = {
                    'offset': offset,
                    'lanes': lanes,
                    'result_hex': _format_vec_hex(int(raw_hex, 16), lanes=lanes),
                }

    return {
        'schema': 'npu_compute_equivalence_trace_v1',
        'gemm': [
            {'offset': offset, 'accum': gemm[offset]}
            for offset in sorted(gemm)
        ],
        'vec': [
            vec[offset]
            for offset in sorted(vec)
        ],
    }


def build_perf_compute_summary(path: str | Path) -> dict[str, Any]:
    with Path(path).open('r', encoding='utf-8') as f:
        trace = json.load(f)

    gemm = {}
    vec = {}
    for event in trace.get('trace', []):
        name = event.get('name')
        if name == 'GEMM':
            if 'offset' not in event:
                raise ValueError('perf GEMM event missing offset')
            if 'expected_accum' not in event:
                raise ValueError('perf GEMM event missing expected_accum')
            offset = int(event['offset'])
            if offset in gemm:
                raise ValueError(f'duplicate GEMM offset in perf trace: {offset}')
            gemm[offset] = int(event['expected_accum'])
        elif name == 'VEC_OP':
            if 'offset' not in event:
                raise ValueError('perf VEC_OP event missing offset')
            if 'expected_result' not in event:
                raise ValueError('perf VEC_OP event missing expected_result')
            offset = int(event['offset'])
            if offset in vec:
                raise ValueError(f'duplicate VEC offset in perf trace: {offset}')
            lanes = int(event.get('lanes', 8))
            if lanes < 1:
                lanes = 1
            if lanes > 8:
                lanes = 8
            vec[offset] = {
                'offset': offset,
                'lanes': lanes,
                'result_hex': _format_vec_hex(int(str(event['expected_result']), 0), lanes=lanes),
            }

    return {
        'schema': 'npu_compute_equivalence_trace_v1',
        'gemm': [
            {'offset': offset, 'accum': gemm[offset]}
            for offset in sorted(gemm)
        ],
        'vec': [
            vec[offset]
            for offset in sorted(vec)
        ],
    }


def canonical_summary_sha256(summary: dict[str, Any]) -> str:
    payload = json.dumps(summary, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode('utf-8')
    return hashlib.sha256(payload).hexdigest()
