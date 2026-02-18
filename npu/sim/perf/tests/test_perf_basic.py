import json
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


if __name__ == "__main__":
    test_perf_basic()
