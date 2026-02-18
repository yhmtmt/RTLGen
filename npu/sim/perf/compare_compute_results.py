#!/usr/bin/env python3
import argparse
import json
import re
import sys


def _parse_rtl_log(path: str) -> tuple[dict[int, int], dict[int, int]]:
    gemm_pat = re.compile(r"\bGEMM_TIMING\b.*\boffset=(-?\d+)\b.*\baccum=(-?\d+)\b")
    vec_pat = re.compile(r"\bVEC_DONE\b.*\boffset=(-?\d+)\b.*\bresult=0x([0-9a-fA-F]+)\b")

    gemm_by_offset: dict[int, int] = {}
    vec_by_offset: dict[int, int] = {}

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            gm = gemm_pat.search(line)
            if gm:
                offset = int(gm.group(1))
                accum = int(gm.group(2))
                if offset in gemm_by_offset:
                    raise ValueError(f"duplicate GEMM completion offset in RTL log: {offset}")
                gemm_by_offset[offset] = accum
                continue
            vm = vec_pat.search(line)
            if vm:
                offset = int(vm.group(1))
                result = int(vm.group(2), 16)
                if offset in vec_by_offset:
                    raise ValueError(f"duplicate VEC completion offset in RTL log: {offset}")
                vec_by_offset[offset] = result
    return gemm_by_offset, vec_by_offset


def _load_perf_expectations(path: str) -> tuple[dict[int, int], dict[int, tuple[int, int]]]:
    with open(path, "r", encoding="utf-8") as f:
        trace = json.load(f)

    gemm_expected: dict[int, int] = {}
    vec_expected: dict[int, tuple[int, int]] = {}

    for event in trace.get("trace", []):
        name = event.get("name")
        if name == "GEMM":
            if "offset" not in event:
                raise ValueError("perf GEMM event missing offset")
            if "expected_accum" not in event:
                raise ValueError("perf GEMM event missing expected_accum")
            offset = int(event["offset"])
            if offset in gemm_expected:
                raise ValueError(f"duplicate GEMM offset in perf trace: {offset}")
            gemm_expected[offset] = int(event["expected_accum"])
        elif name == "VEC_OP":
            if "offset" not in event:
                raise ValueError("perf VEC_OP event missing offset")
            if "expected_result" not in event:
                raise ValueError("perf VEC_OP event missing expected_result")
            lanes = int(event.get("lanes", 8))
            if lanes < 1:
                lanes = 1
            if lanes > 8:
                lanes = 8
            offset = int(event["offset"])
            expected_result = int(event["expected_result"], 0)
            if offset in vec_expected:
                raise ValueError(f"duplicate VEC offset in perf trace: {offset}")
            vec_expected[offset] = (expected_result, lanes)

    return gemm_expected, vec_expected


def _format_offsets(offsets: list[int]) -> str:
    if not offsets:
        return "[]"
    return "[" + ", ".join(str(x) for x in sorted(offsets)) + "]"


def main() -> int:
    ap = argparse.ArgumentParser(description="Compare GEMM/VEC compute results between RTL log and perf trace.")
    ap.add_argument("--rtl-log", required=True, help="RTL sim log with GEMM_TIMING/VEC_DONE lines")
    ap.add_argument("--perf-trace", required=True, help="Perf trace JSON file")
    args = ap.parse_args()

    try:
        rtl_gemm, rtl_vec = _parse_rtl_log(args.rtl_log)
        perf_gemm, perf_vec = _load_perf_expectations(args.perf_trace)
    except ValueError as e:
        print(f"compare-compute: {e}", file=sys.stderr)
        return 2

    if not perf_gemm and not perf_vec:
        print("compare-compute: no GEMM or VEC_OP events in perf trace", file=sys.stderr)
        return 2

    mismatch = False

    missing_gemm = sorted(set(perf_gemm.keys()) - set(rtl_gemm.keys()))
    extra_gemm = sorted(set(rtl_gemm.keys()) - set(perf_gemm.keys()))
    if missing_gemm:
        print(f"compare-compute: missing GEMM completions in RTL log offsets={_format_offsets(missing_gemm)}", file=sys.stderr)
        mismatch = True
    if extra_gemm:
        print(f"compare-compute: extra GEMM completions in RTL log offsets={_format_offsets(extra_gemm)}", file=sys.stderr)
        mismatch = True

    missing_vec = sorted(set(perf_vec.keys()) - set(rtl_vec.keys()))
    extra_vec = sorted(set(rtl_vec.keys()) - set(perf_vec.keys()))
    if missing_vec:
        print(f"compare-compute: missing VEC completions in RTL log offsets={_format_offsets(missing_vec)}", file=sys.stderr)
        mismatch = True
    if extra_vec:
        print(f"compare-compute: extra VEC completions in RTL log offsets={_format_offsets(extra_vec)}", file=sys.stderr)
        mismatch = True

    for offset in sorted(set(perf_gemm.keys()) & set(rtl_gemm.keys())):
        expected = int(perf_gemm[offset])
        got = int(rtl_gemm[offset])
        print(f"compare-compute: GEMM[offset={offset}] rtl_accum={got} perf_expected_accum={expected}")
        if got != expected:
            print(
                f"compare-compute: FAIL GEMM[offset={offset}] rtl_accum={got} perf_expected_accum={expected}",
                file=sys.stderr,
            )
            mismatch = True

    for offset in sorted(set(perf_vec.keys()) & set(rtl_vec.keys())):
        expected_raw, lanes = perf_vec[offset]
        lane_bits = lanes * 8
        mask = (1 << lane_bits) - 1 if lane_bits < 64 else 0xFFFF_FFFF_FFFF_FFFF
        expected = int(expected_raw) & mask
        got = int(rtl_vec[offset]) & mask
        width = max(2, lanes * 2)
        print(
            f"compare-compute: VEC[offset={offset}] rtl_result=0x{got:0{width}x} "
            f"perf_expected_result=0x{expected:0{width}x} lanes={lanes}"
        )
        if got != expected:
            print(
                f"compare-compute: FAIL VEC[offset={offset}] rtl_result=0x{got:0{width}x} "
                f"perf_expected_result=0x{expected:0{width}x}",
                file=sys.stderr,
            )
            mismatch = True

    print(
        f"compare-compute: compared GEMM={len(perf_gemm)} VEC={len(perf_vec)} "
        f"(rtl GEMM={len(rtl_gemm)} rtl VEC={len(rtl_vec)})"
    )
    if mismatch:
        return 1
    print("compare-compute: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
