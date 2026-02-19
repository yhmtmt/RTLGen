import json
import struct
import subprocess
import tempfile
from pathlib import Path


def _encode_gemm_tag(m: int, n: int, k: int) -> int:
    return ((int(m) & 0xFFF) << 20) | ((int(n) & 0x3FF) << 10) | (int(k) & 0x3FF)


def _pack_gemm_desc_raw16(path: Path, *, tag: int, a_words: list[int], b_words: list[int]):
    raw = bytearray(32)
    # opcode=GEMM, flags=0, size_units=1, reserved=0
    struct.pack_into("<BBBBI", raw, 0, 0x10, 0x00, 0x01, 0x00, int(tag))
    for lane, val in enumerate(a_words):
        struct.pack_into("<H", raw, 8 + (lane * 2), int(val) & 0xFFFF)
    for lane, val in enumerate(b_words):
        struct.pack_into("<H", raw, 16 + (lane * 2), int(val) & 0xFFFF)
    path.write_bytes(bytes(raw))


def test_perf_gemm_fp16_expected_fields_raw_placeholder():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        bin_path = tmp / "gemm_fp16.bin"
        out_path = tmp / "trace.json"
        cfg_path = tmp / "cfg.json"
        _pack_gemm_desc_raw16(
            bin_path,
            tag=_encode_gemm_tag(1, 1, 1),
            a_words=[1, -2, 3, -4],
            b_words=[5, 6, -7, -8],
        )
        cfg_path.write_text(
            json.dumps(
                {
                    "gemm_mac_type": "fp16",
                    "gemm_mac_lanes": 4,
                    "gemm_fp16_semantics": "raw16_placeholder",
                    "gemm_fp16_accumulation": "int32",
                    "gemm_fp16_rounding": "rne",
                    "gemm_fp16_subnormals": "preserve",
                    "gemm_tops": 1.0,
                    "gemm_in_bw_gbps": 16.0,
                    "gemm_out_bw_gbps": 16.0,
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
    assert len(trace) == 1
    gemm = trace[0]
    assert gemm["name"] == "GEMM"
    assert gemm["expected_dot"] == 4
    assert gemm["expected_cycles"] == 1
    assert gemm["expected_accum"] == 4
    assert gemm["lanes"] == 4
    assert gemm["fp16_semantics"] == "raw16_placeholder"
    assert gemm["fp16_accumulation"] == "int32"
    assert gemm["fp16_rounding"] == "rne"
    assert gemm["fp16_subnormals"] == "preserve"


def test_perf_gemm_fp16_ieee_half_expected_fields():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        bin_path = tmp / "gemm_fp16.bin"
        out_path = tmp / "trace.json"
        cfg_path = tmp / "cfg.json"
        # A=1.0 (0x3c00), B=0.5 (0x3800), cycles=((32*32*32)>>10)+1=33
        _pack_gemm_desc_raw16(
            bin_path,
            tag=_encode_gemm_tag(32, 32, 32),
            a_words=[0x3C00],
            b_words=[0x3800],
        )
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
    assert len(trace) == 1
    gemm = trace[0]
    assert gemm["name"] == "GEMM"
    assert gemm["expected_cycles"] == 33
    assert gemm["lanes"] == 1
    assert gemm["expected_dot_fp16_hex"] == "0x3800"
    assert gemm["expected_dot"] == 14336
    assert gemm["expected_accum_fp16_hex"] == "0x4c20"
    assert gemm["expected_accum"] == 19488
    assert gemm["fp16_semantics"] == "ieee_half"
    assert gemm["fp16_accumulation"] == "fp16"
    assert gemm["fp16_rounding"] == "rne"
    assert gemm["fp16_subnormals"] == "preserve"


if __name__ == "__main__":
    test_perf_gemm_fp16_expected_fields_raw_placeholder()
    test_perf_gemm_fp16_ieee_half_expected_fields()
