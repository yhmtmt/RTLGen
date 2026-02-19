import json
import struct
import subprocess
import tempfile
from pathlib import Path


def _pack_desc(opcode, flags=0, size_units=1, tag=0):
    raw = bytearray(32 * size_units)
    struct.pack_into("<BBBBI", raw, 0, opcode & 0xFF, flags & 0xFF, size_units & 0xFF, 0, tag & 0xFFFFFFFF)
    return raw


def _pack_vec_fp16_operands(desc: bytearray, a_words, b_words, size_bytes=1024):
    for lane, bits in enumerate(a_words):
        struct.pack_into("<H", desc, 8 + (lane * 2), int(bits) & 0xFFFF)
    for lane, bits in enumerate(b_words):
        struct.pack_into("<H", desc, 16 + (lane * 2), int(bits) & 0xFFFF)
    struct.pack_into("<I", desc, 24, int(size_bytes) & 0xFFFFFFFF)


def _words_from_bytes(byte_list):
    out = []
    for i in range(0, len(byte_list), 2):
        out.append((int(byte_list[i]) & 0xFF) | ((int(byte_list[i + 1]) & 0xFF) << 8))
    return out


def _build_vec_fp16_bin(path: Path):
    stream = bytearray()

    # fp16 operands packed in descriptor data bytes (4 lanes x 16b each)
    a_words = [0x3C00, 0xC000, 0x3800, 0x0000]  # [1.0, -2.0, 0.5, 0.0]
    b_words = [0x3800, 0x3C00, 0xB800, 0x4000]  # [0.5, 1.0, -0.5, 2.0]

    # VEC_OP add, dtype fp16 (flags high nibble=1, low nibble=1)
    d0 = _pack_desc(0x11, flags=0x11)
    _pack_vec_fp16_operands(d0, a_words, b_words, size_bytes=256)
    stream.extend(d0)

    # VEC_OP mul, dtype fp16
    d1 = _pack_desc(0x11, flags=0x12)
    _pack_vec_fp16_operands(d1, a_words, b_words, size_bytes=512)
    stream.extend(d1)

    # VEC_OP relu, dtype fp16
    d2 = _pack_desc(0x11, flags=0x10)
    _pack_vec_fp16_operands(d2, a_words, b_words, size_bytes=768)
    stream.extend(d2)

    # VEC_OP gelu, dtype fp16
    d3 = _pack_desc(0x11, flags=0x13)
    _pack_vec_fp16_operands(d3, a_words, b_words, size_bytes=1024)
    stream.extend(d3)

    # VEC_OP softmax, dtype fp16
    d4 = _pack_desc(0x11, flags=0x14)
    _pack_vec_fp16_operands(d4, a_words, b_words, size_bytes=1280)
    stream.extend(d4)

    # VEC_OP layernorm, dtype fp16
    d5 = _pack_desc(0x11, flags=0x15)
    _pack_vec_fp16_operands(d5, a_words, b_words, size_bytes=1536)
    stream.extend(d5)

    path.write_bytes(bytes(stream))


def test_perf_vec_fp16_expected_fields():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        bin_path = tmp / "vec_fp16.bin"
        out_path = tmp / "trace.json"
        cfg_path = tmp / "cfg.json"
        _build_vec_fp16_bin(bin_path)
        cfg_path.write_text(
            json.dumps(
                {
                    "vec_tops": 1.0,
                    "vec_in_bw_gbps": 16.0,
                    "vec_out_bw_gbps": 16.0,
                    "vec_overhead_ns": 0.0,
                    # byte lanes used for result-compare masking; fp16 uses 2 bytes/element
                    "vec_lanes": 8,
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
    assert len(trace) == 6
    assert [ev["name"] for ev in trace] == ["VEC_OP", "VEC_OP", "VEC_OP", "VEC_OP", "VEC_OP", "VEC_OP"]
    assert [ev["op"] for ev in trace] == ["add", "mul", "relu", "gelu", "softmax", "layernorm"]
    for ev in trace:
        assert ev["dtype"] == "fp16"
        assert int(ev["dtype_code"]) == 1
        assert int(ev["lanes"]) == 8
        assert len(ev["expected_result_bytes"]) == 8

    add_words = _words_from_bytes(trace[0]["expected_result_bytes"])
    mul_words = _words_from_bytes(trace[1]["expected_result_bytes"])
    relu_words = _words_from_bytes(trace[2]["expected_result_bytes"])
    gelu_words = _words_from_bytes(trace[3]["expected_result_bytes"])
    softmax_words = _words_from_bytes(trace[4]["expected_result_bytes"])
    layernorm_words = _words_from_bytes(trace[5]["expected_result_bytes"])

    assert add_words == [0x3E00, 0xBC00, 0x0000, 0x4000]
    assert mul_words == [0x3800, 0xC000, 0xB400, 0x0000]
    assert relu_words == [0x3C00, 0x0000, 0x3800, 0x0000]
    assert gelu_words == [0x3800, 0x0000, 0x3400, 0x0000]
    assert softmax_words == [0x4400, 0x0000, 0x4000, 0x0000]
    assert layernorm_words == [0x3800, 0xBC00, 0x3400, 0x0000]


if __name__ == "__main__":
    test_perf_vec_fp16_expected_fields()
