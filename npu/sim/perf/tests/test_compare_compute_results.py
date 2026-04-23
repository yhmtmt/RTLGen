import json
import subprocess
import tempfile
from pathlib import Path


def _write_rtl_log(path: Path, *, gemm_accum: int, vec_result_hex: str) -> None:
    path.write_text(
        """[1] GEMM_TIMING offset=32 cycles=12 accum={gemm_accum}
[2] VEC_DONE offset=64 result={vec_result_hex}
""".format(gemm_accum=gemm_accum, vec_result_hex=vec_result_hex),
        encoding="utf-8",
    )


def _write_perf_trace(path: Path, *, gemm_accum: int, vec_result: str, lanes: int = 8) -> None:
    payload = {
        "trace": [
            {
                "name": "GEMM",
                "offset": 32,
                "expected_accum": gemm_accum,
            },
            {
                "name": "VEC_OP",
                "offset": 64,
                "lanes": lanes,
                "expected_result": vec_result,
            },
        ]
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_compare_compute_results_hash_match():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        rtl_log = tmp / "rtl.log"
        perf_trace = tmp / "perf.json"
        rtl_summary = tmp / "rtl_summary.json"
        perf_summary = tmp / "perf_summary.json"
        _write_rtl_log(rtl_log, gemm_accum=123, vec_result_hex="0x00000000000000ff")
        _write_perf_trace(perf_trace, gemm_accum=123, vec_result="0x00000000000000ff")

        proc = subprocess.run(
            [
                "python3",
                "npu/sim/perf/compare_compute_results.py",
                "--rtl-log",
                str(rtl_log),
                "--perf-trace",
                str(perf_trace),
                "--rtl-summary-out",
                str(rtl_summary),
                "--perf-summary-out",
                str(perf_summary),
            ],
            cwd="/workspaces/RTLGen",
            capture_output=True,
            text=True,
            check=False,
        )
        rtl_doc = json.loads(rtl_summary.read_text(encoding="utf-8"))
        perf_doc = json.loads(perf_summary.read_text(encoding="utf-8"))

    assert proc.returncode == 0, proc.stderr
    assert "compare-compute: OK" in proc.stdout
    assert "rtl_summary_sha256=" in proc.stdout
    assert "perf_summary_sha256=" in proc.stdout
    assert rtl_doc == perf_doc


def test_compare_compute_results_hash_mismatch():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        rtl_log = tmp / "rtl.log"
        perf_trace = tmp / "perf.json"
        _write_rtl_log(rtl_log, gemm_accum=123, vec_result_hex="0x00000000000000ff")
        _write_perf_trace(perf_trace, gemm_accum=321, vec_result="0x00000000000000ff")

        proc = subprocess.run(
            [
                "python3",
                "npu/sim/perf/compare_compute_results.py",
                "--rtl-log",
                str(rtl_log),
                "--perf-trace",
                str(perf_trace),
            ],
            cwd="/workspaces/RTLGen",
            capture_output=True,
            text=True,
            check=False,
        )

    assert proc.returncode == 1
    assert "FAIL canonical summary hash mismatch" in proc.stderr
    assert "FAIL GEMM[offset=32]" in proc.stderr
