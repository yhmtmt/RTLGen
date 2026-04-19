import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_module(name: str, rel_path: str):
    path = REPO_ROOT / rel_path
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class LlmReferenceRegressionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.onnx_lite = _load_module('onnx_lite_llm_ref', 'npu/mapper/onnx_lite.py')
        cls.llm_ref = _load_module('llm_reference_test', 'npu/eval/llm_reference.py')

    def test_attention_block_uses_nonzero_initializers(self):
        with tempfile.TemporaryDirectory() as td:
            onnx_path = Path(td) / 'attn.onnx'
            onnx_path.write_bytes(
                self.onnx_lite.build_attention_block_model_bytes(
                    name='attn_ref',
                    seq_len=8,
                    hidden_dim=16,
                    num_blocks=2,
                    dtype=self.onnx_lite.TENSOR_INT8,
                )
            )
            model = self.onnx_lite.load_onnx_model(onnx_path)
            self.assertTrue(model.graph.initializers)
            raw_nonzero = [any(b != 0 for b in t.raw_data) for t in model.graph.initializers.values()]
            self.assertTrue(all(raw_nonzero))

    def test_llm_reference_fixture_is_nontrivial_and_comparable(self):
        with tempfile.TemporaryDirectory() as td:
            onnx_path = Path(td) / 'attn.onnx'
            onnx_path.write_bytes(
                self.onnx_lite.build_attention_block_model_bytes(
                    name='attn_ref',
                    seq_len=8,
                    hidden_dim=16,
                    num_blocks=2,
                    dtype=self.onnx_lite.TENSOR_INT8,
                )
            )
            fixture = self.llm_ref.build_reference_fixture(onnx_path, model_id='attn_ref')
            y = fixture['outputs']['Y']['values']
            total_abs = sum(abs(v) for row in y for v in row)
            self.assertGreater(total_abs, 0.0)

            same_metrics = self.llm_ref.compare_reference_docs(fixture, fixture)
            self.assertEqual(0.0, same_metrics['aggregate']['max_abs_error'])
            self.assertEqual(0.0, same_metrics['aggregate']['mean_abs_error'])

            candidate = {
                'model_id': 'attn_ref',
                'outputs': {
                    'Y': {
                        'shape': fixture['outputs']['Y']['shape'],
                        'values': [list(row) for row in fixture['outputs']['Y']['values']],
                    }
                },
            }
            candidate['outputs']['Y']['values'][0][0] += 0.5
            diff_metrics = self.llm_ref.compare_reference_docs(fixture, candidate)
            self.assertGreater(diff_metrics['aggregate']['max_abs_error'], 0.0)
            self.assertGreater(diff_metrics['aggregate']['mean_abs_error'], 0.0)

    def test_llm_candidate_fixture_is_quantized_and_comparable(self):
        with tempfile.TemporaryDirectory() as td:
            onnx_path = Path(td) / 'attn.onnx'
            onnx_path.write_bytes(
                self.onnx_lite.build_attention_block_model_bytes(
                    name='attn_candidate',
                    seq_len=8,
                    hidden_dim=16,
                    num_blocks=2,
                    dtype=self.onnx_lite.TENSOR_INT8,
                )
            )
            reference = self.llm_ref.build_reference_fixture(onnx_path, model_id='attn_candidate')
            candidate = self.llm_ref.build_candidate_fixture(onnx_path, model_id='attn_candidate')

            self.assertEqual(
                'int8_gemm_with_q0_7_softmax_dequantized_outputs',
                candidate['candidate_semantics'],
            )
            self.assertEqual('u8_q0_7_dequantized', candidate['outputs']['P1']['quantization'])
            self.assertEqual('int8_signed', candidate['outputs']['S1']['quantization'])
            self.assertEqual('int8_signed', candidate['outputs']['Y']['quantization'])

            probs = candidate['outputs']['P1']['values']
            self.assertTrue(all(0.0 <= value <= 1.0 for row in probs for value in row))

            candidate_self = self.llm_ref.compare_reference_docs(candidate, candidate)
            self.assertEqual(0.0, candidate_self['aggregate']['max_abs_error'])
            self.assertEqual(0.0, candidate_self['aggregate']['mean_abs_error'])

            ref_vs_candidate = self.llm_ref.compare_reference_docs(reference, candidate)
            self.assertGreater(ref_vs_candidate['aggregate']['count'], 0.0)
            self.assertGreater(ref_vs_candidate['aggregate']['max_abs_error'], 0.0)
            self.assertGreater(ref_vs_candidate['aggregate']['mean_abs_error'], 0.0)


if __name__ == '__main__':
    unittest.main()
