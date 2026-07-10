import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from npu.eval.probe_attention_two_pass_stream_equivalence import build_report
from npu.rtlgen.gen_attention_two_pass_stream import generate


def _config(div_lanes: int = 2) -> dict:
    return {
        "top_name": f"attention_two_pass_stream_d{div_lanes}",
        "attention_two_pass_stream": {"max_blocks": 16384, "div_lanes_per_cycle": div_lanes},
    }


def test_attention_two_pass_stream_generator_has_external_memory_ports(tmp_path: Path) -> None:
    config = _config()
    generate(config, tmp_path)

    manifest = json.loads((tmp_path / "attention_two_pass_stream_manifest.json").read_text())
    text = (tmp_path / "top.v").read_text()
    assert manifest["max_context_tokens"] == 131072
    assert manifest["score_storage"] == "external_ready_valid_sram"
    assert manifest["div_lanes_per_cycle"] == 2
    assert "score_write_valid" in text
    assert "score_read_req_valid" in text
    assert "score_mem" not in text


def test_attention_two_pass_stream_generator_compiles(tmp_path: Path) -> None:
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


def test_attention_two_pass_stream_guard_accepts_generated_design(tmp_path: Path) -> None:
    config = _config()
    (tmp_path / "config.json").write_text(json.dumps(config), encoding="utf-8")
    generate(config, tmp_path / "verilog")
    subprocess.run(
        [sys.executable, "npu/eval/check_attention_two_pass_stream_guard.py", "--design-dir", str(tmp_path)],
        check=True,
        capture_output=True,
        text=True,
    )


def test_attention_two_pass_stream_perf_rtl_equivalence() -> None:
    report = build_report(block_counts=[4, 8], div_lanes=[1, 2, 4, 8])

    assert report["decision"] == "attention_two_pass_stream_equivalence_pass"
    assert report["equivalence_pass"] is True
    assert len(report["rows"]) == 24
    assert all(row["equivalence_pass"] for row in report["rows"])
