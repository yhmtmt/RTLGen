import json
import struct
import subprocess
import tempfile
from pathlib import Path


def _pack_desc(opcode, flags=0, size_units=1, tag=0):
    raw = bytearray(32 * size_units)
    struct.pack_into("<BBBBI", raw, 0, opcode & 0xFF, flags & 0xFF, size_units & 0xFF, 0, tag & 0xFFFFFFFF)
    return raw


def test_perf_vec_hardsigmoid():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        bin_path = tmp / "vec_hardsigmoid.bin"
        out_path = tmp / "trace.json"
        cfg_path = tmp / "cfg.json"

        d0 = _pack_desc(0x11, flags=0x0C)
        payload = [0xC0, 0xD0, 0xF0, 0x00, 0x10, 0x30, 0x40, 0x7F]
        for idx, value in enumerate(payload):
            d0[8 + idx] = value
        bin_path.write_bytes(bytes(d0))
        cfg_path.write_text(
            json.dumps(
                {
                    "dma_bw_gbps": 16.0,
                    "vec_tops": 1.0,
                    "vec_in_bw_gbps": 10.0,
                    "vec_out_bw_gbps": 5.0,
                    "vec_overhead_ns": 20.0,
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
    assert trace[0]["name"] == "VEC_OP"
    assert trace[0]["op"] == "hardsigmoid"
    assert trace[0]["expected_result_bytes"] == [0, 0, 5, 8, 11, 16, 16, 16]
    assert int(trace[0]["expected_result"], 0) >= 0


if __name__ == "__main__":
    test_perf_vec_hardsigmoid()
