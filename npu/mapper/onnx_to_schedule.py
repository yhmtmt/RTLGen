#!/usr/bin/env python3
"""
ONNX (subset) -> NPU schedule IR (v0.1)

This is intentionally small and opinionated for the RTLGen minimal NPU demo:
- Supported op subset: MatMul (+ bias Add) (+ Relu) in an MLP chain.
- Output: schedule IR as defined by `npu/mapper/ir.md`.

The generated schedule models explicit DMA copies from "DRAM" buffers into
arch-defined SRAM instances, then issues GEMM v0.2 descriptors with bias and
epilogue to represent Add+Relu.
"""

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml  # type: ignore

from onnx_lite import OnnxGraph, load_onnx_model


def _align_up(value: int, alignment: int) -> int:
    if alignment <= 0:
        return value
    return (value + alignment - 1) // alignment * alignment


@dataclass
class _Region:
    name: str
    base: int
    size: int
    alignment: int
    next_addr: int

    @classmethod
    def create(cls, name: str, base: int, size: int, alignment: int) -> "_Region":
        return cls(name=name, base=base, size=size, alignment=alignment, next_addr=base)

    def alloc(self, nbytes: int, alignment: Optional[int] = None) -> int:
        if nbytes < 0:
            raise ValueError("alloc size must be non-negative")
        a = max(int(alignment or 0), int(self.alignment or 0), 32)
        addr = _align_up(self.next_addr, a)
        end = addr + int(nbytes)
        if end > self.base + self.size:
            raise ValueError(
                f"out of space in region {self.name}: need {nbytes} bytes, "
                f"have {(self.base + self.size) - addr} bytes remaining"
            )
        self.next_addr = end
        return addr


def _sram_instance_size_bytes(inst: dict) -> int:
    depth = int(inst["depth"])
    width_bits = int(inst["width"])
    banks = int(inst.get("banks", 1))
    word_bytes = width_bits // 8
    return depth * word_bytes * banks


def _find_sram_instance(arch: dict, name: str) -> dict:
    sram = arch.get("sram", {})
    for inst in sram.get("instances", []) or []:
        if inst.get("name") == name:
            return inst
    raise ValueError(f"sram instance not found: {name!r}")


def _infer_mlp_chain(g: OnnxGraph) -> Tuple[str, str, str, str, str, str]:
    """
    Return (x, w1, b1, w2, b2, y) tensor names for:
      X -> MatMul(X,W1) -> Add(+b1) -> Relu -> MatMul(*,W2) -> Add(+b2) -> Y
    """
    if not g.inputs:
        raise ValueError("ONNX graph has no inputs")
    x_name = next(iter(g.inputs.keys()))

    inits = set(g.initializers.keys())

    def is_init(name: str) -> bool:
        return name in inits

    def other_of_pair(pair: List[str], known: str) -> str:
        if len(pair) != 2:
            raise ValueError("expected 2-input node")
        if pair[0] == known:
            return pair[1]
        if pair[1] == known:
            return pair[0]
        raise ValueError("known input not found")

    # Find MatMul1
    matmul1 = next(
        (n for n in g.nodes if n.op_type == "MatMul" and x_name in n.inputs),
        None,
    )
    if matmul1 is None or not matmul1.outputs:
        raise ValueError("failed to find MatMul1 with X as input")
    w1 = other_of_pair(matmul1.inputs, x_name)
    if not is_init(w1):
        raise ValueError(f"MatMul1 weight must be an initializer, got {w1!r}")
    y0 = matmul1.outputs[0]

    # Add1 (bias)
    add1 = next(
        (n for n in g.nodes if n.op_type == "Add" and y0 in n.inputs),
        None,
    )
    if add1 is None or not add1.outputs:
        raise ValueError("failed to find Add1 after MatMul1")
    b1 = other_of_pair(add1.inputs, y0)
    if not is_init(b1):
        raise ValueError(f"Add1 bias must be an initializer, got {b1!r}")
    y1 = add1.outputs[0]

    # Relu1
    relu1 = next(
        (n for n in g.nodes if n.op_type == "Relu" and y1 in n.inputs),
        None,
    )
    if relu1 is None or not relu1.outputs:
        raise ValueError("failed to find Relu after Add1")
    y2 = relu1.outputs[0]

    # MatMul2
    matmul2 = next(
        (n for n in g.nodes if n.op_type == "MatMul" and y2 in n.inputs and n is not matmul1),
        None,
    )
    if matmul2 is None or not matmul2.outputs:
        raise ValueError("failed to find MatMul2 after Relu")
    w2 = other_of_pair(matmul2.inputs, y2)
    if not is_init(w2):
        raise ValueError(f"MatMul2 weight must be an initializer, got {w2!r}")
    y3 = matmul2.outputs[0]

    # Add2
    add2 = next(
        (n for n in g.nodes if n.op_type == "Add" and y3 in n.inputs and n is not add1),
        None,
    )
    if add2 is None or not add2.outputs:
        raise ValueError("failed to find Add2 after MatMul2")
    b2 = other_of_pair(add2.inputs, y3)
    if not is_init(b2):
        raise ValueError(f"Add2 bias must be an initializer, got {b2!r}")
    y = add2.outputs[0]

    return x_name, w1, b1, w2, b2, y


def _require_shape_2d(name: str, shape: List[int]) -> Tuple[int, int]:
    if len(shape) != 2:
        raise ValueError(f"expected 2D shape for {name}, got {shape}")
    if shape[0] <= 0 or shape[1] <= 0:
        raise ValueError(f"non-positive dim in {name} shape: {shape}")
    return int(shape[0]), int(shape[1])


def _require_shape_1d_or_2d(name: str, shape: List[int], expected: int) -> int:
    if len(shape) == 1:
        if shape[0] != expected:
            raise ValueError(f"bias {name} dim mismatch: got {shape[0]}, expected {expected}")
        return expected
    if len(shape) == 2:
        if shape[1] != expected:
            raise ValueError(f"bias {name} dim mismatch: got {shape}, expected [*, {expected}]")
        return expected
    raise ValueError(f"expected 1D or 2D bias shape for {name}, got {shape}")


def build_schedule_for_mlp(
    *,
    g: OnnxGraph,
    arch_path: str,
    activation_sram_name: str = "activation_sram",
    weight_sram_name: str = "weight_sram",
    dram_base: int = 0x0000003000000000,
    dram_size: int = 1 << 28,  # 256 MiB (arbitrary large sandbox)
    dtype_bytes: int = 1,  # int8
) -> Dict:
    x, w1, b1, w2, b2, y = _infer_mlp_chain(g)

    x_shape = g.inputs.get(x, [])
    if not x_shape:
        raise ValueError(f"missing input shape for {x!r}")
    b, in_dim = _require_shape_2d(x, x_shape)

    w1_dims = g.initializers[w1].dims
    if len(w1_dims) != 2:
        raise ValueError(f"expected 2D W1, got {w1_dims}")
    if int(w1_dims[0]) != in_dim:
        raise ValueError(f"W1 dim mismatch: expected [{in_dim}, H], got {w1_dims}")
    hidden_dim = int(w1_dims[1])

    b1_dims = g.initializers[b1].dims
    _require_shape_1d_or_2d(b1, b1_dims, hidden_dim)

    w2_dims = g.initializers[w2].dims
    if len(w2_dims) != 2:
        raise ValueError(f"expected 2D W2, got {w2_dims}")
    if int(w2_dims[0]) != hidden_dim:
        raise ValueError(f"W2 dim mismatch: expected [{hidden_dim}, Out], got {w2_dims}")
    out_dim = int(w2_dims[1])

    b2_dims = g.initializers[b2].dims
    _require_shape_1d_or_2d(b2, b2_dims, out_dim)

    arch = yaml.safe_load(Path(arch_path).read_text(encoding="utf-8"))
    act_inst = _find_sram_instance(arch, activation_sram_name)
    wgt_inst = _find_sram_instance(arch, weight_sram_name)

    act_base = int(act_inst["base_addr"])
    act_size = _sram_instance_size_bytes(act_inst)
    act_align = int(act_inst.get("alignment_bytes", 64))
    wgt_base = int(wgt_inst["base_addr"])
    wgt_size = _sram_instance_size_bytes(wgt_inst)
    wgt_align = int(wgt_inst.get("alignment_bytes", 64))

    dram = _Region.create("dram", dram_base, dram_size, 32)
    act = _Region.create(activation_sram_name, act_base, act_size, act_align)

    def bytes_2d(m: int, n: int) -> int:
        return int(m) * int(n) * int(dtype_bytes)

    def bytes_1d(n: int) -> int:
        return int(n) * int(dtype_bytes)

    sizes = {
        "x": bytes_2d(b, in_dim),
        "w1": bytes_2d(in_dim, hidden_dim),
        "b1": bytes_1d(hidden_dim),
        "y1": bytes_2d(b, hidden_dim),
        "w2": bytes_2d(hidden_dim, out_dim),
        "b2": bytes_1d(out_dim),
        "y": bytes_2d(b, out_dim),
    }

    # Reuse weight SRAM between stages instead of allocating W1 and W2 at once.
    # Stage1 footprint:
    w1_sram = wgt_base
    b1_sram = _align_up(w1_sram + sizes["w1"], wgt_align)
    if b1_sram + sizes["b1"] > wgt_base + wgt_size:
        raise ValueError(
            f"weight SRAM cannot fit GEMM1 weights+bias: "
            f"need {sizes['w1'] + sizes['b1']} bytes in {wgt_size} bytes"
        )

    # Determine stage2 output chunking based on available weight SRAM.
    # Phase-1 policy: split GEMM2 by output channels (N axis) and stream chunks.
    max_out_chunk = wgt_size // ((hidden_dim + 1) * int(dtype_bytes))
    if max_out_chunk <= 0:
        raise ValueError(
            f"weight SRAM too small for GEMM2 chunking: hidden_dim={hidden_dim}, "
            f"wgt_size={wgt_size}"
        )
    max_out_chunk = min(max_out_chunk, out_dim)
    if max_out_chunk <= 0:
        raise ValueError(f"invalid max_out_chunk computed: {max_out_chunk}")

    # Tighten chunk size if alignment padding pushes b2 scratch past SRAM end.
    while max_out_chunk > 0:
        w2_chunk_bytes = bytes_2d(hidden_dim, max_out_chunk)
        b2_sram = _align_up(wgt_base + w2_chunk_bytes, wgt_align)
        b2_chunk_bytes = bytes_1d(max_out_chunk)
        if b2_sram + b2_chunk_bytes <= wgt_base + wgt_size:
            break
        max_out_chunk -= 1
    if max_out_chunk <= 0:
        raise ValueError("failed to find legal GEMM2 chunk size for weight SRAM")

    # Build chunk plan: one chunk for fit case, multiple chunks for split case.
    out_chunks: List[Tuple[int, int]] = []
    out_offset = 0
    while out_offset < out_dim:
        n_chunk = min(max_out_chunk, out_dim - out_offset)
        out_chunks.append((out_offset, n_chunk))
        out_offset += n_chunk

    y_chunk_max_bytes = bytes_2d(b, max_out_chunk)
    w2_chunk_max_bytes = bytes_2d(hidden_dim, max_out_chunk)
    b2_chunk_max_bytes = bytes_1d(max_out_chunk)
    w2_sram = wgt_base
    b2_sram = _align_up(w2_sram + w2_chunk_max_bytes, wgt_align)
    if b2_sram + b2_chunk_max_bytes > wgt_base + wgt_size:
        raise ValueError("internal error: GEMM2 scratch exceeds weight SRAM")

    # Buffers (DRAM side)
    x_dram = dram.alloc(sizes["x"])
    w1_dram = dram.alloc(sizes["w1"])
    b1_dram = dram.alloc(sizes["b1"])
    w2_dram = dram.alloc(sizes["w2"])
    b2_dram = dram.alloc(sizes["b2"])
    y_dram = dram.alloc(sizes["y"])

    # Buffers (SRAM side)
    # Reuse activation SRAM between X (GEMM1 input) and Y chunk scratch (GEMM2 output).
    io_sram_bytes = max(sizes["x"], y_chunk_max_bytes)
    x_sram = act.alloc(io_sram_bytes)
    y1_sram = act.alloc(sizes["y1"])
    y_chunk_sram = x_sram

    buffers = [
        {"id": "X_DRAM", "addr": hex(x_dram), "bytes": sizes["x"]},
        {"id": "W1_DRAM", "addr": hex(w1_dram), "bytes": sizes["w1"]},
        {"id": "b1_DRAM", "addr": hex(b1_dram), "bytes": sizes["b1"]},
        {"id": "W2_DRAM", "addr": hex(w2_dram), "bytes": sizes["w2"]},
        {"id": "b2_DRAM", "addr": hex(b2_dram), "bytes": sizes["b2"]},
        {"id": "Y_DRAM", "addr": hex(y_dram), "bytes": sizes["y"]},
        {"id": "X_SRAM", "addr": hex(x_sram), "bytes": io_sram_bytes},
        {"id": "Y1_SRAM", "addr": hex(y1_sram), "bytes": sizes["y1"]},
        {"id": "Y2_SRAM_TMP", "addr": hex(y_chunk_sram), "bytes": y_chunk_max_bytes},
        {"id": "W1_SRAM", "addr": hex(w1_sram), "bytes": sizes["w1"]},
        {"id": "b1_SRAM", "addr": hex(b1_sram), "bytes": sizes["b1"]},
        {"id": "W2_SRAM_TMP", "addr": hex(w2_sram), "bytes": w2_chunk_max_bytes},
        {"id": "b2_SRAM_TMP", "addr": hex(b2_sram), "bytes": b2_chunk_max_bytes},
    ]

    ops = [
        {"id": "dma_x", "type": "dma_copy", "src": "X_DRAM", "dst": "X_SRAM", "bytes": sizes["x"]},
        {"id": "dma_w1", "type": "dma_copy", "src": "W1_DRAM", "dst": "W1_SRAM", "bytes": sizes["w1"]},
        {"id": "dma_b1", "type": "dma_copy", "src": "b1_DRAM", "dst": "b1_SRAM", "bytes": sizes["b1"]},
        {
            "id": "gemm1",
            "type": "gemm",
            "a": "X_SRAM",
            "b": "W1_SRAM",
            "c": "Y1_SRAM",
            "m": b,
            "n": hidden_dim,
            "k": in_dim,
            "lda": in_dim * dtype_bytes,
            "ldb": hidden_dim * dtype_bytes,
            "ldc": hidden_dim * dtype_bytes,
            "dtype": "int8",
            "layout": "row_major",
            "bias": "b1_SRAM",
            "epilogue": "relu",
        },
    ]

    deps = [
        {"wait": ["dma_x", "dma_w1", "dma_b1"], "then": "gemm1"},
    ]

    last_dma_y_id = ""
    for chunk_idx, (n_off, n_chunk) in enumerate(out_chunks):
        is_single_chunk = len(out_chunks) == 1
        suffix = "" if is_single_chunk else f"_c{chunk_idx}"
        dma_w2_id = f"dma_w2{suffix}"
        dma_b2_id = f"dma_b2{suffix}"
        gemm2_id = f"gemm2{suffix}"
        dma_y_id = f"dma_y{suffix}"

        # Note: W2 chunk addresses assume stage-2 packed-by-output-chunk layout.
        # This is sufficient for deterministic scheduling/perf evaluation flow.
        w2_chunk_dram_addr = w2_dram + bytes_2d(hidden_dim, n_off)
        b2_chunk_dram_addr = b2_dram + bytes_1d(n_off)
        y_chunk_dram_addr = y_dram + bytes_2d(b, n_off)

        w2_chunk_bytes = bytes_2d(hidden_dim, n_chunk)
        b2_chunk_bytes = bytes_1d(n_chunk)
        y_chunk_bytes = bytes_2d(b, n_chunk)

        w2_chunk_buf = f"W2_DRAM{suffix}"
        b2_chunk_buf = f"b2_DRAM{suffix}"
        y_chunk_buf = f"Y_DRAM{suffix}"
        buffers.extend(
            [
                {"id": w2_chunk_buf, "addr": hex(w2_chunk_dram_addr), "bytes": w2_chunk_bytes},
                {"id": b2_chunk_buf, "addr": hex(b2_chunk_dram_addr), "bytes": b2_chunk_bytes},
                {"id": y_chunk_buf, "addr": hex(y_chunk_dram_addr), "bytes": y_chunk_bytes},
            ]
        )

        # Loads can overlap GEMM1 for the first chunk.
        ops.append({"id": dma_w2_id, "type": "dma_copy", "src": w2_chunk_buf, "dst": "W2_SRAM_TMP", "bytes": w2_chunk_bytes})
        ops.append({"id": dma_b2_id, "type": "dma_copy", "src": b2_chunk_buf, "dst": "b2_SRAM_TMP", "bytes": b2_chunk_bytes})
        ops.append(
            {
                "id": gemm2_id,
                "type": "gemm",
                "a": "Y1_SRAM",
                "b": "W2_SRAM_TMP",
                "c": "Y2_SRAM_TMP",
                "m": b,
                "n": n_chunk,
                "k": hidden_dim,
                "lda": hidden_dim * dtype_bytes,
                "ldb": n_chunk * dtype_bytes,
                "ldc": n_chunk * dtype_bytes,
                "dtype": "int8",
                "layout": "row_major",
                "bias": "b2_SRAM_TMP",
                "epilogue": "none",
            }
        )
        ops.append({"id": dma_y_id, "type": "dma_copy", "src": "Y2_SRAM_TMP", "dst": y_chunk_buf, "bytes": y_chunk_bytes})

        if chunk_idx == 0:
            deps.append({"wait": ["gemm1", dma_w2_id, dma_b2_id], "then": gemm2_id})
        else:
            prev_dma_y_id = f"dma_y_c{chunk_idx - 1}"
            deps.append({"wait": [prev_dma_y_id], "then": dma_w2_id})
            deps.append({"wait": [prev_dma_y_id], "then": dma_b2_id})
            deps.append({"wait": [dma_w2_id, dma_b2_id], "then": gemm2_id})
        deps.append({"wait": [gemm2_id], "then": dma_y_id})
        last_dma_y_id = dma_y_id

    events = [
        {"id": 1000, "signal_on": last_dma_y_id, "irq": True},
    ]

    return {
        "version": 0.1,
        "arch": arch_path,
        "mapper_notes": {
            "gemm2_out_chunks": [n for _, n in out_chunks],
            "gemm2_split_enabled": len(out_chunks) > 1,
            "gemm2_weight_layout": "packed_by_output_chunk",
        },
        "buffers": buffers,
        "ops": ops,
        "deps": deps,
        "events": events,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Convert a tiny ONNX MLP to schedule IR (v0.1).")
    ap.add_argument("--onnx", required=True, help="Path to ONNX model")
    ap.add_argument("--arch", required=True, help="Path to arch.yml (used for SRAM base/size)")
    ap.add_argument("--out", required=True, help="Path to write schedule.yml")
    ap.add_argument("--activation-sram", default="activation_sram", help="SRAM instance name for activations")
    ap.add_argument("--weight-sram", default="weight_sram", help="SRAM instance name for weights/bias")
    ap.add_argument("--dram-base", default="0x0000003000000000", help="DRAM base address (int-like)")
    ap.add_argument("--dram-bytes", default=str(1 << 28), help="DRAM region size bytes (int-like)")
    args = ap.parse_args()

    model = load_onnx_model(args.onnx)
    schedule = build_schedule_for_mlp(
        g=model.graph,
        arch_path=args.arch,
        activation_sram_name=args.activation_sram,
        weight_sram_name=args.weight_sram,
        dram_base=int(str(args.dram_base), 0),
        dram_size=int(str(args.dram_bytes), 0),
        dtype_bytes=1,
    )

    out_path = Path(args.out)
    out_path.write_text(yaml.safe_dump(schedule, sort_keys=False), encoding="utf-8")
    print(f"onnx_to_schedule: wrote schedule to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
