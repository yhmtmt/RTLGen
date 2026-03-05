#!/usr/bin/env python3
"""Regression tests for mapper-side large-model split lowering."""

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml  # type: ignore


REPO_ROOT = Path(__file__).resolve().parents[1]
ARCH_PATH = REPO_ROOT / "npu/arch/examples/minimal.yml"


def load_script_module(name: str, relative_path: str):
    module_path = REPO_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Failed to load module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    # Required for dataclass type-resolution during dynamic loading.
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class MapperSplitRegressionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.onnx_lite = load_script_module("onnx_lite", "npu/mapper/onnx_lite.py")

    def _write_mlp_onnx(
        self,
        out_path: Path,
        *,
        name: str,
        b: int,
        in_dim: int,
        hidden_dim: int,
        out_dim: int,
    ) -> None:
        out_path.write_bytes(
            self.onnx_lite.build_mlp_model_bytes(
                name=name,
                b=b,
                in_dim=in_dim,
                hidden_dim=hidden_dim,
                out_dim=out_dim,
                dtype=self.onnx_lite.TENSOR_INT8,
            )
        )

    def _run_lowering(self, onnx_path: Path, sched_path: Path) -> dict:
        cmd = [
            sys.executable,
            str(REPO_ROOT / "npu/mapper/onnx_to_schedule.py"),
            "--onnx",
            str(onnx_path),
            "--arch",
            str(ARCH_PATH),
            "--out",
            str(sched_path),
        ]
        subprocess.run(cmd, cwd=str(REPO_ROOT), check=True, capture_output=True, text=True)
        with sched_path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _validate_and_emit_bin(self, sched_path: Path, bin_path: Path) -> None:
        subprocess.run(
            [sys.executable, str(REPO_ROOT / "npu/mapper/validate.py"), str(sched_path)],
            cwd=str(REPO_ROOT),
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            [
                sys.executable,
                str(REPO_ROOT / "npu/mapper/run.py"),
                str(sched_path),
                "--out-bin",
                str(bin_path),
            ],
            cwd=str(REPO_ROOT),
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertTrue(bin_path.exists())
        self.assertGreater(bin_path.stat().st_size, 0)

    def test_no_split_for_fit_case(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            onnx_path = tmp / "fit.onnx"
            sched_path = tmp / "fit.yml"
            bin_path = tmp / "fit.bin"

            self._write_mlp_onnx(
                onnx_path,
                name="fit",
                b=16,
                in_dim=256,
                hidden_dim=512,
                out_dim=256,
            )
            schedule = self._run_lowering(onnx_path, sched_path)
            self._validate_and_emit_bin(sched_path, bin_path)

            notes = schedule.get("mapper_notes", {})
            self.assertFalse(bool(notes.get("gemm2_split_enabled")))
            self.assertEqual([256], notes.get("gemm2_out_chunks"))

            gemm2_ops = [op for op in schedule["ops"] if str(op.get("id", "")).startswith("gemm2")]
            self.assertEqual(1, len(gemm2_ops))
            self.assertEqual("gemm2", gemm2_ops[0]["id"])
            self.assertEqual(256, int(gemm2_ops[0]["n"]))

    def test_split_for_oversized_case(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            onnx_path = tmp / "split.onnx"
            sched_path = tmp / "split.yml"
            bin_path = tmp / "split.bin"

            out_dim = 4096
            self._write_mlp_onnx(
                onnx_path,
                name="split",
                b=32,
                in_dim=512,
                hidden_dim=2048,
                out_dim=out_dim,
            )
            schedule = self._run_lowering(onnx_path, sched_path)
            self._validate_and_emit_bin(sched_path, bin_path)

            notes = schedule.get("mapper_notes", {})
            self.assertTrue(bool(notes.get("gemm2_split_enabled")))
            chunk_sizes = list(notes.get("gemm2_out_chunks", []))
            self.assertGreater(len(chunk_sizes), 1)
            self.assertEqual(out_dim, sum(int(n) for n in chunk_sizes))

            gemm2_ops = [op for op in schedule["ops"] if str(op.get("id", "")).startswith("gemm2_c")]
            self.assertEqual(len(chunk_sizes), len(gemm2_ops))
            self.assertEqual(chunk_sizes, [int(op["n"]) for op in gemm2_ops])

            # Check event completion tracks the final chunk output DMA.
            last_idx = len(chunk_sizes) - 1
            self.assertEqual(
                f"dma_y_c{last_idx}",
                schedule["events"][0]["signal_on"],
            )

            deps = {dep["then"]: dep["wait"] for dep in schedule.get("deps", [])}
            self.assertIn("gemm2_c0", deps)
            self.assertIn("gemm1", deps["gemm2_c0"])
            self.assertIn("dma_w2_c0", deps["gemm2_c0"])
            self.assertIn("dma_b2_c0", deps["gemm2_c0"])

            if len(chunk_sizes) > 1:
                self.assertIn("dma_w2_c1", deps)
                self.assertIn("dma_y_c0", deps["dma_w2_c1"])


if __name__ == "__main__":
    unittest.main()
