import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from npu.eval.probe_attention_two_pass_equivalence import build_report
from npu.rtlgen.gen_attention_two_pass import generate


def _config(block_count: int = 4) -> dict:
    return {
        "top_name": f"attention_two_pass_b{block_count}",
        "attention_two_pass": {
            "block_count": block_count,
            "row_elems": 8,
            "head_dim": 8,
            "value_dim": 8,
            "score_bits": 32,
            "weight_bits": 16,
            "input_frac_bits": 28,
            "exp_bucket_shift": 20,
        },
    }


def test_attention_two_pass_generator_emits_semantic_manifest(tmp_path: Path) -> None:
    config = _config()
    generate(config, tmp_path)

    manifest = json.loads((tmp_path / "attention_two_pass_manifest.json").read_text())
    text = (tmp_path / "top.v").read_text()
    assert manifest["block_count"] == 4
    assert manifest["exp_sum_bits"] == 33
    assert manifest["weighted_numerator_bits"] == 41
    assert "default: exp_lut = 16'd0" in text
    assert "result_weights" not in text


def test_attention_two_pass_generator_compiles(tmp_path: Path) -> None:
    iverilog = shutil.which("iverilog")
    if not iverilog:
        pytest.skip("iverilog unavailable")
    config = _config()
    generate(config, tmp_path)

    subprocess.run(
        [iverilog, "-g2012", "-s", config["top_name"], "-o", str(tmp_path / "simv"), str(tmp_path / "top.v")],
        check=True,
        capture_output=True,
        text=True,
    )


def test_attention_two_pass_perf_rtl_equivalence() -> None:
    report = build_report(block_counts=[4, 8], command_count=3)

    assert report["decision"] == "attention_two_pass_equivalence_pass"
    assert report["equivalence_pass"] is True
    assert len(report["rows"]) == 4
    assert all(row["equivalence_pass"] for row in report["rows"])


def test_attention_two_pass_guard_accepts_generated_design(tmp_path: Path) -> None:
    config = _config()
    (tmp_path / "config.json").write_text(json.dumps(config), encoding="utf-8")
    generate(config, tmp_path / "verilog")

    subprocess.run(
        [
            sys.executable,
            "npu/eval/check_attention_two_pass_guard.py",
            "--design-dir",
            str(tmp_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
