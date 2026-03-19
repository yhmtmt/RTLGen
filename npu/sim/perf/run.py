#!/usr/bin/env python3
import argparse
import json
import math
import struct
from pathlib import Path

import model

try:
    import yaml
except ImportError:  # pragma: no cover - optional dependency
    yaml = None


DTYPE_NAMES = {
    0x0: "int8",
    0x1: "fp16",
    0x2: "bf16",
    0x3: "fp8",
}

DTYPE_BYTES = {
    0x0: 1.0,
    0x1: 2.0,
    0x2: 2.0,
    0x3: 1.0,
}

VEC_OP_NAMES = {
    0x0: "relu",
    0x1: "add",
    0x2: "mul",
    0x3: "gelu",
    0x4: "softmax",
    0x5: "layernorm",
    0x6: "drelu",
    0x7: "dgelu",
    0x8: "dsoftmax",
    0x9: "dlayernorm",
    0xA: "sigmoid",
}

def parse_desc_stream(data):
    descs = []
    offset = 0
    data_len = len(data)
    while offset + 32 <= data_len:
        size_units = data[offset + 2]
        if size_units == 0:
            size_units = 1
        size_bytes = 32 * size_units
        if offset + size_bytes > data_len:
            break
        chunk = data[offset:offset + size_bytes]
        opcode = chunk[0]
        flags = chunk[1]
        tag = struct.unpack_from("<I", chunk, 4)[0]
        descs.append({
            "offset": offset,
            "opcode": opcode,
            "flags": flags,
            "size_units": size_units,
            "tag": tag,
            "raw": chunk,
        })
        offset += size_bytes
    return descs


def decode_gemm_tag(tag):
    m = (tag >> 20) & 0xFFF
    n = (tag >> 10) & 0x3FF
    k = tag & 0x3FF
    return m, n, k


def _sx8(v):
    v = int(v) & 0xFF
    return v - 256 if (v & 0x80) else v


def _u8(v):
    return int(v) & 0xFF


def _sx16(lo, hi):
    v = ((int(hi) & 0xFF) << 8) | (int(lo) & 0xFF)
    return v - 65536 if (v & 0x8000) else v


def _u16(v):
    return int(v) & 0xFFFF


def _s16_from_u16(v):
    x = _u16(v)
    return x - 65536 if (x & 0x8000) else x


def _fp16_bits_to_float(bits):
    return struct.unpack("<e", struct.pack("<H", _u16(bits)))[0]


def _float_to_fp16_bits(value):
    try:
        return struct.unpack("<H", struct.pack("<e", float(value)))[0]
    except OverflowError:
        sign = math.copysign(1.0, float(value))
        return 0xFC00 if sign < 0 else 0x7C00


def _fp16_is_nan(bits):
    bits = _u16(bits)
    return ((bits & 0x7C00) == 0x7C00) and ((bits & 0x03FF) != 0)


def _fp16_canonicalize_zero(bits):
    bits = _u16(bits)
    if (bits & 0x7FFF) == 0:
        return 0x0000
    return bits


def _fp16_fma_bits(a_bits, b_bits, c_bits):
    a = _fp16_bits_to_float(a_bits)
    b = _fp16_bits_to_float(b_bits)
    c = _fp16_bits_to_float(c_bits)
    if hasattr(math, "fma"):
        out = math.fma(a, b, c)
    else:
        out = (a * b) + c
    return _float_to_fp16_bits(out)


def _gemm_elem_bits(cfg):
    mac_type = str(cfg.get("gemm_mac_type", "int8")).lower()
    return 16 if mac_type in ("int16", "fp16") else 8


def _gemm_lanes(cfg):
    elem_bits = _gemm_elem_bits(cfg)
    default_lanes = 4 if elem_bits == 16 else 8
    lanes = int(cfg.get("gemm_mac_lanes", default_lanes))
    max_lanes = 4 if elem_bits == 16 else 8
    if lanes < 1:
        return 1
    if lanes > max_lanes:
        return max_lanes
    return lanes


def _gemm_fp16_policy(cfg):
    semantics = str(cfg.get("gemm_fp16_semantics", "raw16_placeholder")).lower()
    accumulation = str(cfg.get("gemm_fp16_accumulation", "int32")).lower()
    rounding = str(cfg.get("gemm_fp16_rounding", "rne")).lower()
    subnormals = str(cfg.get("gemm_fp16_subnormals", "preserve")).lower()

    if semantics not in ("raw16_placeholder", "ieee_half"):
        raise ValueError("gemm_fp16_semantics must be one of: raw16_placeholder, ieee_half")
    if accumulation not in ("int32", "fp32", "fp16"):
        raise ValueError("gemm_fp16_accumulation must be one of: int32, fp32, fp16")
    if rounding not in ("rne",):
        raise ValueError("gemm_fp16_rounding must be: rne")
    if subnormals not in ("preserve", "flush"):
        raise ValueError("gemm_fp16_subnormals must be one of: preserve, flush")

    lanes = _gemm_lanes(cfg)
    if semantics == "raw16_placeholder":
        if accumulation != "int32":
            raise ValueError("gemm_fp16_accumulation must be int32 when gemm_fp16_semantics=raw16_placeholder")
        if rounding != "rne":
            raise ValueError("gemm_fp16_rounding must be rne for current fp16 bring-up path")
        if subnormals != "preserve":
            raise ValueError("gemm_fp16_subnormals must be preserve for current fp16 bring-up path")
    else:
        if accumulation != "fp16":
            raise ValueError("gemm_fp16_accumulation must be fp16 when gemm_fp16_semantics=ieee_half")
        if rounding != "rne":
            raise ValueError("gemm_fp16_rounding must be rne for current fp16 ieee_half backend")
        if subnormals != "preserve":
            raise ValueError("gemm_fp16_subnormals must be preserve for current fp16 ieee_half backend")
        if lanes != 1:
            raise ValueError("gemm_mac_lanes must be 1 when gemm_fp16_semantics=ieee_half")

    return {
        "semantics": semantics,
        "accumulation": accumulation,
        "rounding": rounding,
        "subnormals": subnormals,
    }


def _vec_lanes(cfg):
    lanes = int(cfg.get("vec_lanes", cfg.get("gemm_mac_lanes", 8)))
    if lanes < 1:
        return 1
    if lanes > 8:
        return 8
    return lanes


def _vec_fp16_activation_source(cfg):
    src = str(cfg.get("vec_fp16_activation_source", "builtin")).lower()
    if src not in ("builtin", "rtlgen_cpp"):
        raise ValueError("vec_fp16_activation_source must be one of: builtin, rtlgen_cpp")
    return src


def _vec_softmax_int8(x):
    if x < 0:
        return 0
    if x > 31:
        return 127
    return _u8(x << 2)


def _vec_sigmoid_int8(x):
    x = int(x)
    if x < -64:
        return 0
    if x < -32:
        return _u8((x + 64) >> 4)
    if x < 32:
        return _u8(((3 * x) >> 4) + 8)
    if x < 64:
        return _u8((x >> 4) + 12)
    return 16


def _fp16_add_bits(a_bits, b_bits):
    return _fp16_canonicalize_zero(
        _float_to_fp16_bits(_fp16_bits_to_float(a_bits) + _fp16_bits_to_float(b_bits))
    )


def _fp16_mul_bits(a_bits, b_bits):
    return _fp16_canonicalize_zero(
        _float_to_fp16_bits(_fp16_bits_to_float(a_bits) * _fp16_bits_to_float(b_bits))
    )


def _fp16_relu_bits(x_bits):
    x = _fp16_bits_to_float(x_bits)
    if math.isnan(x):
        return _u16(x_bits)
    if x <= 0.0:
        return 0
    return _u16(x_bits)


def _vec_fp16_cpp_activation_bits(a_bits, op_code):
    a_bits = _u16(a_bits)
    sign = (a_bits >> 15) & 0x1
    exp_bits = (a_bits >> 10) & 0x1F
    frac_bits = a_bits & 0x03FF
    payload_nonzero = (a_bits & 0x7FFF) != 0

    if op_code == 0x3:  # gelu
        if sign:
            return 0x0000
        exp_half = (exp_bits - 1) & 0x1F
        return _u16((exp_half << 10) | frac_bits)
    if op_code == 0x4:  # softmax
        if sign:
            return 0x0000
        if exp_bits >= 15:
            return 0x3C00
        return a_bits
    if op_code == 0x5:  # layernorm
        return a_bits
    if op_code == 0x6:  # drelu
        return 0x3C00 if (not sign and payload_nonzero) else 0x0000
    if op_code == 0x7:  # dgelu
        return 0x3800 if (not sign and payload_nonzero) else 0x0000
    if op_code == 0x8:  # dsoftmax
        return 0x3400
    if op_code == 0x9:  # dlayernorm
        return 0x3C00
    # relu/fallback
    return 0x0000 if sign else a_bits


def _vec_expected_result(raw, flags, cfg, dtype_code=0x0):
    op_code = int(flags) & 0xF
    dtype_code = int(dtype_code) & 0xF

    # fp16 vector path packs 4x16b lanes in descriptor bytes [8:15] and [16:23].
    # `lanes` in output remains byte-lane count so compare_compute_results masking stays unchanged.
    if dtype_code == 0x1:
        fp16_act_source = _vec_fp16_activation_source(cfg)
        byte_lanes = _vec_lanes(cfg)
        if byte_lanes % 2 != 0:
            raise ValueError("vec_lanes must be even when VEC dtype=fp16")
        elem_lanes = byte_lanes // 2
        if elem_lanes > 4:
            elem_lanes = 4
        if elem_lanes < 1:
            elem_lanes = 1
        result = []
        for lane in range(elem_lanes):
            a_bits = ((int(raw[9 + (lane * 2)]) & 0xFF) << 8) | (int(raw[8 + (lane * 2)]) & 0xFF)
            b_bits = ((int(raw[17 + (lane * 2)]) & 0xFF) << 8) | (int(raw[16 + (lane * 2)]) & 0xFF)
            x = _fp16_bits_to_float(a_bits)
            if op_code == 0x1:  # add
                out_bits = _fp16_add_bits(a_bits, b_bits)
            elif op_code == 0x2:  # mul
                out_bits = _fp16_mul_bits(a_bits, b_bits)
            elif fp16_act_source == "rtlgen_cpp":
                # RTL fp16 activation wiring bypasses C++ units for NaN on relu/gelu/softmax.
                if _fp16_is_nan(a_bits) and op_code in (0x0, 0x3, 0x4):
                    out_bits = _u16(a_bits)
                else:
                    out_bits = _vec_fp16_cpp_activation_bits(a_bits, op_code)
            elif op_code == 0x3:  # gelu
                out_bits = _fp16_relu_bits(_fp16_mul_bits(a_bits, 0x3800))
            elif op_code == 0x4:  # softmax (coarse scalar approximation)
                out_bits = _fp16_relu_bits(_fp16_mul_bits(a_bits, 0x4400))
            elif op_code == 0x5:  # layernorm (coarse scalar approximation)
                out_bits = _fp16_mul_bits(a_bits, 0x3800)
            elif op_code == 0x6:  # drelu
                out_bits = _float_to_fp16_bits(1.0 if x > 0.0 else 0.0)
            elif op_code == 0x7:  # dgelu
                out_bits = _float_to_fp16_bits(1.0 if x > 0.0 else 0.0)
            elif op_code == 0x8:  # dsoftmax (coarse scalar approximation)
                p_bits = _fp16_relu_bits(_fp16_mul_bits(a_bits, 0x4400))
                one_minus_p_bits = _fp16_add_bits(_fp16_mul_bits(p_bits, 0xBC00), 0x3C00)
                out_bits = _fp16_mul_bits(p_bits, one_minus_p_bits)
            elif op_code == 0x9:  # dlayernorm
                out_bits = _float_to_fp16_bits(1.0)
            else:  # relu/fallback for currently unsupported fp16 vec kernels
                out_bits = _fp16_relu_bits(a_bits)
            result.append(int(out_bits) & 0xFF)
            result.append((int(out_bits) >> 8) & 0xFF)

        packed = 0
        for lane, val in enumerate(result):
            packed |= (int(val) & 0xFF) << (lane * 8)
        return {
            "result_bytes": result,
            "result_hex": f"0x{packed:0{len(result) * 2}x}",
            "lanes": len(result),
        }

    lanes = _vec_lanes(cfg)
    result = []
    for lane in range(lanes):
        x = _sx8(raw[8 + lane])
        y = _sx8(raw[16 + lane])
        if op_code == 0x1:  # add
            out = _u8(x + y)
        elif op_code == 0x2:  # mul
            out = _u8(x * y)
        elif op_code == 0x3:  # gelu
            out = _u8(0 if x < 0 else (x >> 1))
        elif op_code == 0x4:  # softmax
            out = _vec_softmax_int8(x)
        elif op_code == 0x5:  # layernorm
            out = _u8(x >> 1)
        elif op_code == 0x6:  # drelu
            out = 1 if x > 0 else 0
        elif op_code == 0x7:  # dgelu
            out = 1 if x > 0 else 0
        elif op_code == 0x8:  # dsoftmax
            p = _vec_softmax_int8(x)
            out = _u8((p * (127 - p)) >> 7)
        elif op_code == 0x9:  # dlayernorm
            out = 1
        elif op_code == 0xA:  # sigmoid
            out = _vec_sigmoid_int8(x)
        else:  # relu / fallback
            out = 0 if x < 0 else _u8(x)
        result.append(_u8(out))
    packed = 0
    for lane, val in enumerate(result):
        packed |= (int(val) & 0xFF) << (lane * 8)
    return {
        "result_bytes": result,
        "result_hex": f"0x{packed:0{lanes * 2}x}",
        "lanes": lanes,
    }


def _gemm_expected_fields(raw, size_units, tag, cfg):
    mac_type = str(cfg.get("gemm_mac_type", "int8")).lower()
    lanes = _gemm_lanes(cfg)
    elem_bits = _gemm_elem_bits(cfg)
    fp16_policy = _gemm_fp16_policy(cfg) if mac_type == "fp16" else None
    dot = 0
    if elem_bits == 16:
        for lane in range(lanes):
            a_lo = raw[8 + (lane * 2)]
            a_hi = raw[9 + (lane * 2)]
            b_lo = raw[16 + (lane * 2)]
            b_hi = raw[17 + (lane * 2)]
            dot += _sx16(a_lo, a_hi) * _sx16(b_lo, b_hi)
    else:
        for lane in range(lanes):
            dot += _sx8(raw[8 + lane]) * _sx8(raw[16 + lane])

    if size_units >= 2 and len(raw) >= 64:
        m = struct.unpack_from("<I", raw, 32)[0]
        n = struct.unpack_from("<I", raw, 36)[0]
        k = struct.unpack_from("<I", raw, 40)[0]
        op_uid = struct.unpack_from("<Q", raw, 56)[0]
    else:
        m, n, k = decode_gemm_tag(tag)
        op_uid = None

    if m == 0 or n == 0 or k == 0:
        cycles = 1
    else:
        cycles = ((int(m) * int(n) * int(k)) >> 10) + 1
    if op_uid is not None and ((int(op_uid) >> 63) & 0x1):
        cycles += 8

    if fp16_policy is not None and fp16_policy["semantics"] == "ieee_half":
        if lanes != 1:
            raise ValueError("gemm_mac_lanes must be 1 for fp16 ieee_half expected-result decode")
        a_bits = ((int(raw[9]) & 0xFF) << 8) | (int(raw[8]) & 0xFF)
        b_bits = ((int(raw[17]) & 0xFF) << 8) | (int(raw[16]) & 0xFF)
        dot_bits = _fp16_fma_bits(a_bits, b_bits, 0)
        accum_bits = 0
        for _ in range(int(cycles)):
            accum_bits = _fp16_fma_bits(a_bits, b_bits, accum_bits)
        out = {
            "expected_dot": _s16_from_u16(dot_bits),
            "expected_dot_fp16_hex": f"0x{_u16(dot_bits):04x}",
            "expected_cycles": int(cycles),
            "expected_accum": _s16_from_u16(accum_bits),
            "expected_accum_fp16_hex": f"0x{_u16(accum_bits):04x}",
            "lanes": lanes,
        }
    else:
        expected_accum = int(dot) * int(cycles)
        out = {
            "expected_dot": int(dot),
            "expected_cycles": int(cycles),
            "expected_accum": int(expected_accum),
            "lanes": lanes,
        }

    if fp16_policy is not None:
        out.update(
            {
                "fp16_semantics": fp16_policy["semantics"],
                "fp16_accumulation": fp16_policy["accumulation"],
                "fp16_rounding": fp16_policy["rounding"],
                "fp16_subnormals": fp16_policy["subnormals"],
            }
        )
    return out


def _parse_int(value):
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value, 0)
    return int(value)


def _decode_dtype(flags, cfg, key_prefix):
    dtype_code = (int(flags) >> 4) & 0xF
    dtype_name = DTYPE_NAMES.get(dtype_code, "int8")
    default_bytes = float(cfg.get(f"{key_prefix}_dtype_bytes", cfg.get("gemm_dtype_bytes", 1.0)))
    dtype_bytes = float(DTYPE_BYTES.get(dtype_code, default_bytes))
    return dtype_code, dtype_name, dtype_bytes


def _bytes_to_hex_le(data):
    payload = bytes(int(b) & 0xFF for b in data)
    if not payload:
        return "0x"
    return "0x" + payload[::-1].hex()


def _load_memory_image(path):
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    segments = doc.get("segments", [])
    if not isinstance(segments, list):
        raise ValueError("memory image must contain a list field 'segments'")

    mem = {}
    for seg in segments:
        if not isinstance(seg, dict):
            raise ValueError("memory image segments must be mappings")
        if "base_addr" in seg:
            base_addr = _parse_int(seg["base_addr"])
        elif "addr" in seg:
            base_addr = _parse_int(seg["addr"])
        else:
            raise ValueError("memory image segment missing base_addr/addr")
        if "data_bytes" in seg:
            raw_bytes = [int(v) & 0xFF for v in seg["data_bytes"]]
        elif "data_hex" in seg:
            hex_text = str(seg["data_hex"]).strip()
            if hex_text.startswith(("0x", "0X")):
                hex_text = hex_text[2:]
            if len(hex_text) % 2 != 0:
                raise ValueError("memory image data_hex must contain an even number of nybbles")
            raw_bytes = list(bytes.fromhex(hex_text))
        else:
            raise ValueError("memory image segment missing data_bytes/data_hex")
        for idx, byte in enumerate(raw_bytes):
            mem[int(base_addr) + idx] = int(byte) & 0xFF
    return mem


def _mem_read_bytes(mem, addr, size):
    out = []
    for offset in range(int(size)):
        loc = int(addr) + offset
        if loc not in mem:
            return None
        out.append(int(mem[loc]) & 0xFF)
    return out


def _mem_write_bytes(mem, addr, data):
    for offset, byte in enumerate(data):
        mem[int(addr) + offset] = int(byte) & 0xFF


def _softmax_reference_probs(values):
    if not values:
        return []
    finite = [float(v) if math.isfinite(float(v)) else 0.0 for v in values]
    max_val = max(finite)
    weights = [math.exp(v - max_val) for v in finite]
    denom = sum(weights)
    if denom <= 0.0 or not math.isfinite(denom):
        return [0.0 for _ in finite]
    return [w / denom for w in weights]


def _softmax_reference_int8_row(row_bytes):
    logits = [_sx8(b) for b in row_bytes]
    probs = _softmax_reference_probs(logits)
    out = []
    for prob in probs:
        q = int(math.floor((float(prob) * 127.0) + 0.5))
        if q < 0:
            q = 0
        if q > 127:
            q = 127
        out.append(q)
    return out


def _softmax_reference_fp16_row(row_bytes):
    if len(row_bytes) % 2 != 0:
        raise ValueError("fp16 softmax row_bytes must be a multiple of 2")
    logits = []
    for idx in range(0, len(row_bytes), 2):
        bits = ((int(row_bytes[idx + 1]) & 0xFF) << 8) | (int(row_bytes[idx]) & 0xFF)
        logits.append(_fp16_bits_to_float(bits))
    probs = _softmax_reference_probs(logits)
    out = []
    for prob in probs:
        bits = _float_to_fp16_bits(prob)
        out.append(bits & 0xFF)
        out.append((bits >> 8) & 0xFF)
    return out


def _softmax_expected_result(src_bytes, *, row_bytes, rows, dtype_code):
    row_bytes = int(row_bytes)
    rows = int(rows)
    if row_bytes < 0 or rows < 0:
        raise ValueError("softmax row_bytes and rows must be non-negative")
    total_bytes = row_bytes * rows
    if len(src_bytes) < total_bytes:
        raise ValueError("softmax source image shorter than descriptor payload")
    if dtype_code == 0x1:
        row_fn = _softmax_reference_fp16_row
        encoding = "fp16_ieee_half_le"
        semantics = "rowwise_reference_fp16"
    else:
        row_fn = _softmax_reference_int8_row
        encoding = "u8_q0_7"
        semantics = "rowwise_reference_int8"
    out = []
    for row_idx in range(rows):
        start = row_idx * row_bytes
        end = start + row_bytes
        out.extend(row_fn(src_bytes[start:end]))
    return {
        "expected_result_bytes": out,
        "expected_result": _bytes_to_hex_le(out),
        "expected_result_encoding": encoding,
        "softmax_semantics": semantics,
    }


def _derive_sram_instances(arch, metrics, clk_period_ns=None):
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
        if clk_period_ns and clk_period_ns > 0 and access_time_ns:
            access_time_ns = max(access_time_ns, clk_period_ns)
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
    clk_period_ns = cfg.get("clk_period_ns")
    cfg["sram_instances"] = _derive_sram_instances(arch, metrics, clk_period_ns)


def _validate_cfg(cfg):
    mac_type = str(cfg.get("gemm_mac_type", "int8")).lower()
    if mac_type not in ("int8", "int16", "fp16"):
        raise ValueError("gemm_mac_type must be one of: int8, int16, fp16")
    try:
        gemm_engine_count = int(cfg.get("gemm_engine_count", 1))
    except Exception as exc:
        raise ValueError(f"gemm_engine_count must be an int: {exc}")
    if gemm_engine_count < 1:
        raise ValueError("gemm_engine_count must be >= 1")
    _gemm_lanes(cfg)
    _vec_lanes(cfg)
    if mac_type == "fp16":
        _gemm_fp16_policy(cfg)


def desc_to_event(desc, cfg, memory=None):
    opcode = desc["opcode"]
    raw = desc["raw"]
    size_units = desc.get("size_units", 1)
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
        op_uid = None
        if size_units >= 2 and len(raw) >= 64:
            m = struct.unpack_from("<I", raw, 32)[0]
            n = struct.unpack_from("<I", raw, 36)[0]
            k = struct.unpack_from("<I", raw, 40)[0]
            op_uid = struct.unpack_from("<Q", raw, 56)[0]
        else:
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
        event.update(_gemm_expected_fields(raw, size_units, desc["tag"], cfg))
        if op_uid is not None:
            event["op_uid"] = op_uid
    elif opcode == 0x20:  # EVENT_SIGNAL
        event.update({
            "name": "EVENT_SIGNAL",
            "event_id": desc["tag"],
            "irq": bool(desc["flags"] & 0x1),
            "duration_ns": model.event_overhead_ns(cfg),
        })
    elif opcode == 0x11:  # VEC_OP
        src = struct.unpack_from("<Q", raw, 8)[0]
        dst = struct.unpack_from("<Q", raw, 16)[0]
        size = struct.unpack_from("<I", raw, 24)[0]
        op_code = desc["flags"] & 0xF
        op_name = VEC_OP_NAMES.get(op_code, "unknown")
        dtype_code, dtype_name, dtype_bytes = _decode_dtype(desc["flags"], cfg, "vec")
        vec_expected = _vec_expected_result(raw, desc["flags"], cfg, dtype_code=dtype_code)
        event.update({
            "name": "VEC_OP",
            "op": op_name,
            "op_code": op_code,
            "dtype": dtype_name,
            "dtype_code": dtype_code,
            "src": f"0x{src:016x}",
            "dst": f"0x{dst:016x}",
            "bytes": size,
            "duration_ns": model.vec_time_ns(size, op_name, cfg, dtype_bytes=dtype_bytes),
        })
        event.update(
            {
                "expected_result": vec_expected["result_hex"],
                "expected_result_bytes": vec_expected["result_bytes"],
                "lanes": vec_expected["lanes"],
            }
        )
        if op_name == "unknown":
            event["warning"] = f"unsupported vec op 0x{op_code:x}"
    elif opcode == 0x12:  # SOFTMAX
        src = struct.unpack_from("<Q", raw, 8)[0]
        dst = struct.unpack_from("<Q", raw, 16)[0]
        row_bytes = struct.unpack_from("<H", raw, 24)[0]
        rows = struct.unpack_from("<H", raw, 26)[0]
        dtype_code, dtype_name, dtype_bytes = _decode_dtype(desc["flags"], cfg, "softmax")
        total_bytes = int(row_bytes) * int(rows)
        event.update({
            "name": "SOFTMAX",
            "dtype": dtype_name,
            "dtype_code": dtype_code,
            "src": f"0x{src:016x}",
            "dst": f"0x{dst:016x}",
            "row_bytes": row_bytes,
            "rows": rows,
            "bytes": total_bytes,
            "duration_ns": model.softmax_time_ns(row_bytes, rows, cfg, dtype_bytes=dtype_bytes),
        })
        if memory is not None:
            src_bytes = _mem_read_bytes(memory, src, total_bytes)
            if src_bytes is None:
                event["warning"] = (
                    f"softmax expected-result unavailable: missing memory image for "
                    f"src=0x{src:016x} bytes={total_bytes}"
                )
            else:
                try:
                    event.update(
                        _softmax_expected_result(
                            src_bytes,
                            row_bytes=row_bytes,
                            rows=rows,
                            dtype_code=dtype_code,
                        )
                    )
                except ValueError as exc:
                    event["warning"] = f"softmax expected-result unavailable: {exc}"
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


def build_trace(descs, cfg, overlap, memory=None):
    trace = []
    now_ns = 0.0
    warnings = []
    stats = {
        "total_bytes": 0,
        "dma_ops": 0,
        "gemm_ops": 0,
        "vec_ops": 0,
        "softmax_ops": 0,
        "event_ops": 0,
        "noop_ops": 0,
        "unknown_ops": 0,
        "irq_events": 0,
        "dma_time_ns": 0.0,
        "gemm_time_ns": 0.0,
        "vec_time_ns": 0.0,
        "softmax_time_ns": 0.0,
        "event_time_ns": 0.0,
        "noop_time_ns": 0.0,
        "unknown_time_ns": 0.0,
    }
    queue_time = 0.0
    dma_engine_time = 0.0
    misc_compute_time = 0.0
    gemm_engine_count = max(1, int(cfg.get("gemm_engine_count", 1)))
    gemm_engine_times = [0.0 for _ in range(gemm_engine_count)]
    event_times = {}
    issue_overhead = float(cfg.get("issue_overhead_ns", 0.0))
    last_op_end = 0.0

    for desc in descs:
        event = desc_to_event(desc, cfg, memory=memory)
        dur = float(event.get("duration_ns", 0.0))
        if overlap:
            name = event.get("name")
            if name == "DMA_COPY":
                start = max(queue_time, dma_engine_time)
                end = start + dur
                dma_engine_time = end
                queue_time += issue_overhead
            elif name == "GEMM":
                gemm_engine_idx = min(range(gemm_engine_count), key=lambda idx: gemm_engine_times[idx])
                start = max(queue_time, misc_compute_time, gemm_engine_times[gemm_engine_idx])
                end = start + dur
                gemm_engine_times[gemm_engine_idx] = end
                queue_time += issue_overhead
                event["gemm_engine_idx"] = gemm_engine_idx
            elif name in ("VEC_OP", "SOFTMAX"):
                start = max(queue_time, misc_compute_time, max(gemm_engine_times))
                end = start + dur
                misc_compute_time = end
                queue_time += issue_overhead
            elif name == "EVENT_SIGNAL":
                # Signals inserted after a producer op should not become visible
                # before that producer has completed.
                start = max(queue_time, last_op_end)
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
            if name not in ("EVENT_SIGNAL", "EVENT_WAIT"):
                last_op_end = end
        else:
            event["start_ns"] = now_ns
            event["end_ns"] = now_ns + dur
            now_ns += dur
        trace.append(event)
        warning = event.get("warning")
        if warning:
            warnings.append(str(warning))

        name = event.get("name")
        if name == "DMA_COPY":
            stats["dma_ops"] += 1
            stats["total_bytes"] += int(event.get("bytes", 0))
            stats["dma_time_ns"] += dur
            if memory is not None:
                src_bytes = _mem_read_bytes(memory, int(event["src"], 0), int(event.get("bytes", 0)))
                if src_bytes is None:
                    warnings.append(
                        f"dma_copy memory update unavailable: missing memory image for "
                        f"src={event['src']} bytes={event.get('bytes', 0)}"
                    )
                else:
                    _mem_write_bytes(memory, int(event["dst"], 0), src_bytes)
        elif name == "GEMM":
            stats["gemm_ops"] += 1
            stats["gemm_time_ns"] += dur
        elif name == "VEC_OP":
            stats["vec_ops"] += 1
            stats["total_bytes"] += int(event.get("bytes", 0))
            stats["vec_time_ns"] += dur
        elif name == "SOFTMAX":
            stats["softmax_ops"] += 1
            stats["total_bytes"] += int(event.get("bytes", 0))
            stats["softmax_time_ns"] += dur
            if memory is not None and "expected_result_bytes" in event:
                _mem_write_bytes(memory, int(event["dst"], 0), event["expected_result_bytes"])
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
        gemm_engine_time = max(gemm_engine_times) if gemm_engine_times else 0.0
        total_ns = max(queue_time, dma_engine_time, gemm_engine_time, misc_compute_time)
        stats["queue_time_ns"] = queue_time
        stats["dma_engine_time_ns"] = dma_engine_time
        stats["gemm_engine_time_ns"] = gemm_engine_time
        stats["gemm_engine_count"] = gemm_engine_count
        stats["misc_compute_time_ns"] = misc_compute_time
    return trace, total_ns, stats, warnings


def format_summary(stats, warnings):
    lines = []
    lines.append("NPU perf summary")
    lines.append(f"  total_time_ns: {stats['total_time_ns']:.3f}")
    lines.append(f"  total_bytes: {stats['total_bytes']}")
    lines.append(f"  dma_ops: {stats['dma_ops']} (time_ns={stats['dma_time_ns']:.3f})")
    lines.append(f"  gemm_ops: {stats['gemm_ops']} (time_ns={stats['gemm_time_ns']:.3f})")
    lines.append(f"  vec_ops: {stats['vec_ops']} (time_ns={stats['vec_time_ns']:.3f})")
    lines.append(f"  softmax_ops: {stats['softmax_ops']} (time_ns={stats['softmax_time_ns']:.3f})")
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
    ap.add_argument("--mem-json", help="Optional memory image JSON for descriptor-backed expected results")
    ap.add_argument("--gemm-engine-count", type=int, help="Override GEMM engine count for overlap model")
    ap.add_argument("--summary", action="store_true", help="Print summary to stdout")
    ap.add_argument("--overlap", action="store_true", help="Enable DMA/compute overlap model")
    args = ap.parse_args()

    cfg = {}
    if args.config:
        cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
        _load_sram_model(cfg)
    if args.gemm_engine_count is not None:
        cfg["gemm_engine_count"] = max(1, int(args.gemm_engine_count))
    try:
        _validate_cfg(cfg)
    except ValueError as exc:
        raise SystemExit(f"invalid perf config: {exc}")

    data = Path(args.bin).read_bytes()
    descs = parse_desc_stream(data)
    memory = None
    if args.mem_json:
        try:
            memory = _load_memory_image(args.mem_json)
        except ValueError as exc:
            raise SystemExit(f"invalid memory image: {exc}")
    trace, total_ns, stats, warnings = build_trace(descs, cfg, args.overlap, memory=memory)

    out = {
        "meta": {
            "version": "0.1",
            "source_bin": str(args.bin),
            "mode": "overlap" if args.overlap else "sequential",
            "source_mem_json": str(args.mem_json) if args.mem_json else None,
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
