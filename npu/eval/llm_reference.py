#!/usr/bin/env python3
"""Deterministic numerical reference utilities for llm_smoke attention proxies."""

from __future__ import annotations

import json
import math
import struct
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple, Union

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.mapper.onnx_lite import (
    OnnxModel,
    OnnxTensor,
    TENSOR_FLOAT,
    TENSOR_FLOAT16,
    TENSOR_INT8,
    TENSOR_UINT8,
    load_onnx_model,
)

Tensor2D = List[List[float]]
TensorDoc = Dict[str, Any]


def _numel(shape: Sequence[int]) -> int:
    total = 1
    for dim in shape:
        total *= int(dim)
    return total


def decode_initializer_values(tensor: OnnxTensor) -> List[float]:
    count = _numel(tensor.dims)
    raw = tensor.raw_data
    if tensor.data_type == TENSOR_INT8:
        if len(raw) < count:
            raise ValueError(f"tensor {tensor.name} raw_data too short for int8")
        return [float(struct.unpack_from('<b', raw, idx)[0]) for idx in range(count)]
    if tensor.data_type == TENSOR_UINT8:
        if len(raw) < count:
            raise ValueError(f"tensor {tensor.name} raw_data too short for uint8")
        return [float(raw[idx]) for idx in range(count)]
    if tensor.data_type == TENSOR_FLOAT:
        need = count * 4
        if len(raw) < need:
            raise ValueError(f"tensor {tensor.name} raw_data too short for float32")
        return [float(v) for v in struct.unpack('<' + 'f' * count, raw[:need])]
    if tensor.data_type == TENSOR_FLOAT16:
        need = count * 2
        if len(raw) < need:
            raise ValueError(f"tensor {tensor.name} raw_data too short for float16")
        return [float(v) for v in struct.unpack('<' + 'e' * count, raw[:need])]
    raise ValueError(f"unsupported initializer dtype {tensor.data_type} for tensor {tensor.name}")


def reshape_1d(values: Sequence[float], length: int) -> List[float]:
    vals = [float(v) for v in values]
    if len(vals) != int(length):
        raise ValueError(f"expected length {length}, got {len(vals)}")
    return vals


def reshape_2d(values: Sequence[float], rows: int, cols: int) -> Tensor2D:
    vals = [float(v) for v in values]
    if len(vals) != int(rows) * int(cols):
        raise ValueError(f"expected {rows}x{cols} values, got {len(vals)}")
    out: Tensor2D = []
    for r in range(int(rows)):
        start = r * int(cols)
        out.append(vals[start:start + int(cols)])
    return out


def deterministic_input(seq_len: int, hidden_dim: int) -> Tensor2D:
    out: Tensor2D = []
    for r in range(int(seq_len)):
        row: List[float] = []
        for c in range(int(hidden_dim)):
            value = (((r * 17 + c * 11 + 5) % 29) - 14) / 8.0
            row.append(float(value))
        out.append(row)
    return out


def gemm_rows(x: Tensor2D, w_out_in: Tensor2D, bias: Sequence[float]) -> Tensor2D:
    if not x:
        return []
    in_dim = len(x[0])
    out_dim = len(w_out_in)
    if len(bias) != out_dim:
        raise ValueError('bias length mismatch')
    for row in x:
        if len(row) != in_dim:
            raise ValueError('ragged input tensor')
    for row in w_out_in:
        if len(row) != in_dim:
            raise ValueError('weight/input dimension mismatch')

    out: Tensor2D = []
    for row in x:
        out_row: List[float] = []
        for out_idx in range(out_dim):
            acc = float(bias[out_idx])
            w_row = w_out_in[out_idx]
            for k in range(in_dim):
                acc += float(row[k]) * float(w_row[k])
            out_row.append(acc)
        out.append(out_row)
    return out


def softmax_rows(x: Tensor2D) -> Tensor2D:
    out: Tensor2D = []
    for row in x:
        if not row:
            out.append([])
            continue
        m = max(row)
        exps = [math.exp(float(v) - float(m)) for v in row]
        denom = sum(exps)
        if denom <= 0.0:
            raise ValueError('softmax denominator must be positive')
        out.append([float(v / denom) for v in exps])
    return out


def tensor_doc(name: str, values: Tensor2D) -> TensorDoc:
    rows = len(values)
    cols = len(values[0]) if rows else 0
    return {
        'name': name,
        'shape': [rows, cols],
        'values': values,
    }


def _load_initializer_2d(model: OnnxModel, name: str) -> Tensor2D:
    tensor = model.graph.initializers.get(name)
    if tensor is None or len(tensor.dims) != 2:
        raise ValueError(f'missing 2D initializer {name}')
    vals = decode_initializer_values(tensor)
    return reshape_2d(vals, int(tensor.dims[0]), int(tensor.dims[1]))


def _load_initializer_1d(model: OnnxModel, name: str) -> List[float]:
    tensor = model.graph.initializers.get(name)
    if tensor is None or len(tensor.dims) != 1:
        raise ValueError(f'missing 1D initializer {name}')
    vals = decode_initializer_values(tensor)
    return reshape_1d(vals, int(tensor.dims[0]))


def evaluate_attention_proxy_model(model: OnnxModel, x_values: Tensor2D) -> Dict[str, Tensor2D]:
    env: Dict[str, Tensor2D] = {'X': x_values}
    outputs: Dict[str, Tensor2D] = {}

    for node in model.graph.nodes:
        op = node.op_type
        if op == 'Cast':
            env[node.outputs[0]] = [list(row) for row in env[node.inputs[0]]]
            continue
        if op == 'Gemm':
            inp = env[node.inputs[0]]
            w = _load_initializer_2d(model, node.inputs[1])
            b = _load_initializer_1d(model, node.inputs[2])
            out = gemm_rows(inp, w, b)
            env[node.outputs[0]] = out
            outputs[node.outputs[0]] = out
            continue
        if op == 'Softmax':
            inp = env[node.inputs[0]]
            out = softmax_rows(inp)
            env[node.outputs[0]] = out
            outputs[node.outputs[0]] = out
            continue
        raise ValueError(f'unsupported op in llm reference evaluator: {op}')

    for out_name in model.graph.outputs.keys():
        outputs[out_name] = env[out_name]
    return outputs


def build_reference_fixture(model_path: Union[str, Path], *, model_id: str | None = None) -> Dict[str, Any]:
    model = load_onnx_model(model_path)
    input_shape = model.graph.inputs.get('X')
    if input_shape is None or len(input_shape) != 2:
        raise ValueError('llm reference path expects 2D X input')
    x = deterministic_input(int(input_shape[0]), int(input_shape[1]))
    outputs = evaluate_attention_proxy_model(model, x)
    fixture_outputs = {name: tensor_doc(name, values) for name, values in outputs.items()}
    return {
        'version': 0.1,
        'model_id': model_id or Path(model_path).stem,
        'input': tensor_doc('X', x),
        'outputs': fixture_outputs,
    }


def _flatten_values(values: Any) -> List[float]:
    if isinstance(values, list):
        out: List[float] = []
        for item in values:
            out.extend(_flatten_values(item))
        return out
    return [float(values)]


def tensor_error_metrics(reference: Tensor2D, candidate: Tensor2D) -> Dict[str, float]:
    ref = _flatten_values(reference)
    cand = _flatten_values(candidate)
    if len(ref) != len(cand):
        raise ValueError(f'reference/candidate length mismatch: {len(ref)} vs {len(cand)}')
    if not ref:
        return {
            'count': 0.0,
            'mean_abs_error': 0.0,
            'max_abs_error': 0.0,
            'rmse': 0.0,
        }
    abs_err = [abs(a - b) for a, b in zip(ref, cand)]
    sq_err = [(a - b) ** 2 for a, b in zip(ref, cand)]
    return {
        'count': float(len(ref)),
        'mean_abs_error': float(sum(abs_err) / len(abs_err)),
        'max_abs_error': float(max(abs_err)),
        'rmse': float(math.sqrt(sum(sq_err) / len(sq_err))),
    }


def load_json_doc(path: Union[str, Path]) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding='utf-8'))


def compare_reference_docs(reference_doc: Dict[str, Any], candidate_doc: Dict[str, Any]) -> Dict[str, Any]:
    ref_outputs = reference_doc.get('outputs', {}) if isinstance(reference_doc.get('outputs'), dict) else {}
    cand_outputs = candidate_doc.get('outputs', {}) if isinstance(candidate_doc.get('outputs'), dict) else {}

    if not cand_outputs and isinstance(candidate_doc, dict):
        if 'shape' in candidate_doc and 'values' in candidate_doc:
            cand_outputs = {'Y': candidate_doc}
        else:
            cand_outputs = {
                key: value for key, value in candidate_doc.items() if isinstance(value, dict) and 'values' in value
            }

    metrics_by_output: Dict[str, Any] = {}
    aggregate_abs: List[float] = []
    aggregate_sq: List[float] = []
    aggregate_count = 0

    for name, ref_tensor in ref_outputs.items():
        cand_tensor = cand_outputs.get(name)
        if cand_tensor is None:
            continue
        metrics = tensor_error_metrics(ref_tensor['values'], cand_tensor['values'])
        metrics_by_output[name] = metrics
        count = int(metrics['count'])
        aggregate_count += count
        mae = float(metrics['mean_abs_error'])
        rmse = float(metrics['rmse'])
        aggregate_abs.append(mae * count)
        aggregate_sq.append((rmse ** 2) * count)

    aggregate = {
        'count': float(aggregate_count),
        'mean_abs_error': float(sum(aggregate_abs) / aggregate_count) if aggregate_count else 0.0,
        'max_abs_error': max((float(m['max_abs_error']) for m in metrics_by_output.values()), default=0.0),
        'rmse': float(math.sqrt(sum(aggregate_sq) / aggregate_count)) if aggregate_count else 0.0,
    }
    return {
        'version': 0.1,
        'model_id': reference_doc.get('model_id', candidate_doc.get('model_id', 'unknown')),
        'per_output': metrics_by_output,
        'aggregate': aggregate,
    }
