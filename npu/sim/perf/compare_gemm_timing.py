#!/usr/bin/env python3
import argparse
import json
import re
import sys


def _parse_rtl_cycles_from_log(path: str) -> list[int]:
    pat = re.compile(r"\bGEMM_TIMING\b.*\bcycles=(\d+)\b")
    cycles = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            m = pat.search(line)
            if m:
                cycles.append(int(m.group(1)))
    if not cycles:
        raise ValueError("no GEMM_TIMING cycles entry found in RTL log")
    return cycles


def main() -> int:
    ap = argparse.ArgumentParser(description="Compare GEMM timing between RTL sim and perf model trace.")
    ap.add_argument("--rtl-cycles", type=int, default=None, help="Measured RTL cycles")
    ap.add_argument("--rtl-log", default=None, help="RTL sim log containing GEMM_TIMING cycles=<N>")
    ap.add_argument("--clk-ns", type=float, default=10.0, help="RTL clock period in ns")
    ap.add_argument("--perf-trace", required=True, help="Perf trace JSON file")
    ap.add_argument("--tolerance", type=float, default=0.2, help="Relative tolerance")
    args = ap.parse_args()

    if args.rtl_log:
        try:
            rtl_cycles_list = _parse_rtl_cycles_from_log(args.rtl_log)
        except ValueError as e:
            print(f"compare: {e}", file=sys.stderr)
            return 2
    elif args.rtl_cycles is not None:
        rtl_cycles_list = [args.rtl_cycles]
    else:
        print("compare: pass either --rtl-log or --rtl-cycles", file=sys.stderr)
        return 2

    with open(args.perf_trace, "r", encoding="utf-8") as f:
        trace = json.load(f)

    perf_ns_list = []
    for ev in trace.get("trace", []):
        if ev.get("name") == "GEMM":
            perf_ns_list.append(float(ev.get("duration_ns", 0.0)))
    if not perf_ns_list:
        print("compare: no GEMM event in trace", file=sys.stderr)
        return 2

    if len(rtl_cycles_list) != len(perf_ns_list):
        print(
            "compare: GEMM count mismatch "
            f"(rtl={len(rtl_cycles_list)} perf={len(perf_ns_list)})",
            file=sys.stderr,
        )
        return 2

    max_delta = 0.0
    idx = 0
    for rtl_cycles, perf_ns in zip(rtl_cycles_list, perf_ns_list):
        idx += 1
        if perf_ns <= 0:
            print(f"compare: perf GEMM[{idx}] duration is zero", file=sys.stderr)
            return 2
        rtl_ns = float(rtl_cycles) * float(args.clk_ns)
        delta = abs(rtl_ns - perf_ns) / perf_ns
        max_delta = max(max_delta, delta)
        print(
            f"compare: GEMM[{idx}] rtl_cycles={rtl_cycles} rtl_ns={rtl_ns:.3f} "
            f"perf_ns={perf_ns:.3f} delta={delta:.3f}"
        )
        if delta > args.tolerance:
            print(f"compare: FAIL at GEMM[{idx}] (outside tolerance)", file=sys.stderr)
            return 1
    print(f"compare: compared {len(perf_ns_list)} GEMM op(s), max_delta={max_delta:.3f}")
    print("compare: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
