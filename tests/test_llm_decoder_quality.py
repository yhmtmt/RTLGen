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


class LlmDecoderQualityRegressionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.decoder = _load_module('llm_decoder_quality_test', 'npu/eval/llm_decoder_quality.py')

    def test_space_prefix_tokenizer_preserves_single_next_token(self):
        prompt = 'The capital of France is'
        continuation = ' Paris'
        self.assertEqual(
            ['The', ' capital', ' of', ' France', ' is'],
            self.decoder.tokenize_space_prefix_words(prompt),
        )
        self.assertEqual([' Paris'], self.decoder.tokenize_space_prefix_words(continuation))

    def test_build_decoder_reference_doc_binds_dataset_tokenizer_and_model(self):
        dataset_manifest = {
            'dataset_id': 'llm_decoder_eval_tiny_v1',
            'task': 'greedy_next_token',
        }
        sample = {
            'sample_id': 'geo_france_capital',
            'prompt': 'The capital of France is',
            'expected_continuation': ' Paris',
        }
        tokenizer_manifest = {
            'tokenizer_id': 'llm_decoder_space_prefix_v1',
            'kind': 'space_prefix_words',
        }
        vocab = {
            'The': 0,
            ' capital': 1,
            ' of': 2,
            ' France': 3,
            ' is': 4,
            ' Paris': 5,
        }
        model_contract = {
            'model_id': 'llm_decoder_tiny_v1',
            'status': 'reference_only_placeholder',
            'execution_backend': 'python_reference_placeholder',
        }
        doc = self.decoder.build_decoder_reference_doc(
            dataset_manifest=dataset_manifest,
            sample=sample,
            tokenizer_manifest=tokenizer_manifest,
            vocab=vocab,
            model_contract=model_contract,
            dataset_manifest_path='runs/datasets/llm_decoder_eval_tiny_v1/manifest.json',
            tokenizer_manifest_path='runs/tokenizers/llm_decoder_space_prefix_v1/manifest.json',
            model_contract_path='runs/models/llm_decoder_tiny_v1/model_contract.json',
        )
        self.assertEqual('llm_decoder_eval_tiny_v1', doc['dataset_id'])
        self.assertEqual('llm_decoder_space_prefix_v1', doc['tokenizer']['tokenizer_id'])
        self.assertEqual('llm_decoder_tiny_v1', doc['model_binding']['model_id'])
        self.assertEqual(['The', ' capital', ' of', ' France', ' is'], doc['prompt']['tokens'])
        self.assertEqual(' Paris', doc['reference']['next_token_text'])
        self.assertEqual(5, doc['reference']['next_token_id'])

    def test_decoder_reference_suite_generator_emits_reference_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            sample_file = td_path / 'samples.jsonl'
            sample_file.write_text(
                json.dumps(
                    {
                        'sample_id': 'color_banana',
                        'prompt': 'A ripe banana is usually',
                        'expected_continuation': ' yellow',
                    }
                )
                + '\n',
                encoding='utf-8',
            )
            vocab_json = td_path / 'vocab.json'
            vocab_json.write_text(
                json.dumps(
                    {
                        'version': 0.1,
                        'tokenizer_id': 'llm_decoder_space_prefix_v1',
                        'tokens': ['A', ' ripe', ' banana', ' is', ' usually', ' yellow'],
                    }
                ),
                encoding='utf-8',
            )
            tokenizer_manifest = td_path / 'tokenizer_manifest.json'
            tokenizer_manifest.write_text(
                json.dumps(
                    {
                        'version': 0.1,
                        'tokenizer_id': 'llm_decoder_space_prefix_v1',
                        'kind': 'space_prefix_words',
                        'vocab_json': str(vocab_json),
                    }
                ),
                encoding='utf-8',
            )
            model_contract = td_path / 'model_contract.json'
            model_contract.write_text(
                json.dumps(
                    {
                        'version': 0.1,
                        'model_id': 'llm_decoder_tiny_v1',
                        'status': 'reference_only_placeholder',
                        'execution_backend': 'python_reference_placeholder',
                    }
                ),
                encoding='utf-8',
            )
            dataset_manifest = td_path / 'dataset_manifest.json'
            dataset_manifest.write_text(
                json.dumps(
                    {
                        'version': 0.1,
                        'dataset_id': 'llm_decoder_eval_tiny_v1',
                        'task': 'greedy_next_token',
                        'sample_file': str(sample_file),
                        'tokenizer_manifest': str(tokenizer_manifest),
                        'model_contract': str(model_contract),
                    }
                ),
                encoding='utf-8',
            )
            out_dir = td_path / 'reference'
            out_manifest = td_path / 'reference_manifest.json'
            subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / 'npu/eval/gen_llm_decoder_reference_suite.py'),
                    '--dataset-manifest',
                    str(dataset_manifest),
                    '--out-dir',
                    str(out_dir),
                    '--out-manifest',
                    str(out_manifest),
                ],
                check=True,
            )
            manifest = json.loads(out_manifest.read_text(encoding='utf-8'))
            self.assertEqual('llm_decoder_eval_tiny_v1', manifest['dataset_id'])
            self.assertEqual(1, len(manifest['samples']))
            ref_doc = json.loads((out_dir / 'color_banana.json').read_text(encoding='utf-8'))
            self.assertEqual(' yellow', ref_doc['reference']['next_token_text'])


if __name__ == '__main__':
    unittest.main()
