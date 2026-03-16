import json
import subprocess
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_compare_terminal_softmax_quality_passes():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        out_json = tmp / "quality.json"
        out_md = tmp / "quality.md"
        subprocess.check_call(
            [
                "python3",
                str(REPO_ROOT / "npu/eval/compare_terminal_softmax_quality.py"),
                "--onnx",
                str(REPO_ROOT / "runs/model_cache/onnx_imported_softmax_tail_v1/logistic_regression.onnx"),
                "--baseline-arch",
                str(REPO_ROOT / "npu/arch/examples/minimal.yml"),
                "--candidate-arch",
                str(REPO_ROOT / "npu/arch/examples/minimal_softmax_tail_fused.yml"),
                "--perf-config",
                str(REPO_ROOT / "npu/sim/perf/example_config_fp16_cpp.json"),
                "--batch-override",
                "256",
                "--out-json",
                str(out_json),
                "--out-md",
                str(out_md),
            ],
            cwd=str(REPO_ROOT),
        )

        report = json.loads(out_json.read_text(encoding="utf-8"))
        assert report["passed"] is True
        assert report["summary"]["baseline_event_target"] == "dma_y"
        assert report["summary"]["candidate_event_target"] == "softmax1"
        assert report["summary"]["baseline_softmax_dst"] == "ACT_A_SRAM"
        assert report["summary"]["candidate_softmax_dst"] == "Y_DRAM"
        assert report["summary"]["baseline_dma_ops"] == report["summary"]["candidate_dma_ops"] + 1
        assert report["failures"] == []
        assert "status: pass" in out_md.read_text(encoding="utf-8")
