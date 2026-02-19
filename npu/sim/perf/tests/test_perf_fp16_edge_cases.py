import json
import struct
import subprocess
import tempfile
from pathlib import Path


def _encode_gemm_tag(m: int, n: int, k: int) -> int:
    return ((int(m) & 0xFFF) << 20) | ((int(n) & 0x3FF) << 10) | (int(k) & 0x3FF)


def _write_gemm_fp16_ieee_edge_bin(path: Path):
    stream = bytearray()
    tag = _encode_gemm_tag(1, 1, 1)
    # zero, signed-zero, subnormal, inf, nan
    cases = [
        (0x0000, 0x3C00),
        (0x8000, 0x3C00),
        (0x0001, 0x3C00),
        (0x7C00, 0x3C00),
        (0x7E00, 0x3C00),
    ]
    for a_bits, b_bits in cases:
        raw = bytearray(32)
        struct.pack_into("<BBBBI", raw, 0, 0x10, 0x00, 0x01, 0x00, tag)
        struct.pack_into("<H", raw, 8, int(a_bits) & 0xFFFF)
        struct.pack_into("<H", raw, 16, int(b_bits) & 0xFFFF)
        stream.extend(raw)
    path.write_bytes(bytes(stream))


def _write_vec_fp16_edge_bin(path: Path):
    def _pack_words(words):
        out = 0
        for idx, w in enumerate(words):
            out |= (int(w) & 0xFFFF) << (16 * idx)
        return out

    stream = bytearray()
    descs = [
        # add: signed-zero/subnormal/inf behavior
        (0x11, [0x0000, 0x8000, 0x0001, 0x7C00], [0x8000, 0x0000, 0x8001, 0x0000]),
        # mul: signed-zero canonicalization + subnormal + -inf
        (0x12, [0x0000, 0x8000, 0x0001, 0xFC00], [0x3C00, 0x3C00, 0x3C00, 0x3C00]),
        # relu: preserve +subnormal/+inf/+nan, clamp -0
        (0x10, [0x8000, 0x0001, 0x7C00, 0x7E00], [0x0000, 0x0000, 0x0000, 0x0000]),
        # relu: preserve -nan payload and clamp negative finite
        (0x10, [0xFE00, 0x8001, 0x0000, 0x7C00], [0x0000, 0x0000, 0x0000, 0x0000]),
    ]
    for flags, a_words, b_words in descs:
        raw = bytearray(32)
        struct.pack_into("<BBBBI", raw, 0, 0x11, int(flags) & 0xFF, 0x01, 0x00, 0x0)
        struct.pack_into("<Q", raw, 8, _pack_words(a_words))
        struct.pack_into("<Q", raw, 16, _pack_words(b_words))
        struct.pack_into("<I", raw, 24, 256)
        stream.extend(raw)
    path.write_bytes(bytes(stream))


def _is_nan_word(bits: int) -> bool:
    bits = int(bits) & 0xFFFF
    return (bits & 0x7C00) == 0x7C00 and (bits & 0x03FF) != 0


def _words_from_bytes(byte_list):
    out = []
    for i in range(0, len(byte_list), 2):
        out.append((int(byte_list[i]) & 0xFF) | ((int(byte_list[i + 1]) & 0xFF) << 8))
    return out


def test_perf_gemm_fp16_ieee_edge_fields():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        bin_path = tmp / "gemm_fp16_edge.bin"
        out_path = tmp / "trace.json"
        cfg_path = tmp / "cfg.json"
        _write_gemm_fp16_ieee_edge_bin(bin_path)
        cfg_path.write_text(
            json.dumps(
                {
                    "gemm_mac_type": "fp16",
                    "gemm_mac_lanes": 1,
                    "gemm_fp16_semantics": "ieee_half",
                    "gemm_fp16_accumulation": "fp16",
                    "gemm_fp16_rounding": "rne",
                    "gemm_fp16_subnormals": "preserve",
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        subprocess.check_call(
            [
                "python3",
                "npu/sim/perf/run.py",
                "--bin",
                str(bin_path),
                "--out",
                str(out_path),
                "--config",
                str(cfg_path),
            ]
        )
        data = json.loads(out_path.read_text(encoding="utf-8"))

    trace = data["trace"]
    assert len(trace) == 5
    assert [ev["name"] for ev in trace] == ["GEMM"] * 5

    for ev in trace:
        assert ev["fp16_semantics"] == "ieee_half"
        assert ev["fp16_accumulation"] == "fp16"
        assert ev["fp16_rounding"] == "rne"
        assert ev["fp16_subnormals"] == "preserve"
        assert int(ev["lanes"]) == 1
        assert int(ev["expected_cycles"]) == 1

    assert trace[0]["expected_accum_fp16_hex"] == "0x0000"
    assert trace[1]["expected_accum_fp16_hex"] == "0x0000"
    assert trace[2]["expected_accum_fp16_hex"] == "0x0001"
    assert trace[3]["expected_accum_fp16_hex"] == "0x7c00"
    assert _is_nan_word(int(trace[4]["expected_accum_fp16_hex"], 0))


def _run_vec_edge_config(vec_fp16_activation_source: str):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        bin_path = tmp / "vec_fp16_edge.bin"
        out_path = tmp / "trace.json"
        cfg_path = tmp / "cfg.json"
        _write_vec_fp16_edge_bin(bin_path)
        cfg = {
            "vec_tops": 1.0,
            "vec_in_bw_gbps": 16.0,
            "vec_out_bw_gbps": 16.0,
            "vec_overhead_ns": 0.0,
            "vec_lanes": 8,
        }
        if vec_fp16_activation_source:
            cfg["vec_fp16_activation_source"] = vec_fp16_activation_source
        cfg_path.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
        subprocess.check_call(
            [
                "python3",
                "npu/sim/perf/run.py",
                "--bin",
                str(bin_path),
                "--out",
                str(out_path),
                "--config",
                str(cfg_path),
            ]
        )
        return json.loads(out_path.read_text(encoding="utf-8"))


def test_perf_vec_fp16_edge_fields_builtin_and_cpp():
    builtin = _run_vec_edge_config("")
    cpp = _run_vec_edge_config("rtlgen_cpp")

    for data in (builtin, cpp):
        trace = data["trace"]
        assert len(trace) == 4
        assert [ev["name"] for ev in trace] == ["VEC_OP"] * 4
        assert [ev["op"] for ev in trace] == ["add", "mul", "relu", "relu"]
        for ev in trace:
            assert ev["dtype"] == "fp16"
            assert int(ev["dtype_code"]) == 1
            assert int(ev["lanes"]) == 8
            assert len(ev["expected_result_bytes"]) == 8

        add_words = _words_from_bytes(trace[0]["expected_result_bytes"])
        mul_words = _words_from_bytes(trace[1]["expected_result_bytes"])
        relu_words0 = _words_from_bytes(trace[2]["expected_result_bytes"])
        relu_words1 = _words_from_bytes(trace[3]["expected_result_bytes"])

        assert add_words == [0x0000, 0x0000, 0x0000, 0x7C00]
        assert mul_words == [0x0000, 0x0000, 0x0001, 0xFC00]
        assert relu_words0 == [0x0000, 0x0001, 0x7C00, 0x7E00]
        assert relu_words1 == [0xFE00, 0x0000, 0x0000, 0x7C00]


if __name__ == "__main__":
    test_perf_gemm_fp16_ieee_edge_fields()
    test_perf_vec_fp16_edge_fields_builtin_and_cpp()
