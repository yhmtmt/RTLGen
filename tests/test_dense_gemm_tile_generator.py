import json
import subprocess
import sys
from pathlib import Path


def test_dense_gemm_tile_generator_supports_int8(tmp_path: Path) -> None:
    design_dir = tmp_path / "npu_dense_gemm_tile_int8_2x3_k1_p1"
    config_path = design_dir / "config.json"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        json.dumps(
            {
                "top_name": "dense_gemm_tile_int8_2x3_k1_p1",
                "dense_gemm_tile": {
                    "module_name": "dense_gemm_tile_int8_2x3_k1_p1",
                    "precision": "int8",
                    "mac_module_name": "int8_mac_s8s8_acc24",
                    "array_m": 2,
                    "array_n": 3,
                    "k_unroll": 1,
                    "pipeline_stages": 1,
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )

    subprocess.run(
        [
            sys.executable,
            "npu/rtlgen/gen_dense_gemm_tile.py",
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
            "npu/eval/check_dense_gemm_tile_guard.py",
            "--design-dir",
            str(design_dir),
        ],
        check=True,
    )

    manifest = json.loads((design_dir / "verilog" / "dense_gemm_tile_manifest.json").read_text())
    top_text = (design_dir / "verilog" / "top.v").read_text(encoding="utf-8")
    assert manifest["precision"] == "int8"
    assert manifest["operand_bits"] == 8
    assert manifest["accum_bits"] == 24
    assert manifest["macs_per_cycle"] == 6
    assert "module int8_mac_s8s8_acc24" in top_text
    assert "assign R = {{8{product[15]}}, product} + C;" in top_text
