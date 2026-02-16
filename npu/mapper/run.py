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

EPILOGUE_FLAGS = {
    "none": 0x0,
    "relu": 0x1,
    "gelu": 0x2,
    "add": 0x3,
    "mul": 0x4,
}

VEC_OP_FLAGS = {
    "relu": 0x0,
    "add": 0x1,
    "mul": 0x2,
    "gelu": 0x3,
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
        addr = buf["addr"]
        if isinstance(addr, str):
            addr_int = int(addr, 0)
        else:
            addr_int = int(addr)
        buf_map[buf_id] = addr_int
    return buf_map


def emit_desc(op: Dict[str, Any], buf_map: Dict[str, int], default_gemm_uid: int = 0) -> Dict[str, Any]:
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
        use_v2 = bool(op.get("gemm_v2")) or any(
            key in op for key in ("lda", "ldb", "ldc", "alpha", "beta", "bias", "epilogue", "transpose_a", "transpose_b")
        )
        if use_v2:
            epilogue = EPILOGUE_FLAGS.get(str(op.get("epilogue", "none")).lower(), 0)
            transpose_a = 1 if op.get("transpose_a") else 0
            transpose_b = 1 if op.get("transpose_b") else 0
            has_bias = 1 if op.get("bias") else 0
            has_alpha = 1 if op.get("alpha") is not None else 0
            has_beta = 1 if op.get("beta") is not None else 0
            user_tag = int(op.get("user_tag", 0)) & 0xFFFF
            gemm_ext = (
                (epilogue & 0xF)
                | (transpose_a << 4)
                | (transpose_b << 5)
                | (has_bias << 6)
                | (has_alpha << 7)
                | (has_beta << 8)
                | (user_tag << 16)
            )
            desc["tag"] = gemm_ext
            desc["size"] = 3 if (has_bias or has_alpha or has_beta) else 2
            desc["fields"] = {
                "a_addr": buf_map[op["a"]],
                "b_addr": buf_map[op["b"]],
                "c_addr": buf_map[op["c"]],
                "m": int(op["m"]),
                "n": int(op["n"]),
                "k": int(op["k"]),
                "lda": int(op.get("lda", 0)),
                "ldb": int(op.get("ldb", 0)),
                "ldc": int(op.get("ldc", 0)),
                # Extension bytes [56..63]: stable per-op UID for OOO-safe matching.
                "op_uid": int(op.get("op_uid", default_gemm_uid)) & 0xFFFFFFFFFFFFFFFF,
                "bias_addr": buf_map[op["bias"]] if op.get("bias") else 0,
                "alpha": float(op.get("alpha", 0.0)) if has_alpha else 0.0,
                "beta": float(op.get("beta", 0.0)) if has_beta else 0.0,
            }
        else:
            desc["tag"] = pack_mnk(int(op["m"]), int(op["n"]), int(op["k"]))
            desc["fields"] = {
                "a_addr": buf_map[op["a"]],
                "b_addr": buf_map[op["b"]],
                "c_addr": buf_map[op["c"]],
            }
    elif otype == "vec_op":
        op_name = str(op["op"]).lower()
        if op_name not in VEC_OP_FLAGS:
            raise ValueError(f"unsupported vec_op op {op['op']}")
        dtype = DTYPE_FLAGS[op["dtype"]]
        desc["flags"] = ((dtype & 0xF) << 4) | (VEC_OP_FLAGS[op_name] & 0x3)
        desc["fields"] = {
            "src_addr": buf_map[op["src"]],
            "dst_addr": buf_map[op["dst"]],
            "size": int(op["bytes"]),
            "op": op_name,
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
    size_units = int(desc["size"])
    if size_units < 1:
        raise ValueError("descriptor size must be >= 1")
    data = bytearray(32 * size_units)
    opcode = int(desc["opcode"]) & 0xFF
    flags = int(desc["flags"]) & 0xFF
    size = size_units & 0xFF
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
        if size_units >= 2:
            struct.pack_into(
                "<IIIIII",
                data,
                32,
                int(fields.get("m", 0)),
                int(fields.get("n", 0)),
                int(fields.get("k", 0)),
                int(fields.get("lda", 0)),
                int(fields.get("ldb", 0)),
                int(fields.get("ldc", 0)),
            )
            struct.pack_into("<Q", data, 56, int(fields.get("op_uid", 0)))
        if size_units >= 3:
            struct.pack_into("<Q", data, 64, int(fields.get("bias_addr", 0)))
            struct.pack_into("<f", data, 72, float(fields.get("alpha", 0.0)))
            struct.pack_into("<f", data, 76, float(fields.get("beta", 0.0)))
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

    descs = []
    next_gemm_uid = 1
    for op in ops:
        op_uid = 0
        if op.get("type") == "gemm":
            op_uid = next_gemm_uid
            next_gemm_uid += 1
        descs.append(emit_desc(op, buf_map, op_uid))
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
