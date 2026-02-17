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


if __name__ == "__main__":
    test_perf_vec_softmax()
