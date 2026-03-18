#!/usr/bin/env python3
"""
ONNX (subset) -> NPU schedule IR (v0.1)

This is intentionally small and opinionated for the RTLGen minimal NPU demo:
- Supported op subset: small linear chains built from MatMul/Gemm, optional
  input Flatten/Cast, optional Relu between linear stages, and optional final
  Softmax.
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


def _split_even(total: int, parts: int) -> List[Tuple[int, int]]:
    total = max(0, int(total))
    parts = max(1, int(parts))
    if total <= 0:
        return [(0, 0)]
    parts = min(parts, total)
    base = total // parts
    rem = total % parts
    out: List[Tuple[int, int]] = []
    offset = 0
    for idx in range(parts):
        size = base + (1 if idx < rem else 0)
        if size <= 0:
            continue
        out.append((offset, size))
        offset += size
    return out or [(0, total)]


def _normalize_softmax_backend(backend: str) -> str:
    value = str(backend or "dedicated").strip().lower()
    if value not in ("dedicated", "vec_placeholder"):
        raise ValueError("softmax backend must be one of: dedicated, vec_placeholder")
    return value


def _direct_terminal_softmax_output_enabled(arch: dict) -> bool:
    if not isinstance(arch, dict):
        return False
    mapping = arch.get("mapping")
    if not isinstance(mapping, dict):
        return False
    constraints = mapping.get("constraints")
    if not isinstance(constraints, dict):
        return False
    return bool(constraints.get("direct_terminal_softmax_output", False))


def _direct_terminal_output_enabled(arch: dict) -> bool:
    if not isinstance(arch, dict):
        return False
    mapping = arch.get("mapping")
    if not isinstance(mapping, dict):
        return False
    constraints = mapping.get("constraints")
    if not isinstance(constraints, dict):
        return False
    return bool(constraints.get("direct_terminal_output", False))


def _choose_stage_row_chunks(
    *,
    batch: int,
    gemm_num_modules: int,
    k_dim: int,
    n_dim: int,
    terminal_softmax_stage: bool,
) -> List[Tuple[int, int]]:
    chunks = _split_even(batch, max(1, int(gemm_num_modules)))
    if len(chunks) <= 1:
        return chunks
    if not terminal_softmax_stage:
        return chunks

    # For tiny terminal softmax classifiers, splitting the final GEMM across
    # modules often adds synchronization overhead without shrinking the serial
    # softmax tail enough to pay for it. Prefer a monolithic final GEMM until
    # each module would carry a minimally meaningful amount of work.
    min_module_macs = 8192
    min_chunk = min(size for _, size in chunks)
    per_module_macs = int(min_chunk) * int(k_dim) * int(n_dim)
    if per_module_macs < min_module_macs:
        return [(0, int(batch))]
    return chunks


@dataclass
class _LinearLayer:
    op_kind: str
    weight: str
    bias: str
    input_name: str
    output_name: str
    relu_output_name: str
    out_dim: int
    relu: bool


@dataclass
class _SupportedLinearGraph:
    input_name: str
    flatten_input: bool
    input_cast: bool
    layers: List[_LinearLayer]
    terminal_softmax: bool
    terminal_output_name: str
    ignored_graph_outputs: List[str]


def _product_positive(shape: List[int], *, name: str) -> int:
    if not shape:
        raise ValueError(f"{name} must be non-empty")
    out = 1
    for dim in shape:
        dim_i = int(dim)
        if dim_i <= 0:
            raise ValueError(f"{name} has non-positive dim: {shape}")
        out *= dim_i
    return out


def _resolve_batch_dim(raw_batch: int, batch_override: Optional[int]) -> int:
    if batch_override is not None:
        if int(batch_override) <= 0:
            raise ValueError(f"batch_override must be positive, got {batch_override}")
        return int(batch_override)
    if int(raw_batch) <= 0:
        return 1
    return int(raw_batch)


def _input_batch_and_in_dim(
    input_name: str,
    shape: List[int],
    *,
    flatten_input: bool,
    batch_override: Optional[int],
) -> Tuple[int, int]:
    if not shape:
        raise ValueError(f"missing input shape for {input_name!r}")
    batch = _resolve_batch_dim(int(shape[0]), batch_override)
    if flatten_input:
        if len(shape) < 2:
            raise ValueError(f"Flatten input must be rank >= 2, got {shape}")
        return batch, _product_positive(list(shape[1:]), name=f"{input_name} flattened dims")
    if len(shape) != 2:
        raise ValueError(f"expected 2D input shape for {input_name}, got {shape}")
    if int(shape[1]) <= 0:
        raise ValueError(f"non-positive feature dim in {input_name} shape: {shape}")
    return batch, int(shape[1])


def _consumers_by_input(g: OnnxGraph) -> Dict[str, List]:
    out: Dict[str, List] = {}
    for node in g.nodes:
        for inp in node.inputs:
            out.setdefault(inp, []).append(node)
    return out


def _other_input_pair(pair: List[str], known: str) -> str:
    if len(pair) != 2:
        raise ValueError("expected 2-input node")
    if pair[0] == known:
        return pair[1]
    if pair[1] == known:
        return pair[0]
    raise ValueError(f"known input {known!r} not found in {pair}")


def _infer_sequential_mlp(
    g: OnnxGraph,
    *,
    batch_override: Optional[int],
) -> _SupportedLinearGraph:
    if not g.inputs:
        raise ValueError("ONNX graph has no inputs")
    x_name = next(iter(g.inputs.keys()))
    input_shape = g.inputs.get(x_name, [])
    consumers = _consumers_by_input(g)
    init_names = set(g.initializers.keys())

    flatten_input = False
    input_cast = False
    current_name = x_name
    if not input_shape:
        raise ValueError(f"missing input shape for {x_name!r}")
    while True:
        prelude_consumers = consumers.get(current_name, [])
        flatten_nodes = [n for n in prelude_consumers if n.op_type == "Flatten"]
        if not flatten_input and flatten_nodes:
            if len(flatten_nodes) != 1 or len(prelude_consumers) != 1:
                raise ValueError("expected a single Flatten consumer on the graph input path")
            flatten_node = flatten_nodes[0]
            if not flatten_node.outputs:
                raise ValueError("Flatten node missing outputs")
            flatten_input = True
            current_name = flatten_node.outputs[0]
            continue

        cast_nodes = [n for n in prelude_consumers if n.op_type == "Cast"]
        if not input_cast and cast_nodes:
            if len(cast_nodes) != 1 or len(prelude_consumers) != 1:
                raise ValueError("expected a single Cast consumer on the graph input path")
            cast_node = cast_nodes[0]
            if not cast_node.outputs:
                raise ValueError("Cast node missing outputs")
            input_cast = True
            current_name = cast_node.outputs[0]
            continue
        break

    _, current_dim = _input_batch_and_in_dim(
        x_name,
        input_shape,
        flatten_input=flatten_input,
        batch_override=batch_override,
    )

    layers: List[_LinearLayer] = []
    while True:
        linear_nodes = [
            n for n in consumers.get(current_name, []) if n.op_type in {"MatMul", "Gemm"}
        ]
        if not linear_nodes:
            break
        if len(linear_nodes) != 1:
            raise ValueError(f"expected one linear consumer of {current_name!r}, got {len(linear_nodes)}")
        linear = linear_nodes[0]
        if not linear.outputs:
            raise ValueError(f"{linear.op_type} node missing outputs")

        op_kind = str(linear.op_type)
        weight_name = ""
        bias_name = ""
        linear_out = linear.outputs[0]
        if op_kind == "MatMul":
            weight_name = _other_input_pair(linear.inputs, current_name)
            if weight_name not in init_names:
                raise ValueError(f"MatMul weight must be an initializer, got {weight_name!r}")
            add_nodes = [n for n in consumers.get(linear_out, []) if n.op_type == "Add"]
            if len(add_nodes) != 1 or not add_nodes[0].outputs:
                raise ValueError("MatMul must be followed by exactly one Add bias node")
            add_node = add_nodes[0]
            bias_name = _other_input_pair(add_node.inputs, linear_out)
            if bias_name not in init_names:
                raise ValueError(f"Add bias must be an initializer, got {bias_name!r}")
            linear_out = add_node.outputs[0]
        else:
            if len(linear.inputs) != 3:
                raise ValueError("Gemm must have exactly three inputs: X, W, b")
            if linear.inputs[0] != current_name:
                raise ValueError("Gemm input ordering unsupported; expected data input first")
            weight_name = str(linear.inputs[1])
            bias_name = str(linear.inputs[2])
            if weight_name not in init_names:
                raise ValueError(f"Gemm weight must be an initializer, got {weight_name!r}")
            if bias_name not in init_names:
                raise ValueError(f"Gemm bias must be an initializer, got {bias_name!r}")

        w_dims = list(g.initializers[weight_name].dims)
        if len(w_dims) != 2:
            raise ValueError(f"expected 2D weight for {weight_name}, got {w_dims}")
        if int(w_dims[0]) == current_dim:
            out_dim = int(w_dims[1])
        elif int(w_dims[1]) == current_dim:
            out_dim = int(w_dims[0])
        else:
            raise ValueError(
                f"weight {weight_name} dims {w_dims} incompatible with input dim {current_dim}"
            )
        _require_shape_1d_or_2d(bias_name, g.initializers[bias_name].dims, out_dim)

        relu_nodes = [n for n in consumers.get(linear_out, []) if n.op_type == "Relu"]
        relu = False
        relu_out = linear_out
        if relu_nodes:
            if len(relu_nodes) != 1 or not relu_nodes[0].outputs:
                raise ValueError(f"expected one Relu consumer of {linear_out!r}")
            relu = True
            relu_out = relu_nodes[0].outputs[0]

        layers.append(
            _LinearLayer(
                op_kind=op_kind,
                weight=weight_name,
                bias=bias_name,
                input_name=current_name,
                output_name=linear_out,
                relu_output_name=relu_out,
                out_dim=out_dim,
                relu=relu,
            )
        )

        current_name = relu_out
        current_dim = out_dim

    if not layers:
        raise ValueError("failed to infer a supported MLP chain")

    graph_outputs = set(g.outputs.keys())
    tail_consumers = consumers.get(current_name, [])
    terminal_softmax = False
    terminal_output_name = current_name
    if tail_consumers:
        softmax_nodes = [n for n in tail_consumers if n.op_type == "Softmax"]
        if softmax_nodes:
            if len(softmax_nodes) != 1 or not softmax_nodes[0].outputs:
                raise ValueError("expected one Softmax consumer on the terminal tensor")
            unsupported_tail = [
                n.op_type for n in tail_consumers if n.op_type not in {"Softmax", "ArgMax"}
            ]
            if unsupported_tail:
                raise ValueError(
                    f"unsupported terminal side consumers after linear chain: {unsupported_tail}"
                )
            terminal_softmax = True
            terminal_output_name = softmax_nodes[0].outputs[0]
        else:
            raise ValueError(
                f"supported chain must terminate at a graph output, got extra consumers on "
                f"{current_name!r}: {[n.op_type for n in tail_consumers]}"
            )

    if terminal_output_name not in graph_outputs:
        raise ValueError(
            f"supported chain must terminate at a graph output, got final tensor "
            f"{terminal_output_name!r}"
        )

    return _SupportedLinearGraph(
        input_name=x_name,
        flatten_input=flatten_input,
        input_cast=input_cast,
        layers=layers,
        terminal_softmax=terminal_softmax,
        terminal_output_name=terminal_output_name,
        ignored_graph_outputs=sorted(name for name in graph_outputs if name != terminal_output_name),
    )


def _max_final_out_chunk(wgt_size: int, in_dim: int, dtype_bytes: int, out_dim: int) -> int:
    max_out_chunk = wgt_size // ((int(in_dim) + 1) * int(dtype_bytes))
    if max_out_chunk <= 0:
        raise ValueError(
            f"weight SRAM too small for final-layer chunking: in_dim={in_dim}, "
            f"wgt_size={wgt_size}"
        )
    return min(max_out_chunk, int(out_dim))


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
    gemm_num_modules: int = 1,
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
    direct_terminal_softmax_output = _direct_terminal_softmax_output_enabled(arch)
    direct_terminal_output = _direct_terminal_output_enabled(arch)
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

    row_chunks = _split_even(b, max(1, int(gemm_num_modules)))
    row_parallel_enabled = len(row_chunks) > 1

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

    row_views: List[Dict[str, int | str]] = []
    if row_parallel_enabled:
        for row_idx, (m_off, m_chunk) in enumerate(row_chunks):
            x_row_id = f"X_SRAM_r{row_idx}"
            y1_row_id = f"Y1_SRAM_r{row_idx}"
            buffers.extend(
                [
                    {
                        "id": x_row_id,
                        "addr": hex(x_sram + bytes_2d(m_off, in_dim)),
                        "bytes": bytes_2d(m_chunk, in_dim),
                    },
                    {
                        "id": y1_row_id,
                        "addr": hex(y1_sram + bytes_2d(m_off, hidden_dim)),
                        "bytes": bytes_2d(m_chunk, hidden_dim),
                    },
                ]
            )
            row_views.append(
                {
                    "row_idx": row_idx,
                    "m_off": m_off,
                    "m_chunk": m_chunk,
                    "x_buf": x_row_id,
                    "y1_buf": y1_row_id,
                    "gemm1_id": f"gemm1_r{row_idx}",
                }
            )
    else:
        row_views.append(
            {
                "row_idx": 0,
                "m_off": 0,
                "m_chunk": b,
                "x_buf": "X_SRAM",
                "y1_buf": "Y1_SRAM",
                "gemm1_id": "gemm1",
            }
        )

    ops = [
        {"id": "dma_x", "type": "dma_copy", "src": "X_DRAM", "dst": "X_SRAM", "bytes": sizes["x"]},
        {"id": "dma_w1", "type": "dma_copy", "src": "W1_DRAM", "dst": "W1_SRAM", "bytes": sizes["w1"]},
        {"id": "dma_b1", "type": "dma_copy", "src": "b1_DRAM", "dst": "b1_SRAM", "bytes": sizes["b1"]},
    ]

    deps: List[Dict[str, Any]] = []
    for row_view in row_views:
        ops.append(
            {
                "id": str(row_view["gemm1_id"]),
                "type": "gemm",
                "a": str(row_view["x_buf"]),
                "b": "W1_SRAM",
                "c": str(row_view["y1_buf"]),
                "m": int(row_view["m_chunk"]),
                "n": hidden_dim,
                "k": in_dim,
                "lda": in_dim * dtype_bytes,
                "ldb": hidden_dim * dtype_bytes,
                "ldc": hidden_dim * dtype_bytes,
                "dtype": "int8",
                "layout": "row_major",
                "bias": "b1_SRAM",
                "epilogue": "relu",
            }
        )
        deps.append({"wait": ["dma_x", "dma_w1", "dma_b1"], "then": str(row_view["gemm1_id"])})

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
        if chunk_idx > 0:
            deps.append({"wait": [last_dma_y_id], "then": dma_w2_id})
            deps.append({"wait": [last_dma_y_id], "then": dma_b2_id})

        prev_row_dma_y_id = ""
        for row_view in row_views:
            row_idx = int(row_view["row_idx"])
            row_suffix = "" if not row_parallel_enabled else f"_r{row_idx}"
            row_suffix_full = f"{suffix}{row_suffix}"
            row_gemm2_id = gemm2_id if not row_parallel_enabled else f"gemm2{row_suffix_full}"
            row_dma_y_id = dma_y_id if not row_parallel_enabled else f"dma_y{row_suffix_full}"
            row_m_off = int(row_view["m_off"])
            row_m_chunk = int(row_view["m_chunk"])
            row_y_bytes = y_chunk_bytes if not row_parallel_enabled else bytes_2d(row_m_chunk, n_chunk)
            row_y_src = "Y2_SRAM_TMP"
            row_y_dst = y_chunk_buf
            if row_parallel_enabled:
                row_y_src = f"Y2_SRAM_TMP{row_suffix_full}"
                row_y_dst = f"Y_DRAM{row_suffix_full}"
                buffers.extend(
                    [
                        {
                            "id": row_y_src,
                            "addr": hex(y_chunk_sram + bytes_2d(row_m_off, n_chunk)),
                            "bytes": row_y_bytes,
                        },
                        {
                            "id": row_y_dst,
                            "addr": hex(y_chunk_dram_addr + bytes_2d(row_m_off, n_chunk)),
                            "bytes": row_y_bytes,
                        },
                    ]
                )

            ops.append(
                {
                    "id": row_gemm2_id,
                    "type": "gemm",
                    "a": str(row_view["y1_buf"]),
                    "b": "W2_SRAM_TMP",
                    "c": row_y_src,
                    "m": row_m_chunk,
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
            ops.append({"id": row_dma_y_id, "type": "dma_copy", "src": row_y_src, "dst": row_y_dst, "bytes": row_y_bytes})

            if row_parallel_enabled:
                deps.append(
                    {
                        "wait": [str(row_view["gemm1_id"]), dma_w2_id, dma_b2_id],
                        "then": row_gemm2_id,
                    }
                )
            elif chunk_idx == 0:
                deps.append({"wait": ["gemm1", dma_w2_id, dma_b2_id], "then": row_gemm2_id})
            else:
                deps.append({"wait": [dma_w2_id, dma_b2_id], "then": row_gemm2_id})

            dma_wait = [row_gemm2_id]
            if prev_row_dma_y_id:
                dma_wait.append(prev_row_dma_y_id)
            deps.append({"wait": dma_wait, "then": row_dma_y_id})
            prev_row_dma_y_id = row_dma_y_id

        last_dma_y_id = prev_row_dma_y_id

    events = [
        {"id": 1000, "signal_on": last_dma_y_id, "irq": True},
    ]

    return {
        "version": 0.1,
        "arch": arch_path,
        "mapper_notes": {
            "gemm_num_modules": int(max(1, gemm_num_modules)),
            "gemm_row_parallel_enabled": row_parallel_enabled,
            "gemm_row_chunks": [m for _, m in row_chunks],
            "gemm2_out_chunks": [n for _, n in out_chunks],
            "gemm2_split_enabled": len(out_chunks) > 1,
            "gemm2_weight_layout": "packed_by_output_chunk",
        },
        "buffers": buffers,
        "ops": ops,
        "deps": deps,
        "events": events,
    }


def build_schedule_for_supported_graph(
    *,
    g: OnnxGraph,
    arch_path: str,
    activation_sram_name: str = "activation_sram",
    weight_sram_name: str = "weight_sram",
    dram_base: int = 0x0000003000000000,
    dram_size: int = 1 << 28,
    dtype_bytes: int = 1,
    gemm_num_modules: int = 1,
    batch_override: Optional[int] = None,
    softmax_backend: str = "dedicated",
) -> Dict:
    softmax_backend = _normalize_softmax_backend(softmax_backend)
    try:
        supported = _infer_sequential_mlp(
            g,
            batch_override=batch_override,
        )
    except Exception:
        return build_schedule_for_mlp(
            g=g,
            arch_path=arch_path,
            activation_sram_name=activation_sram_name,
            weight_sram_name=weight_sram_name,
            dram_base=dram_base,
            dram_size=dram_size,
            dtype_bytes=dtype_bytes,
            gemm_num_modules=gemm_num_modules,
        )

    x_name = supported.input_name
    flatten_input = supported.flatten_input
    input_cast = supported.input_cast
    layers = supported.layers
    terminal_softmax = supported.terminal_softmax

    x_shape = g.inputs.get(x_name, [])
    batch, in_dim = _input_batch_and_in_dim(
        x_name,
        x_shape,
        flatten_input=flatten_input,
        batch_override=batch_override,
    )

    layer_dims: List[Tuple[int, int]] = []
    cur_dim = in_dim
    for layer in layers:
        layer_dims.append((cur_dim, int(layer.out_dim)))
        cur_dim = int(layer.out_dim)
    out_dim = int(layer_dims[-1][1])

    arch = yaml.safe_load(Path(arch_path).read_text(encoding="utf-8"))
    direct_terminal_softmax_output = _direct_terminal_softmax_output_enabled(arch)
    direct_terminal_output = _direct_terminal_output_enabled(arch)
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

    input_bytes = bytes_2d(batch, in_dim)
    layer_weight_bytes = [bytes_2d(k_dim, n_dim) for k_dim, n_dim in layer_dims]
    layer_bias_bytes = [bytes_1d(n_dim) for _, n_dim in layer_dims]
    layer_output_bytes = [bytes_2d(batch, n_dim) for _, n_dim in layer_dims]

    for idx, ((k_dim, _), w_bytes, b_bytes) in enumerate(
        zip(layer_dims[:-1], layer_weight_bytes[:-1], layer_bias_bytes[:-1])
    ):
        b_sram = _align_up(wgt_base + w_bytes, wgt_align)
        if b_sram + b_bytes > wgt_base + wgt_size:
            raise ValueError(
                f"weight SRAM cannot fit layer {idx + 1} weights+bias: "
                f"need {w_bytes + b_bytes} bytes in {wgt_size} bytes"
            )

    final_in_dim, final_out_dim = layer_dims[-1]
    max_out_chunk = _max_final_out_chunk(wgt_size, final_in_dim, dtype_bytes, final_out_dim)
    while max_out_chunk > 0:
        final_w_bytes = bytes_2d(final_in_dim, max_out_chunk)
        final_b_sram = _align_up(wgt_base + final_w_bytes, wgt_align)
        final_b_bytes = bytes_1d(max_out_chunk)
        if final_b_sram + final_b_bytes <= wgt_base + wgt_size:
            break
        max_out_chunk -= 1
    if max_out_chunk <= 0:
        raise ValueError("failed to find legal final-layer chunk size for weight SRAM")

    out_chunks: List[Tuple[int, int]] = []
    out_offset = 0
    while out_offset < final_out_dim:
        n_chunk = min(max_out_chunk, final_out_dim - out_offset)
        out_chunks.append((out_offset, n_chunk))
        out_offset += n_chunk

    final_chunk_max_bytes = bytes_2d(batch, max_out_chunk)
    final_activation_bytes = layer_output_bytes[-1] if terminal_softmax else final_chunk_max_bytes
    max_act_bytes = max([input_bytes, final_activation_bytes] + layer_output_bytes[:-1])
    act_a_sram = act.alloc(max_act_bytes)
    act_b_sram = act.alloc(max_act_bytes)

    base_row_chunks = _split_even(batch, max(1, int(gemm_num_modules)))
    base_row_parallel_enabled = len(base_row_chunks) > 1
    any_row_parallel_enabled = False
    final_row_chunks = list(base_row_chunks)
    final_row_parallel_enabled = base_row_parallel_enabled

    x_dram = dram.alloc(input_bytes)
    y_dram = dram.alloc(layer_output_bytes[-1])

    layer_w_dram: List[int] = []
    layer_b_dram: List[int] = []
    for w_bytes, b_bytes in zip(layer_weight_bytes, layer_bias_bytes):
        layer_w_dram.append(dram.alloc(w_bytes))
        layer_b_dram.append(dram.alloc(b_bytes))

    buffers = [
        {"id": "X_DRAM", "addr": hex(x_dram), "bytes": input_bytes},
        {"id": "Y_DRAM", "addr": hex(y_dram), "bytes": layer_output_bytes[-1]},
        {"id": "ACT_A_SRAM", "addr": hex(act_a_sram), "bytes": max_act_bytes},
        {"id": "ACT_B_SRAM", "addr": hex(act_b_sram), "bytes": max_act_bytes},
    ]
    for idx, (w_addr, w_bytes, b_addr, b_bytes) in enumerate(
        zip(layer_w_dram, layer_weight_bytes, layer_b_dram, layer_bias_bytes)
    ):
        layer_idx = idx + 1
        buffers.extend(
            [
                {"id": f"W{layer_idx}_DRAM", "addr": hex(w_addr), "bytes": w_bytes},
                {"id": f"b{layer_idx}_DRAM", "addr": hex(b_addr), "bytes": b_bytes},
            ]
        )
    w_sram_tmp_bytes = max(layer_weight_bytes[:-1] + [bytes_2d(final_in_dim, max_out_chunk)])
    b_sram_tmp_bytes = max(layer_bias_bytes[:-1] + [bytes_1d(max_out_chunk)])
    b_sram_tmp_addr = _align_up(wgt_base + w_sram_tmp_bytes, wgt_align)
    if b_sram_tmp_addr + b_sram_tmp_bytes > wgt_base + wgt_size:
        raise ValueError("weight SRAM temp buffers exceed available capacity")
    buffers.extend(
        [
            {"id": "W_SRAM_TMP", "addr": hex(wgt_base), "bytes": w_sram_tmp_bytes},
            {
                "id": "b_SRAM_TMP",
                "addr": hex(b_sram_tmp_addr),
                "bytes": b_sram_tmp_bytes,
            },
        ]
    )

    ops = [
        {"id": "dma_x", "type": "dma_copy", "src": "X_DRAM", "dst": "ACT_A_SRAM", "bytes": input_bytes},
    ]
    deps: List[Dict[str, object]] = []

    current_input_buf = "ACT_A_SRAM"
    current_input_addr = act_a_sram
    stage_ready_ids = ["dma_x"]

    def _row_view_buf(
        *,
        stage_idx: int,
        row_idx: int,
        base_id: str,
        base_addr: int,
        m_off: int,
        m_chunk: int,
        n_dim: int,
    ) -> str:
        buf_id = f"{base_id}_s{stage_idx}_r{row_idx}"
        buffers.append(
            {
                "id": buf_id,
                "addr": hex(base_addr + bytes_2d(m_off, n_dim)),
                "bytes": bytes_2d(m_chunk, n_dim),
            }
        )
        return buf_id

    last_dma_y_id = ""
    for idx, layer in enumerate(layers):
        layer_idx = idx + 1
        k_dim, n_dim = layer_dims[idx]
        dma_w_id = f"dma_w{layer_idx}"
        dma_b_id = f"dma_b{layer_idx}"
        w_dram_id = f"W{layer_idx}_DRAM"
        b_dram_id = f"b{layer_idx}_DRAM"

        final_stage = idx == len(layers) - 1
        next_output_buf = "ACT_B_SRAM" if current_input_buf == "ACT_A_SRAM" else "ACT_A_SRAM"
        next_output_addr = act_b_sram if next_output_buf == "ACT_B_SRAM" else act_a_sram

        if not final_stage:
            ops.append(
                {
                    "id": dma_w_id,
                    "type": "dma_copy",
                    "src": w_dram_id,
                    "dst": "W_SRAM_TMP",
                    "bytes": layer_weight_bytes[idx],
                }
            )
            ops.append(
                {
                    "id": dma_b_id,
                    "type": "dma_copy",
                    "src": b_dram_id,
                    "dst": "b_SRAM_TMP",
                    "bytes": layer_bias_bytes[idx],
                }
            )
            stage_complete_ids: List[str] = []
            if base_row_parallel_enabled:
                any_row_parallel_enabled = True
                for row_idx, (m_off, m_chunk) in enumerate(base_row_chunks):
                    in_buf = _row_view_buf(
                        stage_idx=layer_idx,
                        row_idx=row_idx,
                        base_id=current_input_buf,
                        base_addr=current_input_addr,
                        m_off=m_off,
                        m_chunk=m_chunk,
                        n_dim=k_dim,
                    )
                    out_buf = _row_view_buf(
                        stage_idx=layer_idx,
                        row_idx=row_idx,
                        base_id=next_output_buf,
                        base_addr=next_output_addr,
                        m_off=m_off,
                        m_chunk=m_chunk,
                        n_dim=n_dim,
                    )
                    gemm_id = f"gemm{layer_idx}_r{row_idx}"
                    ops.append(
                        {
                            "id": gemm_id,
                            "type": "gemm",
                            "a": in_buf,
                            "b": "W_SRAM_TMP",
                            "c": out_buf,
                            "m": m_chunk,
                            "n": n_dim,
                            "k": k_dim,
                            "lda": k_dim * dtype_bytes,
                            "ldb": n_dim * dtype_bytes,
                            "ldc": n_dim * dtype_bytes,
                            "dtype": "int8",
                            "layout": "row_major",
                            "bias": "b_SRAM_TMP",
                            "epilogue": "relu" if layer.relu else "none",
                        }
                    )
                    deps.append({"wait": stage_ready_ids + [dma_w_id, dma_b_id], "then": gemm_id})
                    stage_complete_ids.append(gemm_id)
            else:
                gemm_id = f"gemm{layer_idx}"
                ops.append(
                    {
                        "id": gemm_id,
                        "type": "gemm",
                        "a": current_input_buf,
                        "b": "W_SRAM_TMP",
                        "c": next_output_buf,
                        "m": batch,
                        "n": n_dim,
                        "k": k_dim,
                        "lda": k_dim * dtype_bytes,
                        "ldb": n_dim * dtype_bytes,
                        "ldc": n_dim * dtype_bytes,
                        "dtype": "int8",
                        "layout": "row_major",
                        "bias": "b_SRAM_TMP",
                        "epilogue": "relu" if layer.relu else "none",
                    }
                )
                deps.append({"wait": stage_ready_ids + [dma_w_id, dma_b_id], "then": gemm_id})
                stage_complete_ids.append(gemm_id)

            current_input_buf = next_output_buf
            current_input_addr = next_output_addr
            stage_ready_ids = stage_complete_ids
            continue

        terminal_direct_output = bool(idx == len(layers) - 1 and not terminal_softmax and direct_terminal_output)
        stage_row_chunks = (
            [(0, batch)]
            if terminal_direct_output
            else _choose_stage_row_chunks(
                batch=batch,
                gemm_num_modules=gemm_num_modules,
                k_dim=k_dim,
                n_dim=final_out_dim,
                terminal_softmax_stage=terminal_softmax,
            )
        )
        stage_row_parallel_enabled = len(stage_row_chunks) > 1
        final_row_chunks = list(stage_row_chunks)
        final_row_parallel_enabled = stage_row_parallel_enabled
        if stage_row_parallel_enabled:
            any_row_parallel_enabled = True

        prev_chunk_wait_ids: List[str] = []
        for chunk_idx, (n_off, n_chunk) in enumerate(out_chunks):
            suffix = "" if len(out_chunks) == 1 else f"_c{chunk_idx}"
            dma_w_chunk_id = f"{dma_w_id}{suffix}"
            dma_b_chunk_id = f"{dma_b_id}{suffix}"
            gemm_base_id = f"gemm{layer_idx}{suffix}"
            dma_y_base_id = f"dma_y{suffix}" if len(layers) == 2 else f"dma_y{layer_idx}{suffix}"

            w_chunk_dram_addr = layer_w_dram[idx] + bytes_2d(k_dim, n_off)
            b_chunk_dram_addr = layer_b_dram[idx] + bytes_1d(n_off)
            y_chunk_dram_addr = y_dram + bytes_2d(batch, n_off)
            w_chunk_bytes = bytes_2d(k_dim, n_chunk)
            b_chunk_bytes = bytes_1d(n_chunk)
            y_chunk_bytes = bytes_2d(batch, n_chunk)

            if len(out_chunks) == 1:
                w_chunk_id = w_dram_id
                b_chunk_id = b_dram_id
                y_chunk_id = "Y_DRAM"
            else:
                w_chunk_id = f"W{layer_idx}_DRAM{suffix}"
                b_chunk_id = f"b{layer_idx}_DRAM{suffix}"
                y_chunk_id = f"Y_DRAM{suffix}"
                extra_buffers = [
                    {"id": w_chunk_id, "addr": hex(w_chunk_dram_addr), "bytes": w_chunk_bytes},
                    {"id": b_chunk_id, "addr": hex(b_chunk_dram_addr), "bytes": b_chunk_bytes},
                ]
                if not terminal_softmax:
                    extra_buffers.append(
                        {"id": y_chunk_id, "addr": hex(y_chunk_dram_addr), "bytes": y_chunk_bytes}
                    )
                buffers.extend(extra_buffers)
            ops.append(
                {
                    "id": dma_w_chunk_id,
                    "type": "dma_copy",
                    "src": w_chunk_id,
                    "dst": "W_SRAM_TMP",
                    "bytes": w_chunk_bytes,
                }
            )
            ops.append(
                {
                    "id": dma_b_chunk_id,
                    "type": "dma_copy",
                    "src": b_chunk_id,
                    "dst": "b_SRAM_TMP",
                    "bytes": b_chunk_bytes,
                }
            )
            if prev_chunk_wait_ids:
                deps.append({"wait": list(prev_chunk_wait_ids), "then": dma_w_chunk_id})
                deps.append({"wait": list(prev_chunk_wait_ids), "then": dma_b_chunk_id})

            prev_row_tail_id = ""
            chunk_done_ids: List[str] = []
            if stage_row_parallel_enabled:
                for row_idx, (m_off, m_chunk) in enumerate(stage_row_chunks):
                    in_buf = _row_view_buf(
                        stage_idx=layer_idx,
                        row_idx=row_idx,
                        base_id=current_input_buf,
                        base_addr=current_input_addr,
                        m_off=m_off,
                        m_chunk=m_chunk,
                        n_dim=k_dim,
                    )
                    out_sram_id = f"{next_output_buf}{suffix}_r{row_idx}"
                    out_addr = next_output_addr + bytes_2d(m_off, final_out_dim if terminal_softmax else n_chunk)
                    if terminal_softmax:
                        out_addr = next_output_addr + (bytes_2d(m_off, final_out_dim) + bytes_1d(n_off))
                    buffers.append(
                        {
                            "id": out_sram_id,
                            "addr": hex(out_addr),
                            "bytes": bytes_2d(m_chunk, n_chunk),
                        }
                    )
                    out_dram_id = f"{y_chunk_id}_r{row_idx}"
                    if not terminal_softmax:
                        buffers.append(
                            {
                                "id": out_dram_id,
                                "addr": hex(y_chunk_dram_addr + bytes_2d(m_off, n_chunk)),
                                "bytes": bytes_2d(m_chunk, n_chunk),
                            }
                        )
                    gemm_id = f"{gemm_base_id}_r{row_idx}"
                    dma_y_id = f"{dma_y_base_id}_r{row_idx}"
                    ops.append(
                        {
                            "id": gemm_id,
                            "type": "gemm",
                            "a": in_buf,
                            "b": "W_SRAM_TMP",
                            "c": out_sram_id,
                            "m": m_chunk,
                            "n": n_chunk,
                            "k": k_dim,
                            "lda": k_dim * dtype_bytes,
                            "ldb": n_chunk * dtype_bytes,
                            "ldc": (final_out_dim if terminal_softmax else n_chunk) * dtype_bytes,
                            "dtype": "int8",
                            "layout": "row_major",
                            "bias": "b_SRAM_TMP",
                            "epilogue": "relu" if layer.relu else "none",
                        }
                    )
                    deps.append(
                        {
                            "wait": stage_ready_ids + [dma_w_chunk_id, dma_b_chunk_id],
                            "then": gemm_id,
                        }
                    )
                    if terminal_softmax:
                        chunk_done_ids.append(gemm_id)
                    else:
                        if terminal_direct_output:
                            chunk_done_ids.append(gemm_id)
                        else:
                            ops.append(
                                {
                                    "id": dma_y_id,
                                    "type": "dma_copy",
                                    "src": out_sram_id,
                                    "dst": out_dram_id,
                                    "bytes": bytes_2d(m_chunk, n_chunk),
                                }
                            )
                            dma_waits = [gemm_id]
                            if prev_row_tail_id:
                                dma_waits.append(prev_row_tail_id)
                            deps.append({"wait": dma_waits, "then": dma_y_id})
                            prev_row_tail_id = dma_y_id
            else:
                gemm_id = gemm_base_id
                out_buf = next_output_buf
                if terminal_softmax and len(out_chunks) > 1:
                    out_buf = f"{next_output_buf}{suffix}"
                    buffers.append(
                        {
                            "id": out_buf,
                            "addr": hex(next_output_addr + bytes_1d(n_off)),
                            "bytes": y_chunk_bytes,
                        }
                    )
                elif terminal_direct_output:
                    out_buf = y_chunk_id
                ops.append(
                    {
                        "id": gemm_id,
                        "type": "gemm",
                        "a": current_input_buf,
                        "b": "W_SRAM_TMP",
                        "c": out_buf,
                        "m": batch,
                        "n": n_chunk,
                        "k": k_dim,
                        "lda": k_dim * dtype_bytes,
                        "ldb": n_chunk * dtype_bytes,
                        "ldc": (final_out_dim if terminal_softmax else n_chunk) * dtype_bytes,
                        "dtype": "int8",
                        "layout": "row_major",
                        "bias": "b_SRAM_TMP",
                        "epilogue": "relu" if layer.relu else "none",
                    }
                )
                deps.append({"wait": stage_ready_ids + [dma_w_chunk_id, dma_b_chunk_id], "then": gemm_id})
                if terminal_softmax:
                    chunk_done_ids.append(gemm_id)
                else:
                    if terminal_direct_output:
                        prev_row_tail_id = gemm_id
                    else:
                        dma_y_id = dma_y_base_id
                        ops.append(
                            {
                                "id": dma_y_id,
                                "type": "dma_copy",
                                "src": next_output_buf,
                                "dst": y_chunk_id,
                                "bytes": y_chunk_bytes,
                            }
                        )
                        deps.append({"wait": [gemm_id], "then": dma_y_id})
                        prev_row_tail_id = dma_y_id

            if terminal_softmax:
                prev_chunk_wait_ids = list(chunk_done_ids)
            else:
                if terminal_direct_output:
                    prev_chunk_wait_ids = list(chunk_done_ids) if chunk_done_ids else ([prev_row_tail_id] if prev_row_tail_id else [])
                    if prev_chunk_wait_ids:
                        last_dma_y_id = prev_chunk_wait_ids[-1]
                else:
                    prev_chunk_wait_ids = [prev_row_tail_id] if prev_row_tail_id else []
                    last_dma_y_id = prev_row_tail_id

        if terminal_softmax:
            if not prev_chunk_wait_ids:
                raise ValueError("failed to generate final linear outputs for terminal softmax")
            softmax_id = f"softmax{layer_idx}"
            dma_y_id = "dma_y" if len(layers) == 1 else f"dma_y{layer_idx}"
            softmax_direct_output = bool(
                softmax_backend == "dedicated" and direct_terminal_softmax_output
            )
            if softmax_backend == "dedicated":
                ops.append(
                    {
                        "id": softmax_id,
                        "type": "softmax",
                        "src": next_output_buf,
                        "dst": "Y_DRAM" if softmax_direct_output else current_input_buf,
                        "row_bytes": bytes_1d(final_out_dim),
                        "rows": batch,
                        "dtype": "int8",
                    }
                )
            else:
                ops.append(
                    {
                        "id": softmax_id,
                        "type": "vec_op",
                        "op": "softmax",
                        "src": next_output_buf,
                        "dst": current_input_buf,
                        "bytes": layer_output_bytes[-1],
                        "dtype": "int8",
                    }
                )
            deps.append({"wait": prev_chunk_wait_ids, "then": softmax_id})
            if softmax_direct_output:
                last_dma_y_id = softmax_id
            else:
                ops.append(
                    {
                        "id": dma_y_id,
                        "type": "dma_copy",
                        "src": current_input_buf,
                        "dst": "Y_DRAM",
                        "bytes": layer_output_bytes[-1],
                    }
                )
                deps.append({"wait": [softmax_id], "then": dma_y_id})
                last_dma_y_id = dma_y_id

    if not last_dma_y_id:
        raise ValueError("failed to generate final output DMA")

    mapper_notes = {
        "linear_layer_count": len(layers),
        "input_flattened": flatten_input,
        "input_cast_ignored": input_cast,
        "effective_batch": int(batch),
        "gemm_num_modules": int(max(1, gemm_num_modules)),
        "gemm_row_parallel_enabled": any_row_parallel_enabled,
        "gemm_row_chunks": [m for _, m in base_row_chunks],
        "final_linear_row_parallel_enabled": final_row_parallel_enabled,
        "final_linear_row_chunks": [m for _, m in final_row_chunks],
        "final_linear_out_chunks": [n for _, n in out_chunks],
        "final_linear_split_enabled": len(out_chunks) > 1,
        "final_linear_weight_layout": "packed_by_output_chunk",
        "terminal_softmax": terminal_softmax,
        "softmax_backend": softmax_backend if terminal_softmax else "none",
        "terminal_softmax_direct_output": bool(
            terminal_softmax and softmax_backend == "dedicated" and direct_terminal_softmax_output
        ),
        "terminal_direct_output": bool(not terminal_softmax and direct_terminal_output),
        "graph_output_name": supported.terminal_output_name,
        "ignored_graph_outputs": list(supported.ignored_graph_outputs),
    }
    if len(layers) == 2:
        mapper_notes.update(
            {
                "gemm2_out_chunks": [n for _, n in out_chunks],
                "gemm2_split_enabled": len(out_chunks) > 1,
                "gemm2_weight_layout": "packed_by_output_chunk",
            }
        )

    return {
        "version": 0.1,
        "arch": arch_path,
        "mapper_notes": mapper_notes,
        "buffers": buffers,
        "ops": ops,
        "deps": deps,
        "events": [{"id": 1000, "signal_on": last_dma_y_id, "irq": True}],
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
    ap.add_argument("--gemm-num-modules", default="1", help="Number of parallel GEMM module slots to target")
    ap.add_argument(
        "--batch-override",
        default="",
        help="Optional batch dimension override for dynamic or externally selected batch sizing",
    )
    ap.add_argument(
        "--softmax-backend",
        default="dedicated",
        help="Terminal softmax lowering backend: dedicated or vec_placeholder",
    )
    args = ap.parse_args()

    model = load_onnx_model(args.onnx)
    batch_override: Optional[int] = None
    if str(args.batch_override).strip():
        batch_override = max(1, int(str(args.batch_override), 0))
    schedule = build_schedule_for_supported_graph(
        g=model.graph,
        arch_path=args.arch,
        activation_sram_name=args.activation_sram,
        weight_sram_name=args.weight_sram,
        dram_base=int(str(args.dram_base), 0),
        dram_size=int(str(args.dram_bytes), 0),
        dtype_bytes=1,
        gemm_num_modules=max(1, int(str(args.gemm_num_modules), 0)),
        batch_override=batch_override,
        softmax_backend=args.softmax_backend,
    )

    out_path = Path(args.out)
    out_path.write_text(yaml.safe_dump(schedule, sort_keys=False), encoding="utf-8")
    print(f"onnx_to_schedule: wrote schedule to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
