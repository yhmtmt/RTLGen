#!/usr/bin/env python3
import argparse
import json
import struct
from pathlib import Path

import model

try:
    import yaml
except ImportError:  # pragma: no cover - optional dependency
    yaml = None

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


def _parse_int(value):
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value, 0)
    return int(value)


def _derive_sram_instances(arch, metrics):
    sram = arch.get("sram", {})
    instances = sram.get("instances", [])
    metrics_by_name = {}
    default_access = None
    if metrics:
        if "instances" in metrics:
            for inst in metrics.get("instances", []):
                name = inst.get("instance", {}).get("name")
                access_time_ns = inst.get("metrics", {}).get("access_time_ns")
                if name and access_time_ns is not None:
                    metrics_by_name[name] = float(access_time_ns)
        if "max_access_time_ns" in metrics:
            default_access = float(metrics["max_access_time_ns"])
    derived = []
    for inst in instances:
        name = inst.get("name")
        depth = int(inst["depth"])
        width = int(inst["width"])
        banks = int(inst.get("banks", 1))
        base_addr = _parse_int(inst.get("base_addr", 0))
        word_size_bytes = width // 8
        size_bytes = depth * word_size_bytes * banks
        access_time_ns = metrics_by_name.get(name, default_access)
        read_bw_gbps = None
        write_bw_gbps = None
        if access_time_ns and access_time_ns > 0:
            bytes_per_access = word_size_bytes * banks
            bw_gbps = (bytes_per_access / (access_time_ns * 1e-9)) / 1e9
            read_bw_gbps = bw_gbps
            write_bw_gbps = bw_gbps
        derived.append({
            "name": name,
            "base_addr": base_addr,
            "size_bytes": size_bytes,
            "word_size_bytes": word_size_bytes,
            "banks": banks,
            "access_time_ns": access_time_ns,
            "read_bw_gbps": read_bw_gbps,
            "write_bw_gbps": write_bw_gbps,
        })
    return derived


def _load_sram_model(cfg):
    metrics_path = cfg.get("sram_metrics_json")
    arch_path = cfg.get("sram_arch_yaml") or cfg.get("arch_yaml")
    if not arch_path:
        return
    if yaml is None:
        raise RuntimeError("PyYAML is required for sram_arch_yaml support.")
    arch = yaml.safe_load(Path(arch_path).read_text(encoding="utf-8"))
    metrics = None
    if metrics_path:
        metrics = json.loads(Path(metrics_path).read_text(encoding="utf-8"))
    cfg["sram_instances"] = _derive_sram_instances(arch, metrics)


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
            "duration_ns": model.dma_time_ns(size, cfg, src_addr=src, dst_addr=dst),
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
            "event_id": desc["tag"],
            "irq": bool(desc["flags"] & 0x1),
            "duration_ns": model.event_overhead_ns(cfg),
        })
    elif opcode == 0x21:  # EVENT_WAIT
        event.update({
            "name": "EVENT_WAIT",
            "event_id": desc["tag"],
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


def build_trace(descs, cfg, overlap):
    trace = []
    now_ns = 0.0
    warnings = []
    stats = {
        "total_bytes": 0,
        "dma_ops": 0,
        "gemm_ops": 0,
        "event_ops": 0,
        "noop_ops": 0,
        "unknown_ops": 0,
        "irq_events": 0,
        "dma_time_ns": 0.0,
        "gemm_time_ns": 0.0,
        "event_time_ns": 0.0,
        "noop_time_ns": 0.0,
        "unknown_time_ns": 0.0,
    }
    queue_time = 0.0
    dma_engine_time = 0.0
    gemm_engine_time = 0.0
    event_times = {}
    issue_overhead = float(cfg.get("issue_overhead_ns", 0.0))

    for desc in descs:
        event = desc_to_event(desc, cfg)
        dur = float(event.get("duration_ns", 0.0))
        if overlap:
            name = event.get("name")
            if name == "DMA_COPY":
                start = max(queue_time, dma_engine_time)
                end = start + dur
                dma_engine_time = end
                queue_time += issue_overhead
            elif name == "GEMM":
                start = max(queue_time, gemm_engine_time)
                end = start + dur
                gemm_engine_time = end
                queue_time += issue_overhead
            elif name == "EVENT_SIGNAL":
                start = queue_time
                end = start + dur
                queue_time = end
                event_times[event.get("event_id")] = end
            elif name == "EVENT_WAIT":
                wait_time = event_times.get(event.get("event_id"))
                if wait_time is None:
                    wait_time = 0.0
                    warnings.append(f"event_wait missing event_id {event.get('event_id')}")
                start = max(queue_time, wait_time)
                end = start + dur
                queue_time = end
            else:
                start = queue_time
                end = start + dur
                queue_time = end
            event["start_ns"] = start
            event["end_ns"] = end
        else:
            event["start_ns"] = now_ns
            event["end_ns"] = now_ns + dur
            now_ns += dur
        trace.append(event)

        name = event.get("name")
        if name == "DMA_COPY":
            stats["dma_ops"] += 1
            stats["total_bytes"] += int(event.get("bytes", 0))
            stats["dma_time_ns"] += dur
        elif name == "GEMM":
            stats["gemm_ops"] += 1
            stats["gemm_time_ns"] += dur
        elif name in ("EVENT_SIGNAL", "EVENT_WAIT"):
            stats["event_ops"] += 1
            stats["event_time_ns"] += dur
            if name == "EVENT_SIGNAL" and event.get("irq"):
                stats["irq_events"] += 1
        elif name == "NOOP":
            stats["noop_ops"] += 1
            stats["noop_time_ns"] += dur
        else:
            stats["unknown_ops"] += 1
            stats["unknown_time_ns"] += dur
            warnings.append(event.get("warning", "unknown opcode"))

        if name == "GEMM" and dur > 0.0:
            ops = 2.0 * float(event.get("m", 0)) * float(event.get("n", 0)) * float(event.get("k", 0))
            tops = ops / (dur * 1e-9) / 1e12
            event["achieved_tops"] = tops
        if name == "DMA_COPY" and dur > 0.0:
            gbps = float(event.get("bytes", 0)) / (dur * 1e-9) / 1e9
            event["achieved_gbps"] = gbps

    total_ns = now_ns
    if overlap:
        total_ns = max(queue_time, dma_engine_time, gemm_engine_time)
        stats["queue_time_ns"] = queue_time
        stats["dma_engine_time_ns"] = dma_engine_time
        stats["gemm_engine_time_ns"] = gemm_engine_time
    return trace, total_ns, stats, warnings


def format_summary(stats, warnings):
    lines = []
    lines.append("NPU perf summary")
    lines.append(f"  total_time_ns: {stats['total_time_ns']:.3f}")
    lines.append(f"  total_bytes: {stats['total_bytes']}")
    lines.append(f"  dma_ops: {stats['dma_ops']} (time_ns={stats['dma_time_ns']:.3f})")
    lines.append(f"  gemm_ops: {stats['gemm_ops']} (time_ns={stats['gemm_time_ns']:.3f})")
    lines.append(f"  event_ops: {stats['event_ops']} (time_ns={stats['event_time_ns']:.3f})")
    lines.append(f"  noop_ops: {stats['noop_ops']} (time_ns={stats['noop_time_ns']:.3f})")
    lines.append(f"  unknown_ops: {stats['unknown_ops']} (time_ns={stats['unknown_time_ns']:.3f})")
    if warnings:
        lines.append(f"  warnings: {len(warnings)}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="NPU performance simulator (v0.1)")
    ap.add_argument("--bin", required=True, help="Path to descriptor .bin stream")
    ap.add_argument("--out", required=True, help="Path to JSON trace output")
    ap.add_argument("--config", help="Optional model config JSON")
    ap.add_argument("--summary", action="store_true", help="Print summary to stdout")
    ap.add_argument("--overlap", action="store_true", help="Enable DMA/compute overlap model")
    args = ap.parse_args()

    cfg = {}
    if args.config:
        cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
        _load_sram_model(cfg)

    data = Path(args.bin).read_bytes()
    descs = parse_desc_stream(data)
    trace, total_ns, stats, warnings = build_trace(descs, cfg, args.overlap)

    out = {
        "meta": {
            "version": "0.1",
            "source_bin": str(args.bin),
            "mode": "overlap" if args.overlap else "sequential",
        },
        "stats": {
            **stats,
            "total_time_ns": total_ns,
        },
        "warnings": warnings,
        "trace": trace,
    }
    Path(args.out).write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"wrote trace to {args.out}")
    if args.summary:
        print(format_summary(out["stats"], warnings))


if __name__ == "__main__":
    main()
