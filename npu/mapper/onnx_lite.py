"""
onnx_lite.py

Minimal ONNX (protobuf) reader/writer utilities.

Why this exists:
- The full `onnx` Python package (and protobuf runtime) may not be available in
  the early bring-up environment.
- For RTLGen v0 mapping we only need a small ONNX subset (MLP: MatMul/Add/Relu)
  with fixed tensor shapes and initializers.

Scope:
- Decode: enough of ModelProto/GraphProto to extract nodes, initializers, and
  input/output shapes.
- Encode: enough to generate tiny MLP ONNX models for local examples.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union


# ONNX TensorProto data_type enum (subset).
TENSOR_UNDEFINED = 0
TENSOR_FLOAT = 1
TENSOR_UINT8 = 2
TENSOR_INT8 = 3
TENSOR_UINT16 = 4
TENSOR_INT16 = 5
TENSOR_INT32 = 6
TENSOR_INT64 = 7
TENSOR_STRING = 8
TENSOR_BOOL = 9
TENSOR_FLOAT16 = 10
TENSOR_DOUBLE = 11
TENSOR_UINT32 = 12
TENSOR_UINT64 = 13
TENSOR_COMPLEX64 = 14
TENSOR_COMPLEX128 = 15
TENSOR_BFLOAT16 = 16


@dataclass(frozen=True)
class OnnxTensor:
    name: str
    dims: List[int]
    data_type: Optional[int] = None


@dataclass(frozen=True)
class OnnxNode:
    op_type: str
    inputs: List[str]
    outputs: List[str]
    name: str = ""


@dataclass(frozen=True)
class OnnxGraph:
    name: str
    nodes: List[OnnxNode]
    initializers: Dict[str, OnnxTensor]
    inputs: Dict[str, List[int]]
    outputs: Dict[str, List[int]]


@dataclass(frozen=True)
class OnnxModel:
    graph: OnnxGraph


class _ProtoReader:
    def __init__(self, data: bytes):
        self._data = data
        self._pos = 0
        self._end = len(data)

    def eof(self) -> bool:
        return self._pos >= self._end

    def _need(self, n: int) -> None:
        if self._pos + n > self._end:
            raise ValueError("truncated protobuf message")

    def read_bytes(self, n: int) -> bytes:
        self._need(n)
        out = self._data[self._pos : self._pos + n]
        self._pos += n
        return out

    def read_varint(self) -> int:
        shift = 0
        result = 0
        while True:
            if self._pos >= self._end:
                raise ValueError("truncated varint")
            b = self._data[self._pos]
            self._pos += 1
            result |= (b & 0x7F) << shift
            if (b & 0x80) == 0:
                return result
            shift += 7
            if shift >= 70:
                raise ValueError("varint too long")

    def read_tag(self) -> Tuple[int, int]:
        tag = self.read_varint()
        return (tag >> 3), (tag & 0x7)

    def read_length_delimited(self) -> bytes:
        length = self.read_varint()
        return self.read_bytes(length)

    def skip_field(self, wire_type: int) -> None:
        if wire_type == 0:  # varint
            _ = self.read_varint()
            return
        if wire_type == 1:  # 64-bit
            _ = self.read_bytes(8)
            return
        if wire_type == 2:  # length-delimited
            length = self.read_varint()
            _ = self.read_bytes(length)
            return
        if wire_type == 5:  # 32-bit
            _ = self.read_bytes(4)
            return
        raise ValueError(f"unsupported wire_type {wire_type}")


def _parse_packed_varints(blob: bytes) -> List[int]:
    r = _ProtoReader(blob)
    out: List[int] = []
    while not r.eof():
        out.append(r.read_varint())
    return out


def _parse_dimension(data: bytes) -> Optional[int]:
    # TensorShapeProto.Dimension
    r = _ProtoReader(data)
    dim_value: Optional[int] = None
    while not r.eof():
        field, wt = r.read_tag()
        if field == 1 and wt == 0:  # dim_value
            dim_value = int(r.read_varint())
        elif field == 2 and wt == 2:  # dim_param
            _ = r.read_length_delimited()
        else:
            r.skip_field(wt)
    return dim_value


def _parse_tensor_shape(data: bytes) -> List[int]:
    # TensorShapeProto
    r = _ProtoReader(data)
    dims: List[int] = []
    while not r.eof():
        field, wt = r.read_tag()
        if field == 1 and wt == 2:  # dim
            dim = _parse_dimension(r.read_length_delimited())
            dims.append(int(dim) if dim is not None else -1)
        else:
            r.skip_field(wt)
    return dims


def _parse_tensor_type(data: bytes) -> Tuple[Optional[int], List[int]]:
    # TypeProto.Tensor
    r = _ProtoReader(data)
    elem_type: Optional[int] = None
    shape: List[int] = []
    while not r.eof():
        field, wt = r.read_tag()
        if field == 1 and wt == 0:  # elem_type
            elem_type = int(r.read_varint())
        elif field == 2 and wt == 2:  # shape
            shape = _parse_tensor_shape(r.read_length_delimited())
        else:
            r.skip_field(wt)
    return elem_type, shape


def _parse_type_proto(data: bytes) -> Tuple[Optional[int], List[int]]:
    # TypeProto
    r = _ProtoReader(data)
    elem_type: Optional[int] = None
    shape: List[int] = []
    while not r.eof():
        field, wt = r.read_tag()
        if field == 1 and wt == 2:  # tensor_type
            elem_type, shape = _parse_tensor_type(r.read_length_delimited())
        else:
            r.skip_field(wt)
    return elem_type, shape


def _parse_value_info(data: bytes) -> Tuple[str, Optional[int], List[int]]:
    # ValueInfoProto
    r = _ProtoReader(data)
    name = ""
    elem_type: Optional[int] = None
    shape: List[int] = []
    while not r.eof():
        field, wt = r.read_tag()
        if field == 1 and wt == 2:  # name
            name = r.read_length_delimited().decode("utf-8", errors="replace")
        elif field == 2 and wt == 2:  # type
            elem_type, shape = _parse_type_proto(r.read_length_delimited())
        else:
            r.skip_field(wt)
    return name, elem_type, shape


def _parse_tensor_proto(data: bytes) -> OnnxTensor:
    # TensorProto
    r = _ProtoReader(data)
    name = ""
    dims: List[int] = []
    data_type: Optional[int] = None
    while not r.eof():
        field, wt = r.read_tag()
        if field == 1 and wt == 0:  # dims (unpacked)
            dims.append(int(r.read_varint()))
        elif field == 1 and wt == 2:  # dims (packed)
            dims.extend(_parse_packed_varints(r.read_length_delimited()))
        elif field == 2 and wt == 0:  # data_type
            data_type = int(r.read_varint())
        elif field == 8 and wt == 2:  # name
            name = r.read_length_delimited().decode("utf-8", errors="replace")
        else:
            r.skip_field(wt)
    return OnnxTensor(name=name, dims=dims, data_type=data_type)


def _parse_node_proto(data: bytes) -> OnnxNode:
    # NodeProto
    r = _ProtoReader(data)
    name = ""
    op_type = ""
    inputs: List[str] = []
    outputs: List[str] = []
    while not r.eof():
        field, wt = r.read_tag()
        if field == 1 and wt == 2:  # input
            inputs.append(r.read_length_delimited().decode("utf-8", errors="replace"))
        elif field == 2 and wt == 2:  # output
            outputs.append(r.read_length_delimited().decode("utf-8", errors="replace"))
        elif field == 3 and wt == 2:  # name
            name = r.read_length_delimited().decode("utf-8", errors="replace")
        elif field == 4 and wt == 2:  # op_type
            op_type = r.read_length_delimited().decode("utf-8", errors="replace")
        else:
            r.skip_field(wt)
    return OnnxNode(op_type=op_type, inputs=inputs, outputs=outputs, name=name)


def _parse_graph_proto(data: bytes) -> OnnxGraph:
    # GraphProto
    r = _ProtoReader(data)
    name = ""
    nodes: List[OnnxNode] = []
    initializers: Dict[str, OnnxTensor] = {}
    inputs: Dict[str, List[int]] = {}
    outputs: Dict[str, List[int]] = {}
    while not r.eof():
        field, wt = r.read_tag()
        if field == 1 and wt == 2:  # node
            nodes.append(_parse_node_proto(r.read_length_delimited()))
        elif field == 2 and wt == 2:  # name
            name = r.read_length_delimited().decode("utf-8", errors="replace")
        elif field == 5 and wt == 2:  # initializer
            t = _parse_tensor_proto(r.read_length_delimited())
            if t.name:
                initializers[t.name] = t
        elif field == 11 and wt == 2:  # input
            vname, _, shape = _parse_value_info(r.read_length_delimited())
            if vname:
                inputs[vname] = shape
        elif field == 12 and wt == 2:  # output
            vname, _, shape = _parse_value_info(r.read_length_delimited())
            if vname:
                outputs[vname] = shape
        else:
            r.skip_field(wt)
    return OnnxGraph(
        name=name,
        nodes=nodes,
        initializers=initializers,
        inputs=inputs,
        outputs=outputs,
    )


def load_onnx_model(path: Union[str, Path]) -> OnnxModel:
    data = Path(path).read_bytes()
    r = _ProtoReader(data)
    graph: Optional[OnnxGraph] = None
    while not r.eof():
        field, wt = r.read_tag()
        if field == 7 and wt == 2:  # graph
            graph = _parse_graph_proto(r.read_length_delimited())
        else:
            r.skip_field(wt)
    if graph is None:
        raise ValueError("ONNX model missing graph")
    return OnnxModel(graph=graph)


def _enc_varint(value: int) -> bytes:
    if value < 0:
        # Encode negative values as 64-bit two's complement varint.
        value &= (1 << 64) - 1
    out = bytearray()
    while True:
        to_write = value & 0x7F
        value >>= 7
        if value:
            out.append(to_write | 0x80)
        else:
            out.append(to_write)
            break
    return bytes(out)


def _enc_tag(field: int, wire_type: int) -> bytes:
    return _enc_varint((field << 3) | wire_type)


def _enc_ld(field: int, payload: bytes) -> bytes:
    return _enc_tag(field, 2) + _enc_varint(len(payload)) + payload


def _enc_str(field: int, s: str) -> bytes:
    return _enc_ld(field, s.encode("utf-8"))


def _enc_v(field: int, value: int) -> bytes:
    return _enc_tag(field, 0) + _enc_varint(value)


def _encode_dimension(dim_value: int) -> bytes:
    # Dimension { dim_value: int64 }
    return _enc_v(1, dim_value)


def _encode_tensor_shape(shape: List[int]) -> bytes:
    # TensorShapeProto { dim: [Dimension] }
    out = bytearray()
    for dim in shape:
        out += _enc_ld(1, _encode_dimension(int(dim)))
    return bytes(out)


def _encode_tensor_type(elem_type: int, shape: List[int]) -> bytes:
    # TensorTypeProto { elem_type: int32, shape: TensorShapeProto }
    return _enc_v(1, int(elem_type)) + _enc_ld(2, _encode_tensor_shape(shape))


def _encode_type_proto_tensor(elem_type: int, shape: List[int]) -> bytes:
    # TypeProto { tensor_type: TensorTypeProto }
    return _enc_ld(1, _encode_tensor_type(elem_type, shape))


def _encode_value_info(name: str, elem_type: int, shape: List[int]) -> bytes:
    # ValueInfoProto { name, type }
    return _enc_str(1, name) + _enc_ld(2, _encode_type_proto_tensor(elem_type, shape))


def _encode_tensor(name: str, dims: List[int], data_type: int, raw_data: bytes) -> bytes:
    # TensorProto { dims, data_type, name, raw_data }
    out = bytearray()
    for d in dims:
        out += _enc_v(1, int(d))
    out += _enc_v(2, int(data_type))
    out += _enc_str(8, name)
    out += _enc_ld(9, raw_data)
    return bytes(out)


def _encode_node(op_type: str, inputs: List[str], outputs: List[str], name: str = "") -> bytes:
    # NodeProto { input*, output*, name, op_type }
    out = bytearray()
    for inp in inputs:
        out += _enc_str(1, inp)
    for outp in outputs:
        out += _enc_str(2, outp)
    if name:
        out += _enc_str(3, name)
    out += _enc_str(4, op_type)
    return bytes(out)


def _encode_opset_import(domain: str, version: int) -> bytes:
    # OperatorSetIdProto { domain, version }
    out = bytearray()
    if domain:
        out += _enc_str(1, domain)
    out += _enc_v(2, int(version))
    return bytes(out)


def _encode_graph(
    name: str,
    nodes: List[bytes],
    inputs: List[bytes],
    outputs: List[bytes],
    initializers: List[bytes],
) -> bytes:
    # GraphProto
    out = bytearray()
    for n in nodes:
        out += _enc_ld(1, n)
    out += _enc_str(2, name)
    for init in initializers:
        out += _enc_ld(5, init)
    for vi in inputs:
        out += _enc_ld(11, vi)
    for vi in outputs:
        out += _enc_ld(12, vi)
    return bytes(out)


def build_mlp_model_bytes(
    *,
    name: str,
    b: int,
    in_dim: int,
    hidden_dim: int,
    out_dim: int,
    dtype: int = TENSOR_INT8,
    opset_version: int = 13,
    ir_version: int = 8,
) -> bytes:
    """
    Build a tiny MLP ONNX model:
      Y = Add(MatMul(Relu(Add(MatMul(X, W1), b1)), W2), b2)

    The initializers contain raw_data filled with zeros. This is sufficient for
    shape-driven mapping and examples.
    """

    def zeros(n: int) -> bytes:
        return bytes([0] * n)

    w1 = _encode_tensor("W1", [in_dim, hidden_dim], dtype, zeros(in_dim * hidden_dim))
    b1 = _encode_tensor("b1", [hidden_dim], dtype, zeros(hidden_dim))
    w2 = _encode_tensor("W2", [hidden_dim, out_dim], dtype, zeros(hidden_dim * out_dim))
    b2 = _encode_tensor("b2", [out_dim], dtype, zeros(out_dim))

    vi_x = _encode_value_info("X", dtype, [b, in_dim])
    vi_y = _encode_value_info("Y", dtype, [b, out_dim])

    nodes = [
        _encode_node("MatMul", ["X", "W1"], ["Y0"], name="MatMul1"),
        _encode_node("Add", ["Y0", "b1"], ["Y1"], name="Add1"),
        _encode_node("Relu", ["Y1"], ["Y2"], name="Relu1"),
        _encode_node("MatMul", ["Y2", "W2"], ["Y3"], name="MatMul2"),
        _encode_node("Add", ["Y3", "b2"], ["Y"], name="Add2"),
    ]

    graph = _encode_graph(
        name=name,
        nodes=nodes,
        inputs=[vi_x],
        outputs=[vi_y],
        initializers=[w1, b1, w2, b2],
    )

    model = bytearray()
    model += _enc_v(1, int(ir_version))  # ir_version
    model += _enc_ld(8, _encode_opset_import("", opset_version))  # opset_import
    model += _enc_ld(7, graph)  # graph
    return bytes(model)


def write_mlp_model(path: Union[str, Path], *, preset: str) -> None:
    preset = preset.lower().strip()
    if preset == "mlp1":
        b, in_dim, hidden_dim, out_dim = 8, 64, 128, 64
        name = "mlp1"
    elif preset == "mlp2":
        b, in_dim, hidden_dim, out_dim = 16, 256, 512, 256
        name = "mlp2"
    else:
        raise ValueError(f"unknown preset {preset!r} (expected mlp1|mlp2)")
    data = build_mlp_model_bytes(
        name=name,
        b=b,
        in_dim=in_dim,
        hidden_dim=hidden_dim,
        out_dim=out_dim,
        dtype=TENSOR_INT8,
    )
    Path(path).write_bytes(data)
