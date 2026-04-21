import importlib.util
import sys
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


class LlmDecoderOnnxCandidateRunnerRegressionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runner = _load_module('llm_decoder_onnx_candidate_runner_test', 'npu/eval/run_llm_decoder_onnx_candidate.py')

    def test_quantize_logits_symmetric_preserves_length_and_order_for_simple_case(self):
        logits = [1.0, 0.25, -0.5]
        quantized, approx = self.runner._quantize_logits_symmetric(logits, bits=4)
        self.assertEqual(len(logits), len(quantized))
        self.assertEqual(4, approx['bits'])
        self.assertEqual(7, approx['levels'])
        self.assertGreater(quantized[0], quantized[1])
        self.assertGreater(quantized[1], quantized[2])

    def test_quantize_logits_symmetric_rejects_too_few_bits(self):
        with self.assertRaises(SystemExit):
            self.runner._quantize_logits_symmetric([0.1, -0.2], bits=1)

    def test_softmax_exact_and_normalize_exact_produce_probability_distribution(self):
        weights, softmax_meta = self.runner._softmax_exact([1.0, 0.0, -1.0])
        probs, norm_meta = self.runner._normalize_exact(weights)
        self.assertEqual('softmax_exact', softmax_meta['mode'])
        self.assertEqual('normalize_exact', norm_meta['mode'])
        self.assertAlmostEqual(1.0, sum(probs), places=6)
        self.assertGreater(probs[0], probs[1])
        self.assertGreater(probs[1], probs[2])

    def test_softmax_approx_pwl_and_quantized_reciprocal_normalization_preserve_order(self):
        weights, softmax_meta = self.runner._softmax_approx_pwl([1.0, 0.0, -1.0])
        probs, norm_meta = self.runner._normalize_reciprocal_quantized(weights, reciprocal_bits=10)
        self.assertEqual('softmax_approx_pwl', softmax_meta['mode'])
        self.assertEqual('normalize_reciprocal_quantized', norm_meta['mode'])
        self.assertGreater(sum(probs), 0.95)
        self.assertLess(sum(probs), 1.05)
        self.assertGreater(probs[0], probs[1])
        self.assertGreater(probs[1], probs[2])

    def test_probability_quantization_preserves_probability_order(self):
        quantized, meta = self.runner._quantize_probabilities_unsigned([0.61, 0.28, 0.11], bits=8)
        self.assertEqual('unsigned_probability_quant', meta['mode'])
        self.assertGreater(quantized[0], quantized[1])
        self.assertGreater(quantized[1], quantized[2])

    def test_candidate_semantics_can_be_derived_from_backend_config(self):
        semantics = self.runner._derive_candidate_semantics({
            'logit_quant_bits': 4,
            'softmax_mode': 'approx_pwl',
            'normalization_mode': 'reciprocal_quantized',
            'normalization_reciprocal_bits': 10,
            'probability_quant_bits': 8,
        })
        self.assertEqual(
            'onnx_logits_q4_softmax_approx_pwl_norm_recip_q10_prob_q8',
            semantics,
        )


if __name__ == '__main__':
    unittest.main()
