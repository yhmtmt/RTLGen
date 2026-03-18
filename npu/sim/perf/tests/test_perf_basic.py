import json
import struct
import subprocess
import tempfile
from pathlib import Path


def run_perf(tmpdir):
    out_path = Path(tmpdir) / "trace.json"
    cmd = [
        "python3",
        "npu/sim/perf/run.py",
        "--bin",
        "npu/mapper/examples/minimal_descriptors.bin",
        "--out",
        str(out_path),
        "--config",
        "npu/sim/perf/example_config.json",
        "--overlap",
    ]
    subprocess.check_call(cmd)
    return json.loads(out_path.read_text(encoding="utf-8"))


def _encode_gemm_tag(m: int, n: int, k: int) -> int:
    return ((int(m) & 0xFFF) << 20) | ((int(n) & 0x3FF) << 10) | (int(k) & 0x3FF)


def _pack_desc(opcode, flags=0, size_units=1, tag=0):
    raw = bytearray(32 * size_units)
    struct.pack_into("<BBBBI", raw, 0, opcode & 0xFF, flags & 0xFF, size_units & 0xFF, 0, tag & 0xFFFFFFFF)
    return raw


def _write_two_gemm_stream(path: Path, *, m: int, n: int, k: int) -> None:
    raw = bytearray()
    tag = _encode_gemm_tag(m, n, k)
    for _ in range(2):
        desc = bytearray(32)
        struct.pack_into("<BBBBIQQQ", desc, 0, 0x10, 0x00, 0x01, 0x00, tag, 0, 0, 0)
        raw.extend(desc)
    path.write_bytes(bytes(raw))


def _write_event_order_stream(path: Path) -> None:
    raw = bytearray()

    gemm = _pack_desc(0x10, tag=_encode_gemm_tag(256, 256, 256))
    struct.pack_into("<QQQ", gemm, 8, 0x1000, 0x2000, 0x3000)
    raw.extend(gemm)

    raw.extend(_pack_desc(0x20, tag=1))
    raw.extend(_pack_desc(0x21, tag=1))

    dma = _pack_desc(0x01)
    struct.pack_into("<QQI", dma, 8, 0x4000, 0x5000, 1024)
    raw.extend(dma)

    path.write_bytes(bytes(raw))


def test_perf_basic():
    with tempfile.TemporaryDirectory() as tmpdir:
        data = run_perf(tmpdir)
    stats = data["stats"]
    assert stats["dma_ops"] == 1
    assert stats["gemm_ops"] == 1
    assert stats["vec_ops"] == 0
    assert stats["softmax_ops"] == 0
    assert stats["event_ops"] == 3
    assert stats["unknown_ops"] == 0
    assert stats["total_bytes"] == 8192
    assert stats["total_time_ns"] >= max(stats["dma_time_ns"], stats["gemm_time_ns"])
    assert stats["total_time_ns"] <= (stats["dma_time_ns"] + stats["gemm_time_ns"] + stats["event_time_ns"])
    assert data["meta"]["mode"] == "overlap"
    gemm_events = [ev for ev in data["trace"] if ev.get("name") == "GEMM"]
    assert len(gemm_events) == 1
    gemm = gemm_events[0]
    assert "expected_dot" in gemm
    assert "expected_cycles" in gemm
    assert "expected_accum" in gemm
    assert "lanes" in gemm
    assert isinstance(gemm["expected_accum"], int)
    assert 1 <= int(gemm["lanes"]) <= 8


def test_perf_overlap_uses_multiple_gemm_engines():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        bin_path = tmp / "two_gemm.bin"
        out1 = tmp / "trace1.json"
        out2 = tmp / "trace2.json"
        cfg_path = tmp / "cfg.json"
        _write_two_gemm_stream(bin_path, m=64, n=64, k=64)
        cfg_path.write_text(json.dumps({"gemm_tops": 1.0}, indent=2), encoding="utf-8")

        subprocess.check_call(
            [
                "python3",
                "npu/sim/perf/run.py",
                "--bin",
                str(bin_path),
                "--out",
                str(out1),
                "--config",
                str(cfg_path),
                "--overlap",
                "--gemm-engine-count",
                "1",
            ]
        )
        subprocess.check_call(
            [
                "python3",
                "npu/sim/perf/run.py",
                "--bin",
                str(bin_path),
                "--out",
                str(out2),
                "--config",
                str(cfg_path),
                "--overlap",
                "--gemm-engine-count",
                "2",
            ]
        )
        one = json.loads(out1.read_text(encoding="utf-8"))
        two = json.loads(out2.read_text(encoding="utf-8"))

    assert one["stats"]["gemm_ops"] == 2
    assert two["stats"]["gemm_ops"] == 2
    assert int(two["stats"]["gemm_engine_count"]) == 2
    assert float(two["stats"]["total_time_ns"]) < float(one["stats"]["total_time_ns"])
    assert float(two["stats"]["total_time_ns"]) <= float(one["stats"]["gemm_time_ns"]) / 2.0 + 1e-9


def test_perf_event_signal_waits_for_producer_completion_in_overlap_mode():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        bin_path = tmp / "event_order.bin"
        out_path = tmp / "trace.json"
        cfg_path = tmp / "cfg.json"
        _write_event_order_stream(bin_path)
        cfg_path.write_text(
            json.dumps(
                {
                    "gemm_tops": 1.0,
                    "dma_bw_gbps": 16.0,
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
                "--overlap",
            ]
        )
        data = json.loads(out_path.read_text(encoding="utf-8"))

    trace = data["trace"]
    assert [ev["name"] for ev in trace] == ["GEMM", "EVENT_SIGNAL", "EVENT_WAIT", "DMA_COPY"]
    gemm, signal, wait, dma = trace
    assert float(signal["start_ns"]) >= float(gemm["end_ns"])
    assert float(wait["start_ns"]) >= float(signal["end_ns"])
    assert float(dma["start_ns"]) >= float(gemm["end_ns"])


if __name__ == "__main__":
    test_perf_basic()
    test_perf_overlap_uses_multiple_gemm_engines()
    test_perf_event_signal_waits_for_producer_completion_in_overlap_mode()
