import importlib.util
import json
import subprocess
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


class LlmDecoderCompareRegressionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.compare_mod = _load_module('llm_decoder_compare_test', 'npu/eval/compare_llm_decoder_quality.py')

    def test_compare_decoder_manifests_reports_exact_match_rates(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            ref_a = td_path / 'ref_a.json'
            ref_b = td_path / 'ref_b.json'
            cand_a = td_path / 'cand_a.json'
            cand_b = td_path / 'cand_b.json'
            ref_a.write_text(json.dumps({'sample_id': 'a', 'reference': {'next_token_id': 1, 'next_token_text': ' A'}}), encoding='utf-8')
            ref_b.write_text(json.dumps({'sample_id': 'b', 'reference': {'next_token_id': 2, 'next_token_text': ' B'}}), encoding='utf-8')
            cand_a.write_text(json.dumps({'sample_id': 'a', 'candidate': {'next_token_id': 1, 'next_token_text': ' A'}}), encoding='utf-8')
            cand_b.write_text(json.dumps({'sample_id': 'b', 'candidate': {'next_token_id': 3, 'next_token_text': ' C'}}), encoding='utf-8')
            ref_manifest = {
                'dataset_id': 'llm_decoder_eval_tiny_v1',
                'task': 'greedy_next_token',
                'samples': [
                    {'sample_id': 'a', 'reference_json': str(ref_a)},
                    {'sample_id': 'b', 'reference_json': str(ref_b)},
                ],
            }
            cand_manifest = {
                'dataset_id': 'llm_decoder_eval_tiny_v1',
                'task': 'greedy_next_token',
                'candidate_semantics': 'synthetic',
                'samples': [
                    {'sample_id': 'a', 'candidate_json': str(cand_a)},
                    {'sample_id': 'b', 'candidate_json': str(cand_b)},
                ],
            }
            metrics = self.compare_mod.compare_decoder_manifests(ref_manifest, cand_manifest)
            self.assertEqual(2, metrics['aggregate']['sample_count'])
            self.assertEqual(1, metrics['aggregate']['next_token_id_match_count'])
            self.assertEqual(1, metrics['aggregate']['next_token_text_match_count'])
            self.assertEqual(0.5, metrics['aggregate']['next_token_id_match_rate'])
            self.assertEqual(0.5, metrics['aggregate']['next_token_text_match_rate'])

    def test_compare_decoder_manifests_reports_selected_tensor_trace_drift(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            ref_doc = td_path / 'ref.json'
            cand_doc = td_path / 'cand.json'
            ref_doc.write_text(json.dumps({
                'sample_id': 'geo',
                'reference': {
                    'next_token_id': 5,
                    'next_token_text': ' Paris',
                    'selected_tensors': [
                        {'name': 'present.0.key', 'step': 0, 'shape': [1, 2], 'min': -1.0, 'max': 1.0, 'mean': 0.1, 'std': 0.2},
                        {'name': 'present.0.value', 'step': 0, 'shape': [1, 2], 'min': -2.0, 'max': 2.0, 'mean': 0.3, 'std': 0.4},
                    ],
                },
            }), encoding='utf-8')
            cand_doc.write_text(json.dumps({
                'sample_id': 'geo',
                'candidate': {
                    'next_token_id': 5,
                    'next_token_text': ' Paris',
                    'selected_tensors': [
                        {'name': 'present.0.key', 'step': 0, 'shape': [1, 2], 'min': -0.5, 'max': 1.5, 'mean': 0.2, 'std': 0.25, 'quantization': {'bits': 4}},
                        {'name': 'present.1.key', 'step': 0, 'shape': [1, 3], 'min': -3.0, 'max': 3.0, 'mean': 0.0, 'std': 0.5},
                    ],
                },
            }), encoding='utf-8')
            ref_manifest = {
                'dataset_id': 'llm_decoder_eval_tiny_v1',
                'task': 'greedy_next_token',
                'samples': [{'sample_id': 'geo', 'reference_json': str(ref_doc)}],
            }
            cand_manifest = {
                'dataset_id': 'llm_decoder_eval_tiny_v1',
                'task': 'greedy_next_token',
                'candidate_semantics': 'synthetic',
                'samples': [{'sample_id': 'geo', 'candidate_json': str(cand_doc)}],
            }
            metrics = self.compare_mod.compare_decoder_manifests(ref_manifest, cand_manifest)
            trace = metrics['samples'][0]['selected_tensor_trace']
            self.assertEqual(1, trace['aggregate']['matched_tensor_count'])
            self.assertEqual(1, trace['aggregate']['shape_match_count'])
            self.assertEqual(1.0, trace['aggregate']['shape_match_rate'])
            self.assertEqual(1, trace['aggregate']['missing_in_reference_count'])
            self.assertEqual(1, trace['aggregate']['missing_in_candidate_count'])
            self.assertEqual(0.1, trace['compared_tensors'][0]['deltas']['mean_abs_delta'])
            self.assertEqual({'bits': 4}, trace['compared_tensors'][0]['candidate_quantization'])
            self.assertEqual(1, metrics['aggregate']['selected_tensor_trace']['matched_tensor_count'])

    def test_compare_decoder_cli_emits_json(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            ref_doc = td_path / 'ref.json'
            cand_doc = td_path / 'cand.json'
            ref_doc.write_text(json.dumps({'sample_id': 'geo', 'reference': {'next_token_id': 5, 'next_token_text': ' Paris'}}), encoding='utf-8')
            cand_doc.write_text(json.dumps({'sample_id': 'geo', 'candidate': {'next_token_id': 4, 'next_token_text': ' is'}}), encoding='utf-8')
            ref_manifest = td_path / 'reference_manifest.json'
            cand_manifest = td_path / 'candidate_manifest.json'
            ref_manifest.write_text(json.dumps({
                'dataset_id': 'llm_decoder_eval_tiny_v1',
                'task': 'greedy_next_token',
                'samples': [{'sample_id': 'geo', 'reference_json': str(ref_doc)}],
            }), encoding='utf-8')
            cand_manifest.write_text(json.dumps({
                'dataset_id': 'llm_decoder_eval_tiny_v1',
                'task': 'greedy_next_token',
                'candidate_semantics': 'synthetic',
                'samples': [{'sample_id': 'geo', 'candidate_json': str(cand_doc)}],
            }), encoding='utf-8')
            out_json = td_path / 'metrics.json'
            subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / 'npu/eval/compare_llm_decoder_quality.py'),
                    '--reference-manifest',
                    str(ref_manifest),
                    '--candidate-manifest',
                    str(cand_manifest),
                    '--out',
                    str(out_json),
                ],
                check=True,
            )
            metrics = json.loads(out_json.read_text(encoding='utf-8'))
            self.assertEqual(1, metrics['aggregate']['sample_count'])
            self.assertEqual(0.0, metrics['aggregate']['next_token_id_match_rate'])
            self.assertEqual(0.0, metrics['aggregate']['next_token_text_match_rate'])
