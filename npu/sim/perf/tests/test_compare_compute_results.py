import json
import subprocess
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]


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
            cwd=str(REPO_ROOT),
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
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )

    assert proc.returncode == 1
    assert "FAIL canonical summary hash mismatch" in proc.stderr
    assert "FAIL GEMM[offset=32]" in proc.stderr


def test_compare_compute_results_uses_tensor_trace_lanes_for_rtl_vec():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        rtl_log = tmp / "rtl.log"
        perf_trace = tmp / "perf.json"
        rtl_log.write_text(
            """[1] GEMM_TIMING offset=32 cycles=12 accum=123
[2] VEC_DONE index=1 offset=64 op=0 result=0x0000000000000000
TENSOR_TRACE name=vec.result step=1 lanes=1 dtype=packed_u8 result=0x0000000000000000
""",
            encoding="utf-8",
        )
        _write_perf_trace(perf_trace, gemm_accum=123, vec_result="0x00", lanes=1)

        proc = subprocess.run(
            [
                "python3",
                "npu/sim/perf/compare_compute_results.py",
                "--rtl-log",
                str(rtl_log),
                "--perf-trace",
                str(perf_trace),
            ],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )

    assert proc.returncode == 0, proc.stderr
    assert "compare-compute: OK" in proc.stdout
    assert "lanes=1" in proc.stdout


def test_compare_tensor_traces_hash_match():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        rtl_log = tmp / "rtl.log"
        perf_trace = tmp / "perf.json"
        rtl_summary = tmp / "rtl_tensor.json"
        perf_summary = tmp / "perf_tensor.json"
        rtl_log.write_text(
            """TENSOR_TRACE name=gemm.accum step=1 shape=1 dtype=int32 min=123 max=123 mean=123 std=0
TENSOR_TRACE name=vec.result step=1 lanes=8 dtype=packed_u8 result=0x00000000000000ff
""",
            encoding="utf-8",
        )
        _write_perf_trace(perf_trace, gemm_accum=123, vec_result="0x00000000000000ff")

        proc = subprocess.run(
            [
                "python3",
                "npu/sim/perf/compare_tensor_traces.py",
                "--rtl-log",
                str(rtl_log),
                "--perf-trace",
                str(perf_trace),
                "--rtl-summary-out",
                str(rtl_summary),
                "--perf-summary-out",
                str(perf_summary),
            ],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        rtl_doc = json.loads(rtl_summary.read_text(encoding="utf-8"))
        perf_doc = json.loads(perf_summary.read_text(encoding="utf-8"))

    assert proc.returncode == 0, proc.stderr
    assert "compare-tensor-trace: OK" in proc.stdout
    assert "rtl_tensor_trace_sha256=" in proc.stdout
    assert "perf_tensor_trace_sha256=" in proc.stdout
    assert rtl_doc == perf_doc


def test_compare_tensor_traces_hash_mismatch():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        rtl_log = tmp / "rtl.log"
        perf_trace = tmp / "perf.json"
        rtl_log.write_text(
            """TENSOR_TRACE name=gemm.accum step=1 shape=1 dtype=int32 min=123 max=123 mean=123 std=0
TENSOR_TRACE name=vec.result step=1 lanes=8 dtype=packed_u8 result=0x00000000000000ff
""",
            encoding="utf-8",
        )
        _write_perf_trace(perf_trace, gemm_accum=123, vec_result="0x0000000000000001")

        proc = subprocess.run(
            [
                "python3",
                "npu/sim/perf/compare_tensor_traces.py",
                "--rtl-log",
                str(rtl_log),
                "--perf-trace",
                str(perf_trace),
            ],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )

    assert proc.returncode == 1
    assert "FAIL canonical tensor trace hash mismatch" in proc.stderr


def test_compare_tensor_traces_matches_ooo_gemm_by_descriptor_step():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        rtl_log = tmp / "rtl.log"
        perf_trace = tmp / "perf.json"
        rtl_log.write_text(
            """TENSOR_TRACE name=gemm.accum step=2 shape=1 dtype=int32 min=7680 max=7680 mean=7680 std=0
TENSOR_TRACE name=gemm.accum step=1 shape=1 dtype=int32 min=6656 max=6656 mean=6656 std=0
""",
            encoding="utf-8",
        )
        perf_trace.write_text(
            json.dumps(
                {
                    "trace": [
                        {"name": "GEMM", "offset": 128, "expected_accum": 6656},
                        {"name": "GEMM", "offset": 224, "expected_accum": 7680},
                    ]
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        proc = subprocess.run(
            [
                "python3",
                "npu/sim/perf/compare_tensor_traces.py",
                "--rtl-log",
                str(rtl_log),
                "--perf-trace",
                str(perf_trace),
            ],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )

    assert proc.returncode == 0, proc.stderr
    assert "compare-tensor-trace: OK" in proc.stdout


def test_compare_tensor_traces_includes_semantic_softmax_vec_summary():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        rtl_log = tmp / "rtl.log"
        perf_trace = tmp / "perf.json"
        rtl_summary = tmp / "rtl_tensor.json"
        perf_summary = tmp / "perf_tensor.json"
        rtl_log.write_text(
            """TENSOR_TRACE name=vec.result step=1 lanes=1 dtype=packed_u8 result=0x000000000000007f
TENSOR_TRACE name=vec.softmax step=1 lanes=1 dtype=packed_u8 result=0x000000000000007f
TENSOR_TRACE name=vec.result step=2 lanes=1 dtype=packed_u8 result=0x00000000000000fc
TENSOR_TRACE name=vec.layernorm step=2 lanes=1 dtype=packed_u8 result=0x00000000000000fc
""",
            encoding="utf-8",
        )
        perf_trace.write_text(
            json.dumps(
                {
                    "trace": [
                        {
                            "name": "VEC_OP",
                            "op": "softmax",
                            "offset": 256,
                            "lanes": 1,
                            "expected_result": "0x7f",
                        },
                        {
                            "name": "VEC_OP",
                            "op": "layernorm",
                            "offset": 512,
                            "lanes": 1,
                            "expected_result": "0xfc",
                        },
                    ]
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        proc = subprocess.run(
            [
                "python3",
                "npu/sim/perf/compare_tensor_traces.py",
                "--rtl-log",
                str(rtl_log),
                "--perf-trace",
                str(perf_trace),
                "--rtl-summary-out",
                str(rtl_summary),
                "--perf-summary-out",
                str(perf_summary),
            ],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        rtl_doc = json.loads(rtl_summary.read_text(encoding="utf-8"))
        perf_doc = json.loads(perf_summary.read_text(encoding="utf-8"))

    assert proc.returncode == 0, proc.stderr
    assert "compare-tensor-trace: OK" in proc.stdout
    assert rtl_doc == perf_doc
    assert [entry["name"] for entry in perf_doc] == [
        "vec.result",
        "vec.softmax",
        "vec.layernorm",
        "vec.result",
    ]
