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

    def _write_gemm_mlp_onnx(
        self,
        out_path: Path,
        *,
        name: str,
        b: int,
        input_shape: list[int],
        hidden_dims: list[int],
        out_dim: int,
    ) -> None:
        out_path.write_bytes(
            self.onnx_lite.build_gemm_mlp_model_bytes(
                name=name,
                b=b,
                input_shape=input_shape,
                hidden_dims=hidden_dims,
                out_dim=out_dim,
                dtype=self.onnx_lite.TENSOR_INT8,
            )
        )

    def _write_softmax_classifier_onnx(
        self,
        out_path: Path,
        *,
        name: str,
        b: int,
        input_dim: int,
        out_dim: int,
        add_cast: bool = True,
        add_label_output: bool = True,
    ) -> None:
        out_path.write_bytes(
            self.onnx_lite.build_softmax_classifier_model_bytes(
                name=name,
                b=b,
                input_dim=input_dim,
                out_dim=out_dim,
                dtype=self.onnx_lite.TENSOR_INT8,
                add_cast=add_cast,
                add_label_output=add_label_output,
            )
        )

    def _run_lowering(
        self,
        onnx_path: Path,
        sched_path: Path,
        *,
        gemm_num_modules: int | None = None,
        batch_override: int | None = None,
    ) -> dict:
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
        if gemm_num_modules is not None:
            cmd.extend(["--gemm-num-modules", str(gemm_num_modules)])
        if batch_override is not None:
            cmd.extend(["--batch-override", str(batch_override)])
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

    def test_row_parallel_for_multi_module_fit_case(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            onnx_path = tmp / "row_parallel.onnx"
            sched_path = tmp / "row_parallel.yml"
            bin_path = tmp / "row_parallel.bin"

            self._write_mlp_onnx(
                onnx_path,
                name="row_parallel",
                b=16,
                in_dim=256,
                hidden_dim=512,
                out_dim=256,
            )
            schedule = self._run_lowering(onnx_path, sched_path, gemm_num_modules=2)
            self._validate_and_emit_bin(sched_path, bin_path)

            notes = schedule.get("mapper_notes", {})
            self.assertEqual(2, int(notes.get("gemm_num_modules", 0)))
            self.assertTrue(bool(notes.get("gemm_row_parallel_enabled")))
            self.assertEqual([8, 8], notes.get("gemm_row_chunks"))
            self.assertFalse(bool(notes.get("gemm2_split_enabled")))

            gemm1_ops = [op for op in schedule["ops"] if str(op.get("id", "")).startswith("gemm1_r")]
            gemm2_ops = [op for op in schedule["ops"] if str(op.get("id", "")).startswith("gemm2_r")]
            dma_y_ops = [op for op in schedule["ops"] if str(op.get("id", "")).startswith("dma_y_r")]

            self.assertEqual(2, len(gemm1_ops))
            self.assertEqual([8, 8], [int(op["m"]) for op in gemm1_ops])
            self.assertEqual(2, len(gemm2_ops))
            self.assertEqual([8, 8], [int(op["m"]) for op in gemm2_ops])
            self.assertEqual(2, len(dma_y_ops))

            deps = {dep["then"]: dep["wait"] for dep in schedule.get("deps", [])}
            self.assertIn("gemm2_r0", deps)
            self.assertIn("gemm1_r0", deps["gemm2_r0"])
            self.assertIn("dma_w2", deps["gemm2_r0"])
            self.assertIn("dma_b2", deps["gemm2_r0"])
            self.assertIn("dma_y_r1", deps)
            self.assertIn("dma_y_r0", deps["dma_y_r1"])

    def test_imported_gemm_mlp_flatten_batch_override(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            onnx_path = tmp / "imported.onnx"
            sched_path = tmp / "imported.yml"
            bin_path = tmp / "imported.bin"

            self._write_gemm_mlp_onnx(
                onnx_path,
                name="imported_gemm",
                b=1,
                input_shape=[20, 28, 1],
                hidden_dims=[120, 84],
                out_dim=9,
            )
            schedule = self._run_lowering(
                onnx_path,
                sched_path,
                gemm_num_modules=2,
                batch_override=64,
            )
            self._validate_and_emit_bin(sched_path, bin_path)

            notes = schedule.get("mapper_notes", {})
            self.assertEqual(3, int(notes.get("linear_layer_count", 0)))
            self.assertTrue(bool(notes.get("input_flattened")))
            self.assertEqual(64, int(notes.get("effective_batch", 0)))
            self.assertEqual(2, int(notes.get("gemm_num_modules", 0)))
            self.assertTrue(bool(notes.get("gemm_row_parallel_enabled")))
            self.assertEqual([32, 32], notes.get("gemm_row_chunks"))
            self.assertEqual([9], notes.get("final_linear_out_chunks"))
            self.assertNotIn("gemm2_out_chunks", notes)

            gemm1_ops = [op for op in schedule["ops"] if str(op.get("id", "")).startswith("gemm1_r")]
            gemm2_ops = [op for op in schedule["ops"] if str(op.get("id", "")).startswith("gemm2_r")]
            gemm3_ops = [op for op in schedule["ops"] if str(op.get("id", "")).startswith("gemm3_r")]
            dma_y_ops = [op for op in schedule["ops"] if str(op.get("id", "")).startswith("dma_y3_r")]

            self.assertEqual(2, len(gemm1_ops))
            self.assertEqual(2, len(gemm2_ops))
            self.assertEqual(2, len(gemm3_ops))
            self.assertEqual([32, 32], [int(op["m"]) for op in gemm3_ops])
            self.assertEqual(2, len(dma_y_ops))
            self.assertEqual("dma_y3_r1", schedule["events"][0]["signal_on"])

    def test_softmax_classifier_with_aux_output(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            onnx_path = tmp / "classifier.onnx"
            sched_path = tmp / "classifier.yml"
            bin_path = tmp / "classifier.bin"

            self._write_softmax_classifier_onnx(
                onnx_path,
                name="classifier",
                b=1,
                input_dim=16,
                out_dim=4,
                add_cast=True,
                add_label_output=True,
            )
            schedule = self._run_lowering(
                onnx_path,
                sched_path,
                gemm_num_modules=2,
                batch_override=64,
            )
            self._validate_and_emit_bin(sched_path, bin_path)

            notes = schedule.get("mapper_notes", {})
            self.assertEqual(1, int(notes.get("linear_layer_count", 0)))
            self.assertTrue(bool(notes.get("input_cast_ignored")))
            self.assertFalse(bool(notes.get("input_flattened")))
            self.assertEqual(64, int(notes.get("effective_batch", 0)))
            self.assertTrue(bool(notes.get("terminal_softmax")))
            self.assertEqual("P", notes.get("graph_output_name"))
            self.assertEqual(["Y"], notes.get("ignored_graph_outputs"))
            self.assertEqual([4], notes.get("final_linear_out_chunks"))
            self.assertEqual([32, 32], notes.get("gemm_row_chunks"))

            gemm_ops = [op for op in schedule["ops"] if str(op.get("id", "")).startswith("gemm1_r")]
            softmax_ops = [op for op in schedule["ops"] if op.get("type") == "softmax"]
            dma_y_ops = [op for op in schedule["ops"] if str(op.get("id", "")).startswith("dma_y")]

            self.assertEqual(2, len(gemm_ops))
            self.assertEqual(1, len(softmax_ops))
            self.assertEqual(1, len(dma_y_ops))
            self.assertEqual(4, int(softmax_ops[0]["row_bytes"]))
            self.assertEqual(64, int(softmax_ops[0]["rows"]))
            self.assertEqual("dma_y", schedule["events"][0]["signal_on"])


if __name__ == "__main__":
    unittest.main()
