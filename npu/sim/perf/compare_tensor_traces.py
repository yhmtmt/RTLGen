#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from npu.eval.tensor_trace_summary import (
    byte_vector_tensor_summary,
    packed_u8_tensor_summary,
    parse_rtl_tensor_trace_log,
    scalar_tensor_summary,
    selected_tensor_trace_hash,
)

SEMANTIC_VEC_TRACE_NAMES = {
    'softmax': 'vec.softmax',
    'layernorm': 'vec.layernorm',
    'dsoftmax': 'vec.dsoftmax',
    'dlayernorm': 'vec.dlayernorm',
}


def _build_perf_tensor_trace(path: str | Path) -> list[dict[str, Any]]:
    with Path(path).open('r', encoding='utf-8') as f:
        trace = json.load(f)

    tensors = []
    gemm_step = 0
    softmax_step = 0
    vec_step = 0
    for event in trace.get('trace', []):
        name = event.get('name')
        if name == 'GEMM':
            if 'expected_accum' not in event:
                raise ValueError('perf GEMM event missing expected_accum')
            gemm_step += 1
            tensors.append(
                scalar_tensor_summary(
                    name='gemm.accum',
                    step=gemm_step,
                    value=event['expected_accum'],
                    dtype='int32',
                )
            )
        elif name == 'SOFTMAX':
            softmax_step += 1
            if 'expected_result_bytes' not in event:
                continue
            row_bytes = int(event.get('row_bytes', len(event['expected_result_bytes'])))
            rows = int(event.get('rows', 1))
            tensors.append(
                byte_vector_tensor_summary(
                    name='softmax.result',
                    step=softmax_step,
                    data_bytes=event['expected_result_bytes'],
                    dtype=str(event.get('expected_result_encoding', 'u8')),
                    shape=[rows, row_bytes],
                )
            )
        elif name == 'VEC_OP':
            if 'expected_result' not in event:
                raise ValueError('perf VEC_OP event missing expected_result')
            vec_step += 1
            lanes = int(event.get('lanes', 8))
            tensors.append(
                packed_u8_tensor_summary(
                    name='vec.result',
                    step=vec_step,
                    result=str(event['expected_result']),
                    lanes=lanes,
                    dtype='packed_u8',
                )
            )
            semantic_name = SEMANTIC_VEC_TRACE_NAMES.get(str(event.get('op', '')).lower())
            if semantic_name is not None:
                tensors.append(
                    packed_u8_tensor_summary(
                        name=semantic_name,
                        step=vec_step,
                        result=str(event['expected_result']),
                        lanes=lanes,
                        dtype='packed_u8',
                    )
                )
    return sorted(tensors, key=lambda entry: (int(entry.get('step', 0)), str(entry.get('name', ''))))


def _write_json(path: str | None, payload: Any) -> None:
    if not path:
        return
    Path(path).write_text(json.dumps(payload, indent=2) + '\n', encoding='utf-8')


def main() -> int:
    ap = argparse.ArgumentParser(description='Compare canonical RTL/perf tensor trace summaries.')
    ap.add_argument('--rtl-log', required=True, help='RTL sim log containing TENSOR_TRACE lines')
    ap.add_argument('--perf-trace', required=True, help='Perf trace JSON file')
    ap.add_argument('--rtl-summary-out', help='Optional path to write canonical RTL tensor trace JSON')
    ap.add_argument('--perf-summary-out', help='Optional path to write canonical perf tensor trace JSON')
    args = ap.parse_args()

    try:
        rtl_tensors = parse_rtl_tensor_trace_log(args.rtl_log)
        perf_tensors = _build_perf_tensor_trace(args.perf_trace)
    except ValueError as exc:
        print(f'compare-tensor-trace: {exc}', file=sys.stderr)
        return 2

    _write_json(args.rtl_summary_out, rtl_tensors)
    _write_json(args.perf_summary_out, perf_tensors)

    rtl_hash = selected_tensor_trace_hash(rtl_tensors)
    perf_hash = selected_tensor_trace_hash(perf_tensors)
    print(f'compare-tensor-trace: rtl_tensor_trace_sha256={rtl_hash}')
    print(f'compare-tensor-trace: perf_tensor_trace_sha256={perf_hash}')
    print(f'compare-tensor-trace: compared tensors={len(perf_tensors)} rtl_tensors={len(rtl_tensors)}')

    if rtl_hash != perf_hash:
        print('compare-tensor-trace: FAIL canonical tensor trace hash mismatch', file=sys.stderr)
        return 1
    print('compare-tensor-trace: OK')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
