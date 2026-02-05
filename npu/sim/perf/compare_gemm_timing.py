#!/usr/bin/env python3
import argparse
import json
import sys

def main() -> int:
    ap = argparse.ArgumentParser(description="Compare GEMM timing between RTL sim and perf model trace.")
    ap.add_argument("--rtl-cycles", type=int, required=True, help="Measured RTL cycles")
    ap.add_argument("--clk-ns", type=float, default=10.0, help="RTL clock period in ns")
    ap.add_argument("--perf-trace", required=True, help="Perf trace JSON file")
    ap.add_argument("--tolerance", type=float, default=0.2, help="Relative tolerance")
    args = ap.parse_args()

    with open(args.perf_trace, "r", encoding="utf-8") as f:
        trace = json.load(f)

    gemm = None
    for ev in trace.get("trace", []):
        if ev.get("name") == "GEMM":
            gemm = ev
            break
    if gemm is None:
        print("compare: no GEMM event in trace", file=sys.stderr)
        return 2

    perf_ns = float(gemm.get("duration_ns", 0.0))
    rtl_ns = float(args.rtl_cycles) * float(args.clk_ns)
    if perf_ns <= 0:
        print("compare: perf GEMM duration is zero", file=sys.stderr)
        return 2

    delta = abs(rtl_ns - perf_ns) / perf_ns
    print(f"compare: rtl_ns={rtl_ns:.3f} perf_ns={perf_ns:.3f} delta={delta:.3f}")
    if delta > args.tolerance:
        print("compare: FAIL (outside tolerance)", file=sys.stderr)
        return 1
    print("compare: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
