import json
import subprocess
import sys
from pathlib import Path


def test_attention_dual_stream_composed_generator_guard_and_syntax(tmp_path: Path) -> None:
    design_dir = tmp_path / "attention_dual_stream_composed_smoke"
    config_path = design_dir / "config.json"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        json.dumps(
            {
                "top_name": "attention_dual_stream_composed_smoke",
                "attention_dual_stream_composed": {
                    "streams": 2,
                    "array_m": 2,
                    "array_n": 2,
                    "k_unroll": 1,
                    "softmax_row_elems": 4,
                    "softmax_accum_bits": 16,
                    "reciprocal_bits": 10,
                    "value_bits": 6,
                    "value_lanes": 4,
                    "partials": 4,
                    "partials_per_cycle": 2,
                    "stream_buffer_bits": 128,
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    subprocess.run(
        [
            sys.executable,
            "npu/rtlgen/gen_attention_dual_stream_composed.py",
            "--config",
            str(config_path),
            "--out",
            str(design_dir / "verilog"),
        ],
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            "npu/eval/check_attention_dual_stream_composed_guard.py",
            "--design-dir",
            str(design_dir),
        ],
        check=True,
    )
    subprocess.run(
        [
            "/oss-cad-suite/bin/iverilog",
            "-g2012",
            "-o",
            str(design_dir / "simv"),
            str(design_dir / "verilog" / "top.v"),
        ],
        check=True,
    )

    manifest = json.loads((design_dir / "verilog" / "attention_dual_stream_composed_manifest.json").read_text())
    top_text = (design_dir / "verilog" / "top.v").read_text(encoding="utf-8")
    assert manifest["streams"] == 2
    assert manifest["total_macs"] == 8
    assert manifest["softmax_row_elems"] == 4
    assert manifest["value_lanes_per_stream"] == 4
    assert "u_softmax" in top_text
    assert "u_value_stream_0" in top_text
    assert "u_value_stream_1" in top_text
    assert "result_hash <=" in top_text
