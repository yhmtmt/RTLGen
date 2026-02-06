#!/usr/bin/env python3
import argparse
import json
import re
import sys
from typing import Optional


def _parse_rtl_entries_from_log(path: str) -> list[dict]:
    pat_uid = re.compile(
        r"\bGEMM_TIMING\b.*\bindex=(\d+)\b.*\bop_uid=0x([0-9a-fA-F]+)\b.*\btag=0x([0-9a-fA-F]+)\b.*\boffset=(-?\d+)\b.*\bcycles=(\d+)\b"
    )
    pat_full = re.compile(
        r"\bGEMM_TIMING\b.*\bindex=(\d+)\b.*\btag=0x([0-9a-fA-F]+)\b.*\boffset=(-?\d+)\b.*\bcycles=(\d+)\b"
    )
    pat_legacy = re.compile(r"\bGEMM_TIMING\b.*\bcycles=(\d+)\b")
    entries = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            m = pat_uid.search(line)
            if m:
                entries.append(
                    {
                        "index": int(m.group(1)),
                        "op_uid": int(m.group(2), 16),
                        "tag": int(m.group(3), 16),
                        "offset": int(m.group(4)),
                        "cycles": int(m.group(5)),
                    }
                )
                continue
            m = pat_full.search(line)
            if m:
                entries.append(
                    {
                        "index": int(m.group(1)),
                        "op_uid": None,
                        "tag": int(m.group(2), 16),
                        "offset": int(m.group(3)),
                        "cycles": int(m.group(4)),
                    }
                )
                continue
            m = pat_legacy.search(line)
            if m:
                entries.append(
                    {
                        "index": len(entries) + 1,
                        "op_uid": None,
                        "tag": None,
                        "offset": None,
                        "cycles": int(m.group(1)),
                    }
                )
    if not entries:
        raise ValueError("no GEMM_TIMING cycles entry found in RTL log")
    return entries


def _choose_matching_mode(rtl_entries: list[dict], perf_entries: list[dict]) -> str:
    rtl_uids = [e["op_uid"] for e in rtl_entries]
    perf_uids = [e["op_uid"] for e in perf_entries]
    if all(u is not None for u in rtl_uids + perf_uids):
        if len(set(rtl_uids)) == len(rtl_uids) and len(set(perf_uids)) == len(perf_uids):
            if set(rtl_uids) == set(perf_uids):
                return "op_uid"

    rtl_tags = [e["tag"] for e in rtl_entries]
    perf_tags = [e["tag"] for e in perf_entries]
    if all(t is not None for t in rtl_tags + perf_tags):
        if len(set(rtl_tags)) == len(rtl_tags) and len(set(perf_tags)) == len(perf_tags):
            if set(rtl_tags) == set(perf_tags):
                return "tag"

    rtl_offsets = [e["offset"] for e in rtl_entries]
    perf_offsets = [e["offset"] for e in perf_entries]
    if all(o is not None for o in rtl_offsets + perf_offsets):
        if len(set(rtl_offsets)) == len(rtl_offsets) and len(set(perf_offsets)) == len(perf_offsets):
            if set(rtl_offsets) == set(perf_offsets):
                return "offset"

    return "index"


def _match_entries(rtl_entries: list[dict], perf_entries: list[dict], mode: str) -> list[tuple[dict, dict]]:
    if mode == "op_uid":
        perf_by_uid = {int(e["op_uid"]): e for e in perf_entries}
        return [(rtl, perf_by_uid[int(rtl["op_uid"])]) for rtl in rtl_entries]
    if mode == "tag":
        perf_by_tag = {int(e["tag"]): e for e in perf_entries}
        return [(rtl, perf_by_tag[int(rtl["tag"])]) for rtl in rtl_entries]
    if mode == "offset":
        perf_by_offset = {int(e["offset"]): e for e in perf_entries}
        return [(rtl, perf_by_offset[int(rtl["offset"])]) for rtl in rtl_entries]
    return list(zip(rtl_entries, perf_entries))


def _parse_int_value(v):
    if isinstance(v, int):
        return v
    if isinstance(v, str):
        return int(v, 0)
    return int(v)


def _load_tolerance_map(path: Optional[str]) -> dict[int, float]:
    if not path:
        return {}
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    if not isinstance(raw, dict):
        raise ValueError("tolerance map JSON must be an object")
    out = {}
    for k, v in raw.items():
        out[_parse_int_value(k)] = float(v)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Compare GEMM timing between RTL sim and perf model trace.")
    ap.add_argument("--rtl-cycles", type=int, default=None, help="Measured RTL cycles")
    ap.add_argument("--rtl-log", default=None, help="RTL sim log containing GEMM_TIMING cycles=<N>")
    ap.add_argument("--clk-ns", type=float, default=10.0, help="RTL clock period in ns")
    ap.add_argument("--perf-trace", required=True, help="Perf trace JSON file")
    ap.add_argument("--tolerance", type=float, default=0.2, help="Relative tolerance")
    ap.add_argument("--tolerance-map", default=None, help="Optional JSON mapping id->relative tolerance")
    ap.add_argument(
        "--require-order-change",
        action="store_true",
        help="Fail if GEMM completion order in RTL matches perf issue order (mode must not be index)",
    )
    args = ap.parse_args()

    if args.rtl_log:
        try:
            rtl_entries = _parse_rtl_entries_from_log(args.rtl_log)
        except ValueError as e:
            print(f"compare: {e}", file=sys.stderr)
            return 2
    elif args.rtl_cycles is not None:
        rtl_entries = [{"index": 1, "op_uid": None, "tag": None, "offset": None, "cycles": args.rtl_cycles}]
    else:
        print("compare: pass either --rtl-log or --rtl-cycles", file=sys.stderr)
        return 2

    with open(args.perf_trace, "r", encoding="utf-8") as f:
        trace = json.load(f)

    perf_entries = []
    perf_idx = 0
    for ev in trace.get("trace", []):
        if ev.get("name") == "GEMM":
            perf_idx += 1
            perf_entries.append(
                {
                    "index": perf_idx,
                    "op_uid": int(ev["op_uid"]) if "op_uid" in ev else None,
                    "tag": int(ev["tag"]) if "tag" in ev else None,
                    "offset": int(ev["offset"]) if "offset" in ev else None,
                    "perf_ns": float(ev.get("duration_ns", 0.0)),
                }
            )
    if not perf_entries:
        print("compare: no GEMM event in trace", file=sys.stderr)
        return 2

    if len(rtl_entries) != len(perf_entries):
        print(
            "compare: GEMM count mismatch "
            f"(rtl={len(rtl_entries)} perf={len(perf_entries)})",
            file=sys.stderr,
        )
        return 2

    mode = _choose_matching_mode(rtl_entries, perf_entries)
    if mode == "index":
        print("compare: warning: falling back to index-based GEMM matching")
    else:
        print(f"compare: matching GEMM ops by {mode}")
    matched = _match_entries(rtl_entries, perf_entries, mode)
    try:
        tol_map = _load_tolerance_map(args.tolerance_map)
    except ValueError as e:
        print(f"compare: {e}", file=sys.stderr)
        return 2

    if mode != "index":
        rtl_order = [int(e[mode]) for e in rtl_entries]
        perf_order = [int(e[mode]) for e in perf_entries]
        if rtl_order != perf_order:
            print("compare: info: GEMM order differs between RTL completion and perf issue order")
            print(f"compare: rtl_order={rtl_order}")
            print(f"compare: perf_order={perf_order}")
        else:
            print("compare: info: GEMM order is identical between RTL and perf")
        if args.require_order_change and rtl_order == perf_order:
            print("compare: FAIL expected reordered GEMM completion, but order is unchanged", file=sys.stderr)
            return 1
    elif args.require_order_change:
        print("compare: FAIL --require-order-change needs non-index matching mode", file=sys.stderr)
        return 2

    max_delta = 0.0
    for rtl, perf in matched:
        rtl_cycles = int(rtl["cycles"])
        perf_ns = float(perf["perf_ns"])
        label = f"{mode}={rtl[mode]}" if mode in ("op_uid", "tag", "offset") and rtl.get(mode) is not None else f"index={rtl['index']}"
        tol_key = int(rtl[mode]) if mode in ("op_uid", "tag", "offset") and rtl.get(mode) is not None else int(rtl["index"])
        tol = float(tol_map.get(tol_key, args.tolerance))
        if perf_ns <= 0:
            print(f"compare: perf GEMM[{label}] duration is zero", file=sys.stderr)
            return 2
        rtl_ns = float(rtl_cycles) * float(args.clk_ns)
        delta = abs(rtl_ns - perf_ns) / perf_ns
        max_delta = max(max_delta, delta)
        print(
            f"compare: GEMM[{label}] rtl_cycles={rtl_cycles} rtl_ns={rtl_ns:.3f} "
            f"perf_ns={perf_ns:.3f} delta={delta:.3f} tol={tol:.3f}"
        )
        if delta > tol:
            print(f"compare: FAIL at GEMM[{label}] (outside tolerance)", file=sys.stderr)
            return 1
    print(f"compare: compared {len(perf_entries)} GEMM op(s), max_delta={max_delta:.3f}")
    print("compare: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
