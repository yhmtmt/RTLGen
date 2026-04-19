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
