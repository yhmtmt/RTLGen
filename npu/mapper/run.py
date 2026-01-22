#!/usr/bin/env python3
import argparse
import struct
import sys
from typing import Any, Dict, List

import yaml  # type: ignore

from validate import validate_file


OPCODES = {
    "dma_copy": 0x01,
    "dma_strided": 0x02,
    "dma_gather": 0x03,
    "dma_scatter": 0x04,
    "gemm": 0x10,
    "vec_op": 0x11,
    "softmax": 0x12,
    "event_signal": 0x20,
    "event_wait": 0x21,
    "noop": 0x30,
}

DTYPE_FLAGS = {
    "int8": 0x0,
    "fp16": 0x1,
    "bf16": 0x2,
    "fp8": 0x3,
}

LAYOUT_FLAGS = {
    "row_major": 0x0,
    "col_major": 0x1,
}


def pack_mnk(m: int, n: int, k: int) -> int:
    if not (0 <= m <= 0xFFF):
        raise ValueError("gemm m must fit in 12 bits for v0.1")
    if not (0 <= n <= 0x3FF):
        raise ValueError("gemm n must fit in 10 bits for v0.1")
    if not (0 <= k <= 0x3FF):
        raise ValueError("gemm k must fit in 10 bits for v0.1")
    return (m << 20) | (n << 10) | k


def build_buffer_map(doc: Dict[str, Any]) -> Dict[str, int]:
    buffers = doc.get("buffers", [])
    buf_map: Dict[str, int] = {}
    for buf in buffers:
        buf_id = buf["id"]
        addr = int(buf["addr"])
        buf_map[buf_id] = addr
    return buf_map


def emit_desc(op: Dict[str, Any], buf_map: Dict[str, int]) -> Dict[str, Any]:
    otype = op["type"]
    desc: Dict[str, Any] = {
        "opcode": OPCODES[otype],
        "flags": 0,
        "size": 1,
        "tag": 0,
        "fields": {},
    }

    if otype == "dma_copy":
        desc["fields"] = {
            "src_addr": buf_map[op["src"]],
            "dst_addr": buf_map[op["dst"]],
            "size": int(op["bytes"]),
        }
    elif otype == "dma_strided":
        desc["fields"] = {
            "src_addr": buf_map[op["src"]],
            "dst_addr": buf_map[op["dst"]],
            "row_bytes": int(op["row_bytes"]),
            "rows": int(op["rows"]),
            "src_stride": int(op["src_stride"]),
            "dst_stride": int(op["dst_stride"]),
        }
    elif otype in ("dma_gather", "dma_scatter"):
        desc["fields"] = {
            "list_addr": int(op["list_addr"]),
            "list_count": int(op["list_count"]),
            "elem_size": int(op["elem_size"]),
        }
    elif otype == "gemm":
        dtype = DTYPE_FLAGS[op["dtype"]]
        layout = LAYOUT_FLAGS[op["layout"]]
        desc["flags"] = (layout << 4) | dtype
        desc["tag"] = pack_mnk(int(op["m"]), int(op["n"]), int(op["k"]))
        desc["fields"] = {
            "a_addr": buf_map[op["a"]],
            "b_addr": buf_map[op["b"]],
            "c_addr": buf_map[op["c"]],
        }
    elif otype == "vec_op":
        desc["fields"] = {
            "src_addr": buf_map[op["src"]],
            "dst_addr": buf_map[op["dst"]],
            "size": int(op["bytes"]),
            "op": op["op"],
            "dtype": op["dtype"],
        }
    elif otype == "softmax":
        desc["fields"] = {
            "src_addr": buf_map[op["src"]],
            "dst_addr": buf_map[op["dst"]],
            "row_bytes": int(op["row_bytes"]),
            "rows": int(op["rows"]),
            "dtype": op["dtype"],
        }
    elif otype == "event_signal":
        desc["flags"] = 1 if op.get("irq") else 0
        desc["tag"] = int(op["event_id"])
    elif otype == "event_wait":
        desc["tag"] = int(op["event_id"])
    elif otype == "noop":
        pass
    else:
        raise ValueError(f"unknown op type {otype}")

    desc["comment"] = op.get("id", "")
    return desc


def pack_descriptor(desc: Dict[str, Any]) -> bytes:
    data = bytearray(32)
    opcode = int(desc["opcode"]) & 0xFF
    flags = int(desc["flags"]) & 0xFF
    size = int(desc["size"]) & 0xFF
    tag = int(desc["tag"]) & 0xFFFFFFFF
    struct.pack_into("<BBBBI", data, 0, opcode, flags, size, 0, tag)

    fields = desc.get("fields", {})
    if opcode == OPCODES["dma_copy"]:
        struct.pack_into("<QQI", data, 8, int(fields["src_addr"]), int(fields["dst_addr"]), int(fields["size"]))
    elif opcode == OPCODES["dma_strided"]:
        struct.pack_into(
            "<QQHHBB",
            data,
            8,
            int(fields["src_addr"]),
            int(fields["dst_addr"]),
            int(fields["row_bytes"]) & 0xFFFF,
            int(fields["rows"]) & 0xFFFF,
            int(fields["src_stride"]) & 0xFF,
            int(fields["dst_stride"]) & 0xFF,
        )
    elif opcode in (OPCODES["dma_gather"], OPCODES["dma_scatter"]):
        struct.pack_into(
            "<QII",
            data,
            8,
            int(fields["list_addr"]),
            int(fields["list_count"]) & 0xFFFFFFFF,
            int(fields["elem_size"]) & 0xFFFFFFFF,
        )
    elif opcode == OPCODES["gemm"]:
        struct.pack_into(
            "<QQQ",
            data,
            8,
            int(fields["a_addr"]),
            int(fields["b_addr"]),
            int(fields["c_addr"]),
        )
    elif opcode == OPCODES["vec_op"]:
        struct.pack_into(
            "<QQI",
            data,
            8,
            int(fields["src_addr"]),
            int(fields["dst_addr"]),
            int(fields["size"]),
        )
    elif opcode == OPCODES["softmax"]:
        struct.pack_into(
            "<QQHH",
            data,
            8,
            int(fields["src_addr"]),
            int(fields["dst_addr"]),
            int(fields["row_bytes"]) & 0xFFFF,
            int(fields["rows"]) & 0xFFFF,
        )
    else:
        pass

    return bytes(data)


def expand_deps(doc: Dict[str, Any], ops: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    deps = doc.get("deps", [])
    if not deps:
        return ops

    wait_map: Dict[str, List[int]] = {}
    next_event = 1
    for dep in deps:
        waits = dep.get("wait", [])
        for w in waits:
            wait_map.setdefault(w, [])
        for w in waits:
            wait_map[w].append(next_event)
            next_event += 1

    expanded: List[Dict[str, Any]] = []
    for op in ops:
        expanded.append(op)
        for event_id in wait_map.get(op["id"], []):
            expanded.append({"id": f"{op['id']}_signal_{event_id}", "type": "event_signal", "event_id": event_id})

    final: List[Dict[str, Any]] = []
    for op in expanded:
        op_id = op.get("id")
        if not op_id:
            final.append(op)
            continue
        for dep in deps:
            if dep.get("then") == op_id:
                for w in dep.get("wait", []):
                    idx = wait_map[w].pop(0)
                    final.append({"id": f"{op_id}_wait_{idx}", "type": "event_wait", "event_id": idx})
        final.append(op)
    return final


def insert_signal_events(doc: Dict[str, Any], ops: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    events = doc.get("events", [])
    if not events:
        return ops
    signal_map: Dict[str, List[Dict[str, Any]]] = {}
    for ev in events:
        signal_map.setdefault(ev["signal_on"], []).append(ev)

    out: List[Dict[str, Any]] = []
    for op in ops:
        out.append(op)
        for ev in signal_map.get(op.get("id", ""), []):
            out.append(
                {
                    "id": f"event_{ev['id']}",
                    "type": "event_signal",
                    "event_id": ev["id"],
                    "irq": bool(ev.get("irq", False)),
                }
            )
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Map a schedule IR to shell commands.")
    parser.add_argument("schedule", help="Path to schedule.yml")
    parser.add_argument("--arch", help="Optional arch.yml path (overrides schedule)")
    parser.add_argument("--dry-run", action="store_true", help="Validate only")
    parser.add_argument("--out", help="Write descriptors to a YAML file")
    parser.add_argument("--out-bin", help="Write binary 32B descriptor stream")
    args = parser.parse_args()

    try:
        doc = validate_file(args.schedule)
    except Exception as exc:
        print(f"mapper: {exc}", file=sys.stderr)
        return 1

    if args.arch:
        doc["arch"] = args.arch

    if args.dry_run:
        print("mapper: schedule validated")
        return 0

    buf_map = build_buffer_map(doc)
    ops = doc.get("ops", [])
    ops = expand_deps(doc, ops)
    ops = insert_signal_events(doc, ops)

    descs = [emit_desc(op, buf_map) for op in ops]
    out_doc = {"version": 0.1, "descriptors": descs}

    if args.out_bin:
        with open(args.out_bin, "wb") as f:
            for desc in descs:
                f.write(pack_descriptor(desc))
        print(f"mapper: wrote {len(descs)} descriptors to {args.out_bin}")

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            yaml.safe_dump(out_doc, f, sort_keys=False)
        print(f"mapper: wrote {len(descs)} descriptors to {args.out}")
        return 0
    if args.out_bin:
        return 0
    else:
        print(yaml.safe_dump(out_doc, sort_keys=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
