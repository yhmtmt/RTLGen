import json
import struct
import subprocess
import tempfile
from pathlib import Path


def _pack_desc(opcode, flags=0, size_units=1, tag=0):
    raw = bytearray(32 * size_units)
    struct.pack_into("<BBBBI", raw, 0, opcode & 0xFF, flags & 0xFF, size_units & 0xFF, 0, tag & 0xFFFFFFFF)
    return raw


def _build_vec_softmax_bin(path: Path):
    stream = bytearray()

    # VEC_OP add, dtype int8
    d0 = _pack_desc(0x11, flags=0x01)
    struct.pack_into("<QQI", d0, 8, 0x1000, 0x2000, 1024)
    stream.extend(d0)

    # VEC_OP dsoftmax, dtype int8
    d1 = _pack_desc(0x11, flags=0x08)
    struct.pack_into("<QQI", d1, 8, 0x3000, 0x4000, 2048)
    stream.extend(d1)

    # SOFTMAX opcode, flags keep int8 dtype in high nibble (0)
    d2 = _pack_desc(0x12, flags=0x00)
    struct.pack_into("<QQHH", d2, 8, 0x5000, 0x6000, 256, 4)
    stream.extend(d2)

    path.write_bytes(bytes(stream))


def _build_mem_image(path: Path, *, base_addr: int, data_bytes: list[int]) -> None:
    path.write_text(
        json.dumps(
            {
                "segments": [
                    {
                        "base_addr": base_addr,
                        "data_bytes": [int(v) & 0xFF for v in data_bytes],
                    }
                ]
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def _pack_fp16_bytes(values: list[float]) -> list[int]:
    out: list[int] = []
    for value in values:
        bits = struct.unpack("<H", struct.pack("<e", float(value)))[0]
        out.append(bits & 0xFF)
        out.append((bits >> 8) & 0xFF)
    return out


def test_perf_vec_softmax():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        bin_path = tmp / "vec_softmax.bin"
        out_path = tmp / "trace.json"
        cfg_path = tmp / "cfg.json"
        _build_vec_softmax_bin(bin_path)
        cfg_path.write_text(
            json.dumps(
                {
                    "dma_bw_gbps": 16.0,
                    "vec_tops": 1.0,
                    "vec_in_bw_gbps": 10.0,
                    "vec_out_bw_gbps": 5.0,
                    "vec_overhead_ns": 20.0,
                    "softmax_tops": 0.5,
                    "softmax_in_bw_gbps": 8.0,
                    "softmax_out_bw_gbps": 4.0,
                    "softmax_overhead_ns": 30.0,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        cmd = [
            "python3",
            "npu/sim/perf/run.py",
            "--bin",
            str(bin_path),
            "--out",
            str(out_path),
            "--config",
            str(cfg_path),
        ]
        subprocess.check_call(cmd)
        data = json.loads(out_path.read_text(encoding="utf-8"))

    stats = data["stats"]
    assert stats["dma_ops"] == 0
    assert stats["gemm_ops"] == 0
    assert stats["vec_ops"] == 2
    assert stats["softmax_ops"] == 1
    assert stats["event_ops"] == 0
    assert stats["unknown_ops"] == 0
    assert stats["total_bytes"] == (1024 + 2048 + (256 * 4))

    trace = data["trace"]
    assert trace[0]["name"] == "VEC_OP"
    assert trace[0]["op"] == "add"
    assert trace[1]["name"] == "VEC_OP"
    assert trace[1]["op"] == "dsoftmax"
    assert trace[2]["name"] == "SOFTMAX"
    assert trace[0]["duration_ns"] > 0.0
    assert trace[1]["duration_ns"] > 0.0
    assert trace[2]["duration_ns"] > 0.0
    for idx in (0, 1):
        vec_ev = trace[idx]
        assert "expected_result" in vec_ev
        assert "expected_result_bytes" in vec_ev
        assert "lanes" in vec_ev
        assert isinstance(vec_ev["expected_result_bytes"], list)
        assert len(vec_ev["expected_result_bytes"]) == int(vec_ev["lanes"])
        assert int(vec_ev["expected_result"], 0) >= 0


def test_perf_softmax_expected_result_with_mem_image():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        bin_path = tmp / "softmax.bin"
        out_path = tmp / "trace.json"
        mem_path = tmp / "mem.json"

        raw = _pack_desc(0x12, flags=0x00)
        struct.pack_into("<QQHH", raw, 8, 0x5000, 0x6000, 4, 2)
        bin_path.write_bytes(bytes(raw))
        _build_mem_image(
            mem_path,
            base_addr=0x5000,
            data_bytes=[0x00, 0x01, 0x02, 0x03, 0xFC, 0x00, 0x04, 0x08],
        )

        subprocess.check_call(
            [
                "python3",
                "npu/sim/perf/run.py",
                "--bin",
                str(bin_path),
                "--out",
                str(out_path),
                "--mem-json",
                str(mem_path),
            ]
        )
        data = json.loads(out_path.read_text(encoding="utf-8"))

    ev = data["trace"][0]
    assert ev["name"] == "SOFTMAX"
    assert ev["expected_result_encoding"] == "u8_q0_7"
    assert ev["softmax_semantics"] == "rowwise_reference_int8"
    assert len(ev["expected_result_bytes"]) == 8
    assert all(0 <= int(v) <= 127 for v in ev["expected_result_bytes"])
    assert sum(ev["expected_result_bytes"][:4]) in (126, 127, 128)
    assert sum(ev["expected_result_bytes"][4:]) in (126, 127, 128)


def test_perf_softmax_expected_result_fp16_with_mem_image():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        bin_path = tmp / "softmax_fp16.bin"
        out_path = tmp / "trace.json"
        mem_path = tmp / "mem.json"

        raw = _pack_desc(0x12, flags=0x10)
        struct.pack_into("<QQHH", raw, 8, 0x7000, 0x7100, 4, 1)
        bin_path.write_bytes(bytes(raw))
        _build_mem_image(
            mem_path,
            base_addr=0x7000,
            data_bytes=_pack_fp16_bytes([0.0, 1.0]),
        )

        subprocess.check_call(
            [
                "python3",
                "npu/sim/perf/run.py",
                "--bin",
                str(bin_path),
                "--out",
                str(out_path),
                "--mem-json",
                str(mem_path),
            ]
        )
        data = json.loads(out_path.read_text(encoding="utf-8"))

    ev = data["trace"][0]
    assert ev["name"] == "SOFTMAX"
    assert ev["expected_result_encoding"] == "fp16_ieee_half_le"
    assert ev["softmax_semantics"] == "rowwise_reference_fp16"
    assert len(ev["expected_result_bytes"]) == 4
    lo0, hi0, lo1, hi1 = [int(v) & 0xFF for v in ev["expected_result_bytes"]]
    p0 = struct.unpack("<e", struct.pack("<H", (hi0 << 8) | lo0))[0]
    p1 = struct.unpack("<e", struct.pack("<H", (hi1 << 8) | lo1))[0]
    assert abs((p0 + p1) - 1.0) < 0.02
    assert 0.20 < p0 < 0.35
    assert 0.65 < p1 < 0.80


if __name__ == "__main__":
    test_perf_vec_softmax()
    test_perf_softmax_expected_result_with_mem_image()
    test_perf_softmax_expected_result_fp16_with_mem_image()
