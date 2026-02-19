import json
import struct
import subprocess
import tempfile
from pathlib import Path


def _pack_gemm_desc(path: Path):
    raw = bytearray(32)
    # opcode=GEMM, flags=0, size_units=1, reserved=0
    struct.pack_into("<BBBBI", raw, 0, 0x10, 0x00, 0x01, 0x00, 0x00100401)
    # A lanes (raw16): [1, -2, 3, -4]
    struct.pack_into("<hhhh", raw, 8, 1, -2, 3, -4)
    # B lanes (raw16): [5, 6, -7, -8]
    struct.pack_into("<hhhh", raw, 16, 5, 6, -7, -8)
    path.write_bytes(bytes(raw))


def test_perf_gemm_fp16_expected_fields():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        bin_path = tmp / "gemm_fp16.bin"
        out_path = tmp / "trace.json"
        cfg_path = tmp / "cfg.json"
        _pack_gemm_desc(bin_path)
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


def test_perf_gemm_fp16_rejects_unimplemented_ieee_semantics():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        bin_path = tmp / "gemm_fp16.bin"
        out_path = tmp / "trace.json"
        cfg_path = tmp / "cfg.json"
        _pack_gemm_desc(bin_path)
        cfg_path.write_text(
            json.dumps(
                {
                    "gemm_mac_type": "fp16",
                    "gemm_mac_lanes": 4,
                    "gemm_fp16_semantics": "ieee_half",
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        proc = subprocess.run(
            [
                "python3",
                "npu/sim/perf/run.py",
                "--bin",
                str(bin_path),
                "--out",
                str(out_path),
                "--config",
                str(cfg_path),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
    assert proc.returncode != 0
    combined = (proc.stdout or "") + (proc.stderr or "")
    assert "ieee_half is planned but not implemented yet" in combined


if __name__ == "__main__":
    test_perf_gemm_fp16_expected_fields()
