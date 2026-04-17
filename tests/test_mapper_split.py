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
ARCH_SOFTMAX_FUSED_PATH = REPO_ROOT / "npu/arch/examples/minimal_softmax_tail_fused.yml"
ARCH_TERMINAL_DIRECT_OUTPUT_PATH = REPO_ROOT / "npu/arch/examples/minimal_terminal_direct_output.yml"
ARCH_TERMINAL_VECOP_DIRECT_OUTPUT_PATH = REPO_ROOT / "npu/arch/examples/minimal_terminal_vecop_direct_output.yml"


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
        final_relu: bool = False,
    ) -> None:
        out_path.write_bytes(
            self.onnx_lite.build_gemm_mlp_model_bytes(
                name=name,
                b=b,
                input_shape=input_shape,
                hidden_dims=hidden_dims,
                out_dim=out_dim,
                dtype=self.onnx_lite.TENSOR_INT8,
                final_relu=final_relu,
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

    def _write_terminal_relu_onnx(
        self,
        out_path: Path,
        *,
        name: str,
        b: int,
        input_shape: list[int],
        add_flatten: bool = False,
        add_cast: bool = False,
    ) -> None:
        out_path.write_bytes(
            self.onnx_lite.build_terminal_relu_model_bytes(
                name=name,
                b=b,
                input_shape=input_shape,
                dtype=self.onnx_lite.TENSOR_INT8,
                add_flatten=add_flatten,
                add_cast=add_cast,
            )
        )

    def _write_terminal_relu6_onnx(
        self,
        out_path: Path,
        *,
        name: str,
        b: int,
        input_shape: list[int],
        add_flatten: bool = False,
        add_cast: bool = False,
    ) -> None:
        out_path.write_bytes(
            self.onnx_lite.build_terminal_relu6_model_bytes(
                name=name,
                b=b,
                input_shape=input_shape,
                dtype=self.onnx_lite.TENSOR_INT8,
                add_flatten=add_flatten,
                add_cast=add_cast,
            )
        )

    def _write_terminal_leakyrelu_onnx(
        self,
        out_path: Path,
        *,
        name: str,
        b: int,
        input_shape: list[int],
        add_flatten: bool = False,
        add_cast: bool = False,
    ) -> None:
        out_path.write_bytes(
            self.onnx_lite.build_terminal_leakyrelu_model_bytes(
                name=name,
                b=b,
                input_shape=input_shape,
                dtype=self.onnx_lite.TENSOR_INT8,
                add_flatten=add_flatten,
                add_cast=add_cast,
            )
        )

    def _write_terminal_sigmoid_onnx(
        self,
        out_path: Path,
        *,
        name: str,
        b: int,
        input_shape: list[int],
        add_flatten: bool = False,
        add_cast: bool = False,
    ) -> None:
        out_path.write_bytes(
            self.onnx_lite.build_terminal_sigmoid_model_bytes(
                name=name,
                b=b,
                input_shape=input_shape,
                dtype=self.onnx_lite.TENSOR_INT8,
                add_flatten=add_flatten,
                add_cast=add_cast,
            )
        )

    def _write_terminal_tanh_onnx(
        self,
        out_path: Path,
        *,
        name: str,
        b: int,
        input_shape: list[int],
        add_flatten: bool = False,
        add_cast: bool = False,
    ) -> None:
        out_path.write_bytes(
            self.onnx_lite.build_terminal_tanh_model_bytes(
                name=name,
                b=b,
                input_shape=input_shape,
                dtype=self.onnx_lite.TENSOR_INT8,
                add_flatten=add_flatten,
                add_cast=add_cast,
            )
        )

    def _write_terminal_hardsigmoid_onnx(
        self,
        out_path: Path,
        *,
        name: str,
        b: int,
        input_shape: list[int],
        add_flatten: bool = False,
        add_cast: bool = False,
    ) -> None:
        out_path.write_bytes(
            self.onnx_lite.build_terminal_hardsigmoid_model_bytes(
                name=name,
                b=b,
                input_shape=input_shape,
                dtype=self.onnx_lite.TENSOR_INT8,
                add_flatten=add_flatten,
                add_cast=add_cast,
            )
        )

    def _write_terminal_hardtanh_onnx(
        self,
        out_path: Path,
        *,
        name: str,
        b: int,
        input_shape: list[int],
        add_flatten: bool = False,
        add_cast: bool = False,
    ) -> None:
        out_path.write_bytes(
            self.onnx_lite.build_terminal_hardtanh_model_bytes(
                name=name,
                b=b,
                input_shape=input_shape,
                dtype=self.onnx_lite.TENSOR_INT8,
                add_flatten=add_flatten,
                add_cast=add_cast,
            )
        )

    def _write_attention_block_onnx(
        self,
        out_path: Path,
        *,
        name: str,
        seq_len: int,
        hidden_dim: int,
        num_blocks: int = 1,
        add_cast: bool = False,
    ) -> None:
        out_path.write_bytes(
            self.onnx_lite.build_attention_block_model_bytes(
                name=name,
                seq_len=seq_len,
                hidden_dim=hidden_dim,
                num_blocks=num_blocks,
                dtype=self.onnx_lite.TENSOR_INT8,
                add_cast=add_cast,
            )
        )

    def _run_lowering(
        self,
        onnx_path: Path,
        sched_path: Path,
        *,
        arch_path: Path | None = None,
        gemm_num_modules: int | None = None,
        batch_override: int | None = None,
        softmax_backend: str | None = None,
    ) -> dict:
        cmd = [
            sys.executable,
            str(REPO_ROOT / "npu/mapper/onnx_to_schedule.py"),
            "--onnx",
            str(onnx_path),
            "--arch",
            str(arch_path or ARCH_PATH),
            "--out",
            str(sched_path),
        ]
        if gemm_num_modules is not None:
            cmd.extend(["--gemm-num-modules", str(gemm_num_modules)])
        if batch_override is not None:
            cmd.extend(["--batch-override", str(batch_override)])
        if softmax_backend is not None:
            cmd.extend(["--softmax-backend", softmax_backend])
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
            self.assertEqual("dedicated", notes.get("softmax_backend"))
            self.assertEqual("P", notes.get("graph_output_name"))
            self.assertEqual(["Y"], notes.get("ignored_graph_outputs"))
            self.assertEqual([4], notes.get("final_linear_out_chunks"))
            self.assertEqual([32, 32], notes.get("gemm_row_chunks"))
            self.assertFalse(bool(notes.get("gemm_row_parallel_enabled")))
            self.assertFalse(bool(notes.get("final_linear_row_parallel_enabled")))
            self.assertEqual([64], notes.get("final_linear_row_chunks"))

            gemm_ops = [op for op in schedule["ops"] if str(op.get("id", "")).startswith("gemm1_r")]
            monolithic_gemm_ops = [op for op in schedule["ops"] if op.get("id") == "gemm1"]
            softmax_ops = [op for op in schedule["ops"] if op.get("type") == "softmax"]
            dma_y_ops = [op for op in schedule["ops"] if str(op.get("id", "")).startswith("dma_y")]

            self.assertEqual(0, len(gemm_ops))
            self.assertEqual(1, len(monolithic_gemm_ops))
            self.assertEqual(64, int(monolithic_gemm_ops[0]["m"]))
            self.assertEqual(1, len(softmax_ops))
            self.assertEqual(1, len(dma_y_ops))
            self.assertEqual(4, int(softmax_ops[0]["row_bytes"]))
            self.assertEqual(64, int(softmax_ops[0]["rows"]))
            self.assertEqual("dma_y", schedule["events"][0]["signal_on"])

    def test_attention_block_generator_emits_nonterminal_softmax(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            onnx_path = tmp / 'attn.onnx'

            self._write_attention_block_onnx(
                onnx_path,
                name='attn_proxy',
                seq_len=32,
                hidden_dim=64,
                num_blocks=2,
                add_cast=False,
            )

            model = self.onnx_lite.load_onnx_model(onnx_path)
            self.assertEqual([32, 64], model.graph.inputs['X'])
            self.assertEqual([32, 64], model.graph.outputs['Y'])

            op_types = [node.op_type for node in model.graph.nodes]
            self.assertEqual(6, len(op_types))
            self.assertEqual(['Gemm', 'Softmax', 'Gemm', 'Gemm', 'Softmax', 'Gemm'], op_types)
            softmax_positions = [idx for idx, op in enumerate(op_types) if op == 'Softmax']
            self.assertEqual([1, 4], softmax_positions)
            self.assertLess(max(softmax_positions), len(op_types) - 1)

            for node in model.graph.nodes:
                if node.op_type == 'Softmax':
                    self.assertTrue(node.outputs[0].startswith('P'))
                if node.op_type == 'Gemm':
                    self.assertTrue(node.name.startswith('ScoreGemm') or node.name.startswith('ValueGemm'))

    def test_attention_block_lowering_emits_intermediate_softmax(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            onnx_path = tmp / 'attn_lower.onnx'
            sched_path = tmp / 'attn_lower.yml'
            bin_path = tmp / 'attn_lower.bin'

            self._write_attention_block_onnx(
                onnx_path,
                name='attn_proxy_lower',
                seq_len=32,
                hidden_dim=64,
                num_blocks=2,
                add_cast=False,
            )
            schedule = self._run_lowering(
                onnx_path,
                sched_path,
                softmax_backend='dedicated',
            )
            self._validate_and_emit_bin(sched_path, bin_path)

            notes = schedule.get('mapper_notes', {})
            self.assertEqual('attention_proxy', notes.get('graph_kind'))
            self.assertEqual(2, int(notes.get('attention_proxy_blocks', 0)))
            self.assertEqual(2, int(notes.get('nonterminal_softmax_count', 0)))
            self.assertEqual(4, int(notes.get('linear_layer_count', 0)))
            self.assertEqual('dedicated', notes.get('softmax_backend'))
            self.assertEqual('Y', notes.get('graph_output_name'))

            gemm_ops = [op for op in schedule['ops'] if op.get('type') == 'gemm']
            softmax_ops = [op for op in schedule['ops'] if op.get('type') == 'softmax']
            dma_y_ops = [op for op in schedule['ops'] if op.get('id') == 'dma_y']

            self.assertEqual(4, len(gemm_ops))
            self.assertEqual(2, len(softmax_ops))
            self.assertEqual(1, len(dma_y_ops))
            self.assertEqual(32, int(softmax_ops[0]['rows']))
            self.assertEqual(32, int(softmax_ops[0]['row_bytes']))
            self.assertEqual('dma_y', schedule['events'][0]['signal_on'])

    def test_softmax_classifier_vec_placeholder_backend(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            onnx_path = tmp / "classifier.onnx"
            sched_path = tmp / "classifier.yml"
            bin_path = tmp / "classifier.bin"

            self._write_softmax_classifier_onnx(
                onnx_path,
                name="classifier_vec_softmax",
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
                softmax_backend="vec_placeholder",
            )
            self._validate_and_emit_bin(sched_path, bin_path)

            notes = schedule.get("mapper_notes", {})
            self.assertTrue(bool(notes.get("terminal_softmax")))
            self.assertEqual("vec_placeholder", notes.get("softmax_backend"))

            softmax_ops = [op for op in schedule["ops"] if op.get("type") == "softmax"]
            vec_softmax_ops = [
                op for op in schedule["ops"] if op.get("type") == "vec_op" and str(op.get("op", "")).lower() == "softmax"
            ]

            self.assertEqual(0, len(softmax_ops))
            self.assertEqual(1, len(vec_softmax_ops))
            self.assertEqual(64 * 4, int(vec_softmax_ops[0]["bytes"]))

    def test_softmax_classifier_direct_output_when_arch_requests_it(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            onnx_path = tmp / "classifier_direct.onnx"
            sched_path = tmp / "classifier_direct.yml"
            bin_path = tmp / "classifier_direct.bin"

            self._write_softmax_classifier_onnx(
                onnx_path,
                name="classifier_direct",
                b=1,
                input_dim=16,
                out_dim=4,
                add_cast=True,
                add_label_output=True,
            )
            cmd = [
                sys.executable,
                str(REPO_ROOT / "npu/mapper/onnx_to_schedule.py"),
                "--onnx",
                str(onnx_path),
                "--arch",
                str(ARCH_SOFTMAX_FUSED_PATH),
                "--out",
                str(sched_path),
                "--gemm-num-modules",
                "2",
                "--batch-override",
                "64",
                "--softmax-backend",
                "dedicated",
            ]
            subprocess.run(cmd, cwd=str(REPO_ROOT), check=True, capture_output=True, text=True)
            self._validate_and_emit_bin(sched_path, bin_path)

            with sched_path.open("r", encoding="utf-8") as f:
                schedule = yaml.safe_load(f)

            notes = schedule.get("mapper_notes", {})
            self.assertTrue(bool(notes.get("terminal_softmax")))
            self.assertEqual("dedicated", notes.get("softmax_backend"))
            self.assertTrue(bool(notes.get("terminal_softmax_direct_output")))
            self.assertFalse(bool(notes.get("final_linear_row_parallel_enabled")))
            self.assertEqual([64], notes.get("final_linear_row_chunks"))

            softmax_ops = [op for op in schedule["ops"] if op.get("type") == "softmax"]
            dma_y_ops = [op for op in schedule["ops"] if str(op.get("id", "")).startswith("dma_y")]
            monolithic_gemm_ops = [op for op in schedule["ops"] if op.get("id") == "gemm1"]
            split_gemm_ops = [op for op in schedule["ops"] if str(op.get("id", "")).startswith("gemm1_r")]

            self.assertEqual(1, len(softmax_ops))
            self.assertEqual("Y_DRAM", softmax_ops[0]["dst"])
            self.assertEqual(0, len(dma_y_ops))
            self.assertEqual(1, len(monolithic_gemm_ops))
            self.assertEqual(0, len(split_gemm_ops))
            self.assertEqual("softmax1", schedule["events"][0]["signal_on"])

    def test_terminal_relu_chain_lowers_without_softmax(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            onnx_path = tmp / "terminal_relu.onnx"
            sched_path = tmp / "terminal_relu.yml"
            bin_path = tmp / "terminal_relu.bin"

            self._write_gemm_mlp_onnx(
                onnx_path,
                name="terminal_relu",
                b=128,
                input_shape=[2, 4],
                hidden_dims=[],
                out_dim=128,
                final_relu=True,
            )
            schedule = self._run_lowering(onnx_path, sched_path)
            self._validate_and_emit_bin(sched_path, bin_path)

            notes = schedule.get("mapper_notes", {})
            self.assertFalse(bool(notes.get("terminal_softmax")))
            self.assertEqual("Y", notes.get("graph_output_name"))

            softmax_ops = [op for op in schedule["ops"] if op.get("type") == "softmax"]
            self.assertEqual([], softmax_ops)

            gemm_ops = [op for op in schedule["ops"] if op.get("type") == "gemm"]
            self.assertEqual(1, len(gemm_ops))
            self.assertEqual("relu", gemm_ops[0].get("epilogue"))

            dma_y_ops = [op for op in schedule["ops"] if str(op.get("id", "")).startswith("dma_y")]
            self.assertEqual(1, len(dma_y_ops))
            self.assertEqual("dma_y1", schedule["events"][0]["signal_on"])

    def test_terminal_linear_direct_output_when_arch_requests_it(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            onnx_path = tmp / "terminal_linear.onnx"
            sched_path = tmp / "terminal_linear.yml"
            bin_path = tmp / "terminal_linear.bin"

            self._write_gemm_mlp_onnx(
                onnx_path,
                name="terminal_linear",
                b=128,
                input_shape=[2, 4],
                hidden_dims=[],
                out_dim=64,
                final_relu=False,
            )
            schedule = self._run_lowering(
                onnx_path,
                sched_path,
                arch_path=ARCH_TERMINAL_DIRECT_OUTPUT_PATH,
            )
            self._validate_and_emit_bin(sched_path, bin_path)

            notes = schedule.get("mapper_notes", {})
            self.assertFalse(bool(notes.get("terminal_softmax")))
            self.assertTrue(bool(notes.get("terminal_direct_output")))
            self.assertFalse(bool(notes.get("final_linear_row_parallel_enabled")))

            gemm_ops = [op for op in schedule["ops"] if op.get("type") == "gemm"]
            self.assertEqual(1, len(gemm_ops))
            self.assertEqual("Y_DRAM", gemm_ops[0].get("c"))
            self.assertEqual("none", gemm_ops[0].get("epilogue"))

            dma_y_ops = [op for op in schedule["ops"] if str(op.get("id", "")).startswith("dma_y")]
            self.assertEqual([], dma_y_ops)
            self.assertEqual("gemm1", schedule["events"][0]["signal_on"])

    def test_terminal_relu_direct_output_when_arch_requests_it(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            onnx_path = tmp / "terminal_relu_direct.onnx"
            sched_path = tmp / "terminal_relu_direct.yml"
            bin_path = tmp / "terminal_relu_direct.bin"

            self._write_gemm_mlp_onnx(
                onnx_path,
                name="terminal_relu_direct",
                b=128,
                input_shape=[2, 4],
                hidden_dims=[],
                out_dim=128,
                final_relu=True,
            )
            schedule = self._run_lowering(
                onnx_path,
                sched_path,
                arch_path=ARCH_TERMINAL_DIRECT_OUTPUT_PATH,
            )
            self._validate_and_emit_bin(sched_path, bin_path)

            notes = schedule.get("mapper_notes", {})
            self.assertFalse(bool(notes.get("terminal_softmax")))
            self.assertTrue(bool(notes.get("terminal_direct_output")))

            gemm_ops = [op for op in schedule["ops"] if op.get("type") == "gemm"]
            self.assertEqual(1, len(gemm_ops))
            self.assertEqual("Y_DRAM", gemm_ops[0].get("c"))
            self.assertEqual("relu", gemm_ops[0].get("epilogue"))

            dma_y_ops = [op for op in schedule["ops"] if str(op.get("id", "")).startswith("dma_y")]
            self.assertEqual([], dma_y_ops)
            self.assertEqual("gemm1", schedule["events"][0]["signal_on"])

    def test_terminal_vecop_relu_lowers_without_direct_output(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            onnx_path = tmp / "terminal_vec_relu.onnx"
            sched_path = tmp / "terminal_vec_relu.yml"
            bin_path = tmp / "terminal_vec_relu.bin"

            self._write_terminal_relu_onnx(
                onnx_path,
                name="terminal_vec_relu",
                b=128,
                input_shape=[64],
            )
            schedule = self._run_lowering(onnx_path, sched_path)
            self._validate_and_emit_bin(sched_path, bin_path)

            notes = schedule.get("mapper_notes", {})
            self.assertEqual("terminal_vec_op", notes.get("graph_kind"))
            self.assertEqual("relu", notes.get("terminal_vec_op"))
            self.assertFalse(bool(notes.get("terminal_vecop_direct_output")))

            vec_ops = [op for op in schedule["ops"] if op.get("type") == "vec_op"]
            dma_y_ops = [op for op in schedule["ops"] if str(op.get("id", "")).startswith("dma_y")]
            self.assertEqual(1, len(vec_ops))
            self.assertEqual("relu", vec_ops[0].get("op"))
            self.assertEqual("ACT_B_SRAM", vec_ops[0].get("dst"))
            self.assertEqual(1, len(dma_y_ops))
            self.assertEqual("ACT_B_SRAM", dma_y_ops[0].get("src"))
            self.assertEqual("Y_DRAM", dma_y_ops[0].get("dst"))
            self.assertEqual("dma_y", schedule["events"][0]["signal_on"])

    def test_terminal_vecop_relu_direct_output_when_arch_requests_it(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            onnx_path = tmp / "terminal_vec_relu_direct.onnx"
            sched_path = tmp / "terminal_vec_relu_direct.yml"
            bin_path = tmp / "terminal_vec_relu_direct.bin"

            self._write_terminal_relu_onnx(
                onnx_path,
                name="terminal_vec_relu_direct",
                b=128,
                input_shape=[2, 4, 8],
                add_flatten=True,
            )
            schedule = self._run_lowering(
                onnx_path,
                sched_path,
                arch_path=ARCH_TERMINAL_VECOP_DIRECT_OUTPUT_PATH,
            )
            self._validate_and_emit_bin(sched_path, bin_path)

            notes = schedule.get("mapper_notes", {})
            self.assertEqual("terminal_vec_op", notes.get("graph_kind"))
            self.assertTrue(bool(notes.get("input_flattened")))
            self.assertTrue(bool(notes.get("terminal_vecop_direct_output")))

            vec_ops = [op for op in schedule["ops"] if op.get("type") == "vec_op"]
            dma_y_ops = [op for op in schedule["ops"] if str(op.get("id", "")).startswith("dma_y")]
            self.assertEqual(1, len(vec_ops))
            self.assertEqual("Y_DRAM", vec_ops[0].get("dst"))
            self.assertEqual([], dma_y_ops)
            self.assertEqual("vec1", schedule["events"][0]["signal_on"])


    def test_terminal_vecop_sigmoid_lowers_without_direct_output(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            onnx_path = tmp / "terminal_vec_sigmoid.onnx"
            sched_path = tmp / "terminal_vec_sigmoid.yml"
            bin_path = tmp / "terminal_vec_sigmoid.bin"

            self._write_terminal_sigmoid_onnx(
                onnx_path,
                name="terminal_vec_sigmoid",
                b=128,
                input_shape=[64],
            )
            schedule = self._run_lowering(onnx_path, sched_path)
            self._validate_and_emit_bin(sched_path, bin_path)

            notes = schedule.get("mapper_notes", {})
            self.assertEqual("terminal_vec_op", notes.get("graph_kind"))
            self.assertEqual("sigmoid", notes.get("terminal_vec_op"))
            self.assertFalse(bool(notes.get("terminal_vecop_direct_output")))

            vec_ops = [op for op in schedule["ops"] if op.get("type") == "vec_op"]
            dma_y_ops = [op for op in schedule["ops"] if str(op.get("id", "")).startswith("dma_y")]
            self.assertEqual(1, len(vec_ops))
            self.assertEqual("sigmoid", vec_ops[0].get("op"))
            self.assertEqual("ACT_B_SRAM", vec_ops[0].get("dst"))
            self.assertEqual(1, len(dma_y_ops))
            self.assertEqual("ACT_B_SRAM", dma_y_ops[0].get("src"))
            self.assertEqual("Y_DRAM", dma_y_ops[0].get("dst"))
            self.assertEqual("dma_y", schedule["events"][0]["signal_on"])

    def test_terminal_vecop_sigmoid_direct_output_when_arch_requests_it(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            onnx_path = tmp / "terminal_vec_sigmoid_direct.onnx"
            sched_path = tmp / "terminal_vec_sigmoid_direct.yml"
            bin_path = tmp / "terminal_vec_sigmoid_direct.bin"

            self._write_terminal_sigmoid_onnx(
                onnx_path,
                name="terminal_vec_sigmoid_direct",
                b=128,
                input_shape=[2, 4, 8],
                add_flatten=True,
            )
            schedule = self._run_lowering(
                onnx_path,
                sched_path,
                arch_path=ARCH_TERMINAL_VECOP_DIRECT_OUTPUT_PATH,
            )
            self._validate_and_emit_bin(sched_path, bin_path)

            notes = schedule.get("mapper_notes", {})
            self.assertEqual("terminal_vec_op", notes.get("graph_kind"))
            self.assertEqual("sigmoid", notes.get("terminal_vec_op"))
            self.assertTrue(bool(notes.get("input_flattened")))
            self.assertTrue(bool(notes.get("terminal_vecop_direct_output")))

            vec_ops = [op for op in schedule["ops"] if op.get("type") == "vec_op"]
            dma_y_ops = [op for op in schedule["ops"] if str(op.get("id", "")).startswith("dma_y")]
            self.assertEqual(1, len(vec_ops))
            self.assertEqual("sigmoid", vec_ops[0].get("op"))
            self.assertEqual("Y_DRAM", vec_ops[0].get("dst"))
            self.assertEqual([], dma_y_ops)
            self.assertEqual("vec1", schedule["events"][0]["signal_on"])


    def test_terminal_vecop_tanh_lowers_without_direct_output(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            onnx_path = tmp / "terminal_vec_tanh.onnx"
            sched_path = tmp / "terminal_vec_tanh.yml"
            bin_path = tmp / "terminal_vec_tanh.bin"

            self._write_terminal_tanh_onnx(
                onnx_path,
                name="terminal_vec_tanh",
                b=128,
                input_shape=[64],
            )
            schedule = self._run_lowering(onnx_path, sched_path)
            self._validate_and_emit_bin(sched_path, bin_path)

            notes = schedule.get("mapper_notes", {})
            self.assertEqual("terminal_vec_op", notes.get("graph_kind"))
            self.assertEqual("tanh", notes.get("terminal_vec_op"))
            self.assertFalse(bool(notes.get("terminal_vecop_direct_output")))

            vec_ops = [op for op in schedule["ops"] if op.get("type") == "vec_op"]
            dma_y_ops = [op for op in schedule["ops"] if str(op.get("id", "")).startswith("dma_y")]
            self.assertEqual(1, len(vec_ops))
            self.assertEqual("tanh", vec_ops[0].get("op"))
            self.assertEqual("ACT_B_SRAM", vec_ops[0].get("dst"))
            self.assertEqual(1, len(dma_y_ops))
            self.assertEqual("ACT_B_SRAM", dma_y_ops[0].get("src"))
            self.assertEqual("Y_DRAM", dma_y_ops[0].get("dst"))
            self.assertEqual("dma_y", schedule["events"][0]["signal_on"])

    def test_terminal_vecop_tanh_direct_output_when_arch_requests_it(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            onnx_path = tmp / "terminal_vec_tanh_direct.onnx"
            sched_path = tmp / "terminal_vec_tanh_direct.yml"
            bin_path = tmp / "terminal_vec_tanh_direct.bin"

            self._write_terminal_tanh_onnx(
                onnx_path,
                name="terminal_vec_tanh_direct",
                b=128,
                input_shape=[2, 4, 8],
                add_flatten=True,
            )
            schedule = self._run_lowering(
                onnx_path,
                sched_path,
                arch_path=ARCH_TERMINAL_VECOP_DIRECT_OUTPUT_PATH,
            )
            self._validate_and_emit_bin(sched_path, bin_path)

            notes = schedule.get("mapper_notes", {})
            self.assertEqual("terminal_vec_op", notes.get("graph_kind"))
            self.assertEqual("tanh", notes.get("terminal_vec_op"))
            self.assertTrue(bool(notes.get("input_flattened")))
            self.assertTrue(bool(notes.get("terminal_vecop_direct_output")))

            vec_ops = [op for op in schedule["ops"] if op.get("type") == "vec_op"]
            dma_y_ops = [op for op in schedule["ops"] if str(op.get("id", "")).startswith("dma_y")]
            self.assertEqual(1, len(vec_ops))
            self.assertEqual("tanh", vec_ops[0].get("op"))
            self.assertEqual("Y_DRAM", vec_ops[0].get("dst"))
            self.assertEqual([], dma_y_ops)
            self.assertEqual("vec1", schedule["events"][0]["signal_on"])


    def test_terminal_vecop_relu6_lowers_without_direct_output(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            onnx_path = tmp / "terminal_vec_relu6.onnx"
            sched_path = tmp / "terminal_vec_relu6.yml"
            bin_path = tmp / "terminal_vec_relu6.bin"

            self._write_terminal_relu6_onnx(
                onnx_path,
                name="terminal_vec_relu6",
                b=128,
                input_shape=[64],
            )
            schedule = self._run_lowering(onnx_path, sched_path)
            self._validate_and_emit_bin(sched_path, bin_path)

            notes = schedule.get("mapper_notes", {})
            self.assertEqual("terminal_vec_op", notes.get("graph_kind"))
            self.assertEqual("relu6", notes.get("terminal_vec_op"))
            self.assertFalse(bool(notes.get("terminal_vecop_direct_output")))

            vec_ops = [op for op in schedule["ops"] if op.get("type") == "vec_op"]
            dma_y_ops = [op for op in schedule["ops"] if str(op.get("id", "")).startswith("dma_y")]
            self.assertEqual(1, len(vec_ops))
            self.assertEqual("relu6", vec_ops[0].get("op"))
            self.assertEqual("ACT_B_SRAM", vec_ops[0].get("dst"))
            self.assertEqual(1, len(dma_y_ops))
            self.assertEqual("ACT_B_SRAM", dma_y_ops[0].get("src"))
            self.assertEqual("Y_DRAM", dma_y_ops[0].get("dst"))

    def test_terminal_vecop_relu6_direct_output_when_arch_requests_it(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            onnx_path = tmp / "terminal_vec_relu6_direct.onnx"
            sched_path = tmp / "terminal_vec_relu6_direct.yml"
            bin_path = tmp / "terminal_vec_relu6_direct.bin"

            self._write_terminal_relu6_onnx(
                onnx_path,
                name="terminal_vec_relu6_direct",
                b=128,
                input_shape=[2, 4, 8],
                add_flatten=True,
            )
            schedule = self._run_lowering(
                onnx_path,
                sched_path,
                arch_path=ARCH_TERMINAL_VECOP_DIRECT_OUTPUT_PATH,
            )
            self._validate_and_emit_bin(sched_path, bin_path)

            notes = schedule.get("mapper_notes", {})
            self.assertEqual("terminal_vec_op", notes.get("graph_kind"))
            self.assertEqual("relu6", notes.get("terminal_vec_op"))
            self.assertTrue(bool(notes.get("input_flattened")))
            self.assertTrue(bool(notes.get("terminal_vecop_direct_output")))

            vec_ops = [op for op in schedule["ops"] if op.get("type") == "vec_op"]
            dma_y_ops = [op for op in schedule["ops"] if str(op.get("id", "")).startswith("dma_y")]
            self.assertEqual(1, len(vec_ops))
            self.assertEqual("relu6", vec_ops[0].get("op"))
            self.assertEqual("Y_DRAM", vec_ops[0].get("dst"))
            self.assertEqual([], dma_y_ops)

    def test_terminal_vecop_leakyrelu_lowers_without_direct_output(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            onnx_path = tmp / "terminal_vec_leakyrelu.onnx"
            sched_path = tmp / "terminal_vec_leakyrelu.yml"
            bin_path = tmp / "terminal_vec_leakyrelu.bin"

            self._write_terminal_leakyrelu_onnx(
                onnx_path,
                name="terminal_vec_leakyrelu",
                b=128,
                input_shape=[64],
            )
            schedule = self._run_lowering(onnx_path, sched_path)
            self._validate_and_emit_bin(sched_path, bin_path)

            notes = schedule.get("mapper_notes", {})
            self.assertEqual("terminal_vec_op", notes.get("graph_kind"))
            self.assertEqual("leakyrelu", notes.get("terminal_vec_op"))
            self.assertFalse(bool(notes.get("terminal_vecop_direct_output")))

            vec_ops = [op for op in schedule["ops"] if op.get("type") == "vec_op"]
            dma_y_ops = [op for op in schedule["ops"] if str(op.get("id", "")).startswith("dma_y")]
            self.assertEqual(1, len(vec_ops))
            self.assertEqual("leakyrelu", vec_ops[0].get("op"))
            self.assertEqual("ACT_B_SRAM", vec_ops[0].get("dst"))
            self.assertEqual(1, len(dma_y_ops))
            self.assertEqual("ACT_B_SRAM", dma_y_ops[0].get("src"))
            self.assertEqual("Y_DRAM", dma_y_ops[0].get("dst"))

    def test_terminal_vecop_leakyrelu_direct_output_when_arch_requests_it(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            onnx_path = tmp / "terminal_vec_leakyrelu_direct.onnx"
            sched_path = tmp / "terminal_vec_leakyrelu_direct.yml"
            bin_path = tmp / "terminal_vec_leakyrelu_direct.bin"

            self._write_terminal_leakyrelu_onnx(
                onnx_path,
                name="terminal_vec_leakyrelu_direct",
                b=128,
                input_shape=[2, 4, 8],
                add_flatten=True,
            )
            schedule = self._run_lowering(
                onnx_path,
                sched_path,
                arch_path=ARCH_TERMINAL_VECOP_DIRECT_OUTPUT_PATH,
            )
            self._validate_and_emit_bin(sched_path, bin_path)

            notes = schedule.get("mapper_notes", {})
            self.assertEqual("terminal_vec_op", notes.get("graph_kind"))
            self.assertEqual("leakyrelu", notes.get("terminal_vec_op"))
            self.assertTrue(bool(notes.get("input_flattened")))
            self.assertTrue(bool(notes.get("terminal_vecop_direct_output")))

            vec_ops = [op for op in schedule["ops"] if op.get("type") == "vec_op"]
            dma_y_ops = [op for op in schedule["ops"] if str(op.get("id", "")).startswith("dma_y")]
            self.assertEqual(1, len(vec_ops))
            self.assertEqual("leakyrelu", vec_ops[0].get("op"))
            self.assertEqual("Y_DRAM", vec_ops[0].get("dst"))
            self.assertEqual([], dma_y_ops)

    def test_terminal_vecop_hardsigmoid_lowers_without_direct_output(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            onnx_path = tmp / "terminal_vec_hardsigmoid.onnx"
            sched_path = tmp / "terminal_vec_hardsigmoid.yml"
            bin_path = tmp / "terminal_vec_hardsigmoid.bin"

            self._write_terminal_hardsigmoid_onnx(
                onnx_path,
                name="terminal_vec_hardsigmoid",
                b=128,
                input_shape=[64],
            )
            schedule = self._run_lowering(onnx_path, sched_path)
            self._validate_and_emit_bin(sched_path, bin_path)

            notes = schedule.get("mapper_notes", {})
            self.assertEqual("terminal_vec_op", notes.get("graph_kind"))
            self.assertEqual("hardsigmoid", notes.get("terminal_vec_op"))
            self.assertFalse(bool(notes.get("terminal_vecop_direct_output")))

            vec_ops = [op for op in schedule["ops"] if op.get("type") == "vec_op"]
            dma_y_ops = [op for op in schedule["ops"] if str(op.get("id", "")).startswith("dma_y")]
            self.assertEqual(1, len(vec_ops))
            self.assertEqual("hardsigmoid", vec_ops[0].get("op"))
            self.assertEqual("ACT_B_SRAM", vec_ops[0].get("dst"))
            self.assertEqual(1, len(dma_y_ops))
            self.assertEqual("ACT_B_SRAM", dma_y_ops[0].get("src"))
            self.assertEqual("Y_DRAM", dma_y_ops[0].get("dst"))
            self.assertEqual("dma_y", schedule["events"][0]["signal_on"])

    def test_terminal_vecop_hardsigmoid_direct_output_when_arch_requests_it(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            onnx_path = tmp / "terminal_vec_hardsigmoid_direct.onnx"
            sched_path = tmp / "terminal_vec_hardsigmoid_direct.yml"
            bin_path = tmp / "terminal_vec_hardsigmoid_direct.bin"

            self._write_terminal_hardsigmoid_onnx(
                onnx_path,
                name="terminal_vec_hardsigmoid_direct",
                b=128,
                input_shape=[2, 4, 8],
                add_flatten=True,
            )
            schedule = self._run_lowering(
                onnx_path,
                sched_path,
                arch_path=ARCH_TERMINAL_VECOP_DIRECT_OUTPUT_PATH,
            )
            self._validate_and_emit_bin(sched_path, bin_path)

            notes = schedule.get("mapper_notes", {})
            self.assertEqual("terminal_vec_op", notes.get("graph_kind"))
            self.assertEqual("hardsigmoid", notes.get("terminal_vec_op"))
            self.assertTrue(bool(notes.get("input_flattened")))
            self.assertTrue(bool(notes.get("terminal_vecop_direct_output")))

            vec_ops = [op for op in schedule["ops"] if op.get("type") == "vec_op"]
            dma_y_ops = [op for op in schedule["ops"] if str(op.get("id", "")).startswith("dma_y")]
            self.assertEqual(1, len(vec_ops))
            self.assertEqual("hardsigmoid", vec_ops[0].get("op"))
            self.assertEqual("Y_DRAM", vec_ops[0].get("dst"))
            self.assertEqual([], dma_y_ops)
            self.assertEqual("vec1", schedule["events"][0]["signal_on"])


    def test_terminal_vecop_hardtanh_lowers_without_direct_output(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            onnx_path = tmp / "terminal_vec_hardtanh.onnx"
            sched_path = tmp / "terminal_vec_hardtanh.yml"
            bin_path = tmp / "terminal_vec_hardtanh.bin"

            self._write_terminal_hardtanh_onnx(
                onnx_path,
                name="terminal_vec_hardtanh",
                b=128,
                input_shape=[64],
            )
            schedule = self._run_lowering(onnx_path, sched_path)
            self._validate_and_emit_bin(sched_path, bin_path)

            notes = schedule.get("mapper_notes", {})
            self.assertEqual("terminal_vec_op", notes.get("graph_kind"))
            self.assertEqual("hardtanh", notes.get("terminal_vec_op"))
            self.assertFalse(bool(notes.get("terminal_vecop_direct_output")))

            vec_ops = [op for op in schedule["ops"] if op.get("type") == "vec_op"]
            dma_y_ops = [op for op in schedule["ops"] if str(op.get("id", "")).startswith("dma_y")]
            self.assertEqual(1, len(vec_ops))
            self.assertEqual("hardtanh", vec_ops[0].get("op"))
            self.assertEqual("ACT_B_SRAM", vec_ops[0].get("dst"))
            self.assertEqual(1, len(dma_y_ops))
            self.assertEqual("ACT_B_SRAM", dma_y_ops[0].get("src"))
            self.assertEqual("Y_DRAM", dma_y_ops[0].get("dst"))
            self.assertEqual("dma_y", schedule["events"][0]["signal_on"])

    def test_terminal_vecop_hardtanh_direct_output_when_arch_requests_it(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            onnx_path = tmp / "terminal_vec_hardtanh_direct.onnx"
            sched_path = tmp / "terminal_vec_hardtanh_direct.yml"
            bin_path = tmp / "terminal_vec_hardtanh_direct.bin"

            self._write_terminal_hardtanh_onnx(
                onnx_path,
                name="terminal_vec_hardtanh_direct",
                b=128,
                input_shape=[2, 4, 8],
                add_flatten=True,
            )
            schedule = self._run_lowering(
                onnx_path,
                sched_path,
                arch_path=ARCH_TERMINAL_VECOP_DIRECT_OUTPUT_PATH,
            )
            self._validate_and_emit_bin(sched_path, bin_path)

            notes = schedule.get("mapper_notes", {})
            self.assertEqual("terminal_vec_op", notes.get("graph_kind"))
            self.assertEqual("hardtanh", notes.get("terminal_vec_op"))
            self.assertTrue(bool(notes.get("input_flattened")))
            self.assertTrue(bool(notes.get("terminal_vecop_direct_output")))

            vec_ops = [op for op in schedule["ops"] if op.get("type") == "vec_op"]
            dma_y_ops = [op for op in schedule["ops"] if str(op.get("id", "")).startswith("dma_y")]
            self.assertEqual(1, len(vec_ops))
            self.assertEqual("hardtanh", vec_ops[0].get("op"))
            self.assertEqual("Y_DRAM", vec_ops[0].get("dst"))
            self.assertEqual([], dma_y_ops)
            self.assertEqual("vec1", schedule["events"][0]["signal_on"])


if __name__ == "__main__":
    unittest.main()
