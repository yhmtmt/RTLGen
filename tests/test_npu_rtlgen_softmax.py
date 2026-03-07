#!/usr/bin/env python3
"""Regression tests for dedicated NPU SOFTMAX RTL generation."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BASE_CFG = REPO_ROOT / "runs/designs/npu_blocks/npu_fp16_cpp_nm1_cmp/config_nm1.json"


class NpuRtlgenSoftmaxRegressionTest(unittest.TestCase):
    def test_generates_dedicated_softmax_wrapper_and_opcode_path(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cfg_path = root / "cfg.json"
            out_dir = root / "out"

            cfg = json.loads(BASE_CFG.read_text(encoding="utf-8"))
            cfg.setdefault("compute", {})["softmax"] = {
                "enabled": True,
                "dtype": "int8",
                "row_bytes": 4,
                "module_name": "softmax_rowwise_int8_r4_wrapper",
                "accum_bits": 16,
                "max_shift": 7,
            }
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
            self.assertIn("module softmax_rowwise_int8_r4_wrapper(", top_v)
            self.assertIn("u_softmax_engine", top_v)
            self.assertIn("SOFTMAX_DESC_ENABLED = 1", top_v)
            self.assertIn("cq_mem_rdata[7:0] == 8'h12", top_v)

            subprocess.run(
                [
                    "iverilog",
                    "-g2012",
                    "-I",
                    str(out_dir),
                    "-o",
                    str(out_dir / "top.vvp"),
                    str(out_dir / "top.v"),
                    str(out_dir / "top_axi.v"),
                    str(out_dir / "axi_lite_mmio_bridge.sv"),
                    str(out_dir / "sram_models.sv"),
                ],
                cwd=str(REPO_ROOT),
                check=True,
            )


if __name__ == "__main__":
    unittest.main()
