#!/usr/bin/env python3
"""Regression tests for dedicated NPU SOFTMAX RTL generation."""

import json
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BASE_CFG = REPO_ROOT / "runs/designs/npu_blocks/npu_fp16_cpp_nm1_cmp/config_nm1.json"
RTLGEN_BIN = REPO_ROOT / "build/rtlgen"
FALLBACK_RTLGEN_BIN = Path("/workspaces/RTLGen/build/rtlgen")


class NpuRtlgenSoftmaxRegressionTest(unittest.TestCase):
    def _write_softmax_config(self, cfg_path: Path, *, pipeline: int = 3, base_cfg: Path = BASE_CFG) -> None:
        cfg = json.loads(base_cfg.read_text(encoding="utf-8"))
        if base_cfg == BASE_CFG:
            gemm_cpp = cfg.setdefault("compute", {}).setdefault("gemm", {}).setdefault("rtlgen_cpp", {})
            if RTLGEN_BIN.exists():
                gemm_cpp["binary_path"] = str(RTLGEN_BIN)
            else:
                gemm_cpp["binary_path"] = str(FALLBACK_RTLGEN_BIN)
        cfg.setdefault("compute", {})["softmax"] = {
            "enabled": True,
            "dtype": "int8",
            "row_bytes": 4,
            "module_name": "softmax_rowwise_int8_r4_wrapper",
            "accum_bits": 16,
            "max_shift": 7,
            "pipeline": pipeline,
        }
        cfg_path.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")

    def test_generates_dedicated_softmax_wrapper_and_opcode_path(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cfg_path = root / "cfg.json"
            out_dir = root / "out"

            self._write_softmax_config(cfg_path, pipeline=3)

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
            self.assertIn("reg [31:0] y_pipe_0;", top_v)
            self.assertIn("reg [31:0] y_pipe_2;", top_v)
            self.assertIn("assign Y = y_pipe_2;", top_v)

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

    def test_tb_emits_dedicated_softmax_tensor_trace(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cfg_path = root / "cfg.json"
            desc_path = root / "softmax.bin"
            self._write_softmax_config(cfg_path, pipeline=1, base_cfg=REPO_ROOT / "npu/rtlgen/examples/minimal.json")

            desc = bytearray(32)
            struct.pack_into("<BBBBI", desc, 0, 0x12, 0x00, 0x01, 0x00, 0)
            struct.pack_into("<I", desc, 8, 0)
            struct.pack_into("<HH", desc, 24, 4, 2)
            desc_path.write_bytes(desc)

            proc = subprocess.run(
                [
                    "make",
                    "-f",
                    "npu/sim/rtl/Makefile",
                    "run",
                    f"CONFIG={cfg_path}",
                    f"BIN={desc_path}",
                    "BYTES=32",
                    "VVPFLAGS=+event_test=1",
                ],
                cwd=str(REPO_ROOT),
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(0, proc.returncode, proc.stderr + proc.stdout)
        self.assertIn("SOFTMAX_DONE index=1 offset=0 row_bytes=4 rows=2", proc.stdout)
        self.assertIn(
            "TENSOR_TRACE name=softmax.result step=1 shape=2,4 dtype=u8_q0_7 bytes_hex=0x2020202020202020",
            proc.stdout,
        )


if __name__ == "__main__":
    unittest.main()
