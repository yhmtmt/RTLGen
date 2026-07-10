import json
from pathlib import Path
import subprocess
import sys


def test_attention_separated_cluster_guard_accepts_semantic_rtl(tmp_path: Path) -> None:
    design_dir = tmp_path / "attention_separated_cluster_p4_c1"
    config = {
        "top_name": "attention_separated_cluster_p4_c1",
        "attention_separated_cluster": {
            "producer_count": 4,
            "consumer_count": 1,
            "row_elems": 8,
            "head_dim": 8,
            "value_dim": 8,
            "score_bits": 32,
            "weight_bits": 16,
            "input_frac_bits": 28,
            "exp_bucket_shift": 20,
        },
    }
    design_dir.mkdir()
    (design_dir / "config.json").write_text(json.dumps(config), encoding="utf-8")
    subprocess.run(
        [
            sys.executable,
            "npu/rtlgen/gen_attention_separated_cluster.py",
            "--config",
            str(design_dir / "config.json"),
            "--out",
            str(design_dir / "verilog"),
        ],
        check=True,
    )

    subprocess.run(
        [
            sys.executable,
            "npu/eval/check_attention_separated_cluster_guard.py",
            "--design-dir",
            str(design_dir),
        ],
        check=True,
    )


def test_attention_separated_cluster_guard_rejects_hash_proxy(tmp_path: Path) -> None:
    design_dir = tmp_path / "attention_separated_cluster_p1_c1"
    config = {
        "top_name": "attention_separated_cluster_p1_c1",
        "attention_separated_cluster": {
            "producer_count": 1,
            "consumer_count": 1,
            "row_elems": 8,
            "head_dim": 8,
            "value_dim": 8,
            "score_bits": 32,
            "weight_bits": 16,
            "input_frac_bits": 28,
            "exp_bucket_shift": 20,
        },
    }
    design_dir.mkdir()
    (design_dir / "config.json").write_text(json.dumps(config), encoding="utf-8")
    subprocess.run(
        [
            sys.executable,
            "npu/rtlgen/gen_attention_separated_cluster.py",
            "--config",
            str(design_dir / "config.json"),
            "--out",
            str(design_dir / "verilog"),
        ],
        check=True,
    )
    with (design_dir / "verilog" / "top.v").open("a", encoding="utf-8") as handle:
        handle.write("\n// result_hash proxy\n")

    result = subprocess.run(
        [
            sys.executable,
            "npu/eval/check_attention_separated_cluster_guard.py",
            "--design-dir",
            str(design_dir),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "forbidden proxy token" in result.stderr
