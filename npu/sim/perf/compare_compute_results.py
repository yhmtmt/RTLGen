#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import sys

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from npu.sim.perf.compute_trace_summary import (
    build_perf_compute_summary,
    build_rtl_compute_summary,
    canonical_summary_sha256,
)


def _gemm_map(summary):
    return {int(entry['offset']): int(entry['accum']) for entry in summary.get('gemm', [])}


def _vec_map(summary):
    return {
        int(entry['offset']): (str(entry['result_hex']), int(entry['lanes']))
        for entry in summary.get('vec', [])
    }


def _format_offsets(offsets):
    if not offsets:
        return '[]'
    return '[' + ', '.join(str(x) for x in sorted(offsets)) + ']'


def main() -> int:
    ap = argparse.ArgumentParser(description='Compare GEMM/VEC compute results between RTL log and perf trace.')
    ap.add_argument('--rtl-log', required=True, help='RTL sim log with GEMM_TIMING/VEC_DONE lines')
    ap.add_argument('--perf-trace', required=True, help='Perf trace JSON file')
    ap.add_argument('--rtl-summary-out', help='Optional path to write canonical RTL compute summary JSON')
    ap.add_argument('--perf-summary-out', help='Optional path to write canonical perf compute summary JSON')
    args = ap.parse_args()

    try:
        rtl_summary = build_rtl_compute_summary(args.rtl_log)
        perf_summary = build_perf_compute_summary(args.perf_trace)
    except ValueError as e:
        print(f'compare-compute: {e}', file=sys.stderr)
        return 2

    if args.rtl_summary_out:
        Path(args.rtl_summary_out).write_text(json.dumps(rtl_summary, indent=2) + '\n', encoding='utf-8')
    if args.perf_summary_out:
        Path(args.perf_summary_out).write_text(json.dumps(perf_summary, indent=2) + '\n', encoding='utf-8')

    rtl_hash = canonical_summary_sha256(rtl_summary)
    perf_hash = canonical_summary_sha256(perf_summary)
    print(f'compare-compute: rtl_summary_sha256={rtl_hash}')
    print(f'compare-compute: perf_summary_sha256={perf_hash}')

    rtl_gemm = _gemm_map(rtl_summary)
    perf_gemm = _gemm_map(perf_summary)
    rtl_vec = _vec_map(rtl_summary)
    perf_vec = _vec_map(perf_summary)

    if not perf_gemm and not perf_vec:
        print('compare-compute: no GEMM or VEC_OP events in perf trace', file=sys.stderr)
        return 2

    mismatch = False

    missing_gemm = sorted(set(perf_gemm.keys()) - set(rtl_gemm.keys()))
    extra_gemm = sorted(set(rtl_gemm.keys()) - set(perf_gemm.keys()))
    if missing_gemm:
        print(f'compare-compute: missing GEMM completions in RTL log offsets={_format_offsets(missing_gemm)}', file=sys.stderr)
        mismatch = True
    if extra_gemm:
        print(f'compare-compute: extra GEMM completions in RTL log offsets={_format_offsets(extra_gemm)}', file=sys.stderr)
        mismatch = True

    missing_vec = sorted(set(perf_vec.keys()) - set(rtl_vec.keys()))
    extra_vec = sorted(set(rtl_vec.keys()) - set(perf_vec.keys()))
    if missing_vec:
        print(f'compare-compute: missing VEC completions in RTL log offsets={_format_offsets(missing_vec)}', file=sys.stderr)
        mismatch = True
    if extra_vec:
        print(f'compare-compute: extra VEC completions in RTL log offsets={_format_offsets(extra_vec)}', file=sys.stderr)
        mismatch = True

    for offset in sorted(set(perf_gemm.keys()) & set(rtl_gemm.keys())):
        expected = int(perf_gemm[offset])
        got = int(rtl_gemm[offset])
        print(f'compare-compute: GEMM[offset={offset}] rtl_accum={got} perf_expected_accum={expected}')
        if got != expected:
            print(
                f'compare-compute: FAIL GEMM[offset={offset}] rtl_accum={got} perf_expected_accum={expected}',
                file=sys.stderr,
            )
            mismatch = True

    for offset in sorted(set(perf_vec.keys()) & set(rtl_vec.keys())):
        expected, lanes = perf_vec[offset]
        got, got_lanes = rtl_vec[offset]
        print(
            f'compare-compute: VEC[offset={offset}] rtl_result={got} perf_expected_result={expected} lanes={lanes}'
        )
        if got_lanes != lanes:
            print(
                f'compare-compute: FAIL VEC[offset={offset}] rtl_lanes={got_lanes} perf_lanes={lanes}',
                file=sys.stderr,
            )
            mismatch = True
        if got != expected:
            print(
                f'compare-compute: FAIL VEC[offset={offset}] rtl_result={got} perf_expected_result={expected}',
                file=sys.stderr,
            )
            mismatch = True

    print(
        f'compare-compute: compared GEMM={len(perf_gemm)} VEC={len(perf_vec)} '
        f'(rtl GEMM={len(rtl_gemm)} rtl VEC={len(rtl_vec)})'
    )
    if rtl_hash != perf_hash:
        print('compare-compute: FAIL canonical summary hash mismatch', file=sys.stderr)
        mismatch = True
    if mismatch:
        return 1
    print('compare-compute: OK')
    return 0


if __name__ == '__main__':
    sys.exit(main())
