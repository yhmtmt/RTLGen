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


class LlmDecoderContractRegressionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.validator = _load_module('llm_decoder_contract_validator_test', 'npu/eval/validate_llm_decoder_contract.py')

    def test_decoder_contract_schema_declares_required_artifact_shapes(self):
        schema_path = REPO_ROOT / 'npu/eval/llm_decoder_contract.schema.json'
        schema = json.loads(schema_path.read_text(encoding='utf-8'))
        defs = schema['$defs']
        self.assertIn('prompt_sample', defs)
        self.assertIn('dataset_manifest', defs)
        self.assertIn('reference_artifact', defs)
        self.assertIn('candidate_artifact', defs)
        self.assertIn('metrics_report', defs)
        metrics_required = defs['metrics_report']['properties']['aggregate']['required']
        self.assertIn('next_token_id_match_rate', metrics_required)
        self.assertIn('topk_contains_reference_id_rate', metrics_required)
        self.assertIn('selected_tensor_trace', metrics_required)

    def test_checked_in_tiny_decoder_contract_validates(self):
        result = self.validator.validate_decoder_contract(
            'runs/datasets/llm_decoder_eval_tiny_v1/manifest.json'
        )
        self.assertTrue(result['ok'], result['errors'])
        self.assertEqual('llm_decoder_eval_tiny_v1', result['dataset_id'])
        self.assertEqual(5, result['sample_count'])
        aggregate = result['metrics']['aggregate']
        self.assertEqual(5, aggregate['sample_count'])
        self.assertIn('topk_contains_reference_id_rate', aggregate)
        self.assertIn('selected_tensor_trace', aggregate)

    def test_validator_cli_writes_metrics_summary(self):
        with tempfile.TemporaryDirectory() as td:
            out_path = Path(td) / 'decoder_contract_validation.json'
            subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / 'npu/eval/validate_llm_decoder_contract.py'),
                    '--dataset-manifest',
                    'runs/datasets/llm_decoder_eval_tiny_v1/manifest.json',
                    '--out',
                    str(out_path),
                ],
                cwd=REPO_ROOT,
                check=True,
                stdout=subprocess.DEVNULL,
            )
            doc = json.loads(out_path.read_text(encoding='utf-8'))
            self.assertTrue(doc['ok'], doc['errors'])
            self.assertEqual(5, doc['metrics']['aggregate']['sample_count'])
