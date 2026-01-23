#!/usr/bin/env python3
import argparse
import json
import struct
from pathlib import Path

import model


def parse_desc_stream(data):
    descs = []
    for off in range(0, len(data), 32):
        chunk = data[off:off + 32]
        if len(chunk) < 32:
            break
        opcode = chunk[0]
        flags = chunk[1]
        size_units = chunk[2]
        tag = struct.unpack_from("<I", chunk, 4)[0]
        descs.append({
            "offset": off,
            "opcode": opcode,
            "flags": flags,
            "size_units": size_units,
            "tag": tag,
            "raw": chunk,
        })
    return descs


def decode_gemm_tag(tag):
    m = (tag >> 20) & 0xFFF
    n = (tag >> 10) & 0x3FF
    k = tag & 0x3FF
    return m, n, k


def desc_to_event(desc, cfg):
    opcode = desc["opcode"]
    raw = desc["raw"]
    event = {
        "offset": desc["offset"],
        "opcode": opcode,
        "tag": desc["tag"],
        "flags": desc["flags"],
    }
    if opcode == 0x01:  # DMA_COPY
        src = struct.unpack_from("<Q", raw, 8)[0]
        dst = struct.unpack_from("<Q", raw, 16)[0]
        size = struct.unpack_from("<I", raw, 24)[0]
        event.update({
            "name": "DMA_COPY",
            "src": f"0x{src:016x}",
            "dst": f"0x{dst:016x}",
            "bytes": size,
            "duration_ns": model.dma_time_ns(size, cfg),
        })
    elif opcode == 0x10:  # GEMM
        a = struct.unpack_from("<Q", raw, 8)[0]
        b = struct.unpack_from("<Q", raw, 16)[0]
        c = struct.unpack_from("<Q", raw, 24)[0]
        m, n, k = decode_gemm_tag(desc["tag"])
        event.update({
            "name": "GEMM",
            "a": f"0x{a:016x}",
            "b": f"0x{b:016x}",
            "c": f"0x{c:016x}",
            "m": m,
            "n": n,
            "k": k,
            "duration_ns": model.gemm_time_ns(m, n, k, cfg),
        })
    elif opcode == 0x20:  # EVENT_SIGNAL
        event.update({
            "name": "EVENT_SIGNAL",
            "duration_ns": model.event_overhead_ns(cfg),
        })
    elif opcode == 0x21:  # EVENT_WAIT
        event.update({
            "name": "EVENT_WAIT",
            "duration_ns": model.event_overhead_ns(cfg),
        })
    elif opcode == 0x30:  # NOOP
        event.update({
            "name": "NOOP",
            "duration_ns": model.noop_overhead_ns(cfg),
        })
    else:
        event.update({
            "name": "UNKNOWN",
            "duration_ns": 0.0,
            "warning": f"unsupported opcode 0x{opcode:02x}",
        })
    return event


def build_trace(descs, cfg):
    trace = []
    now_ns = 0.0
    stats = {
        "total_bytes": 0,
        "dma_ops": 0,
        "gemm_ops": 0,
        "event_ops": 0,
        "noop_ops": 0,
        "unknown_ops": 0,
    }

    for desc in descs:
        event = desc_to_event(desc, cfg)
        dur = float(event.get("duration_ns", 0.0))
        event["start_ns"] = now_ns
        event["end_ns"] = now_ns + dur
        now_ns += dur
        trace.append(event)

        name = event.get("name")
        if name == "DMA_COPY":
            stats["dma_ops"] += 1
            stats["total_bytes"] += int(event.get("bytes", 0))
        elif name == "GEMM":
            stats["gemm_ops"] += 1
        elif name in ("EVENT_SIGNAL", "EVENT_WAIT"):
            stats["event_ops"] += 1
        elif name == "NOOP":
            stats["noop_ops"] += 1
        else:
            stats["unknown_ops"] += 1

    return trace, now_ns, stats


def main():
    ap = argparse.ArgumentParser(description="NPU performance simulator (v0.1)")
    ap.add_argument("--bin", required=True, help="Path to descriptor .bin stream")
    ap.add_argument("--out", required=True, help="Path to JSON trace output")
    ap.add_argument("--config", help="Optional model config JSON")
    args = ap.parse_args()

    cfg = {}
    if args.config:
        cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))

    data = Path(args.bin).read_bytes()
    descs = parse_desc_stream(data)
    trace, total_ns, stats = build_trace(descs, cfg)

    out = {
        "meta": {
            "version": "0.1",
            "source_bin": str(args.bin),
        },
        "stats": {
            **stats,
            "total_time_ns": total_ns,
        },
        "trace": trace,
    }
    Path(args.out).write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"wrote trace to {args.out}")


if __name__ == "__main__":
    main()
