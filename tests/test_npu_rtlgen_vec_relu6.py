#!/usr/bin/env python3
"""Regression tests for integrated nm1 ReLU6 vec-op RTL generation."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RELU6_CFG = (
    REPO_ROOT
    / "runs/designs/npu_blocks/npu_fp16_cpp_nm1_relu6cmp/config_nm1_relu6.json"
)
RTLGEN_BIN = REPO_ROOT / "build/rtlgen"
FALLBACK_RTLGEN_BIN = Path("/workspaces/RTLGen/build/rtlgen")


class NpuRtlgenVecReLU6RegressionTest(unittest.TestCase):
    def test_generates_relu6_enabled_nm1_top_and_runs_vec_smoke(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cfg_path = root / "cfg.json"
            out_dir = root / "npu" / "rtlgen" / "out"
            vvp_path = root / "npu_top.vvp"
            cfg = json.loads(RELU6_CFG.read_text(encoding="utf-8"))
            gemm_cpp = cfg.setdefault("compute", {}).setdefault("gemm", {}).setdefault("rtlgen_cpp", {})
            vec_cpp = cfg.setdefault("compute", {}).setdefault("vec", {}).setdefault("rtlgen_cpp", {})
            if RTLGEN_BIN.exists():
                gemm_cpp["binary_path"] = str(RTLGEN_BIN)
                vec_cpp["binary_path"] = str(RTLGEN_BIN)
            else:
                gemm_cpp["binary_path"] = str(FALLBACK_RTLGEN_BIN)
                vec_cpp["binary_path"] = str(FALLBACK_RTLGEN_BIN)
            cfg_path.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")

            subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / "npu/rtlgen/gen.py"),
                    "--config",
                    str(cfg_path),
                    "--out",
                    str(out_dir),
                ],
                cwd=str(REPO_ROOT),
                check=True,
            )

            top_v = (out_dir / "top.v").read_text(encoding="utf-8")
            self.assertIn("vec_act_relu6_int8", top_v)

            subprocess.run(
                [
                    "iverilog",
                    "-g2012",
                    "-I",
                    str(out_dir),
                    "-o",
                    str(vvp_path),
                    str(out_dir / "top.v"),
                    str(out_dir / "top_axi.v"),
                    str(out_dir / "axi_lite_mmio_bridge.sv"),
                    str(out_dir / "sram_models.sv"),
                ],
                cwd=str(root),
                check=True,
            )


if __name__ == "__main__":
    unittest.main()
