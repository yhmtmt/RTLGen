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


class LlmDecoderOnnxRunnerRegressionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runner = _load_module('llm_decoder_onnx_runner_test', 'npu/eval/run_llm_decoder_onnx_reference.py')

    def test_extract_next_token_logits_accepts_common_shapes(self):
        one_d = [0.1, 0.5, -0.2]
        two_d = [[0.0, 0.1], [0.2, 0.3]]
        three_d = [[[1.0, 2.0], [3.0, 4.0]]]
        self.assertEqual(one_d, self.runner._extract_next_token_logits(one_d))
        self.assertEqual(two_d[-1], self.runner._extract_next_token_logits(two_d))
        self.assertEqual(three_d[0][-1], self.runner._extract_next_token_logits(three_d))

    def test_extract_next_token_logits_rejects_other_ranks(self):
        with self.assertRaises(ValueError):
            self.runner._extract_next_token_logits([[[[0.0]]]])

    def test_runner_rejects_gpt2_bundle_without_tokenizer_json_path(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            vocab_json = td_path / 'vocab.json'
            merges_txt = td_path / 'merges.txt'
            vocab_json.write_text(
                json.dumps({'T': 0, 'h': 1, 'e': 2, '<|endoftext|>': 3}),
                encoding='utf-8',
            )
            merges_txt.write_text('#version: 0.2\nT h\nTh e\n', encoding='utf-8')
            tokenizer_manifest = td_path / 'tokenizer_manifest.json'
            tokenizer_manifest.write_text(
                json.dumps(
                    {
                        'tokenizer_id': 'llm_decoder_gpt2_bpe_stub_v1',
                        'kind': 'gpt2_bpe',
                        'family': 'gpt2_bpe',
                        'vocab_json': str(vocab_json),
                        'merges_txt': str(merges_txt),
                    }
                ),
                encoding='utf-8',
            )
            request = {
                'role': 'reference',
                'backend_config': {
                    'backend_id': 'command_json_v1',
                    'onnx_model_path': str(td_path / 'missing.onnx'),
                    'input_name': 'input_ids',
                },
                'sample': {
                    'sample_id': 'geo_france_capital',
                    'prompt': 'The capital of France is',
                    'expected_continuation': ' Paris',
                },
                'paths': {
                    'tokenizer_manifest_path': str(tokenizer_manifest),
                },
            }
            proc = subprocess.run(
                [sys.executable, str(REPO_ROOT / 'npu/eval/run_llm_decoder_onnx_reference.py')],
                input=json.dumps(request),
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(0, proc.returncode)
            self.assertIn('gpt2_bpe tokenizer bundle is missing tokenizer_json_path', proc.stderr)

    def test_runner_fails_cleanly_when_model_path_is_missing(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            vocab_json = td_path / 'vocab.json'
            model_config = td_path / 'config.json'
            vocab_json.write_text(
                json.dumps({'tokens': ['The', ' capital', ' of', ' France', ' is', ' Paris']}),
                encoding='utf-8',
            )
            model_config.write_text(
                json.dumps({'n_layer': 2, 'n_head': 2, 'n_embd': 128}),
                encoding='utf-8',
            )
            tokenizer_manifest = td_path / 'tokenizer_manifest.json'
            tokenizer_manifest.write_text(
                json.dumps(
                    {
                        'tokenizer_id': 'llm_decoder_space_prefix_v1',
                        'kind': 'space_prefix_words',
                        'vocab_json': str(vocab_json),
                    }
                ),
                encoding='utf-8',
            )
            request = {
                'role': 'reference',
                'backend_config': {
                    'backend_id': 'command_json_v1',
                    'onnx_model_path': str(td_path / 'missing.onnx'),
                    'model_config_path': str(model_config),
                    'input_name': 'input_ids',
                },
                'sample': {
                    'sample_id': 'geo_france_capital',
                    'prompt': 'The capital of France is',
                    'expected_continuation': ' Paris',
                },
                'paths': {
                    'tokenizer_manifest_path': str(tokenizer_manifest),
                },
            }
            proc = subprocess.run(
                [sys.executable, str(REPO_ROOT / 'npu/eval/run_llm_decoder_onnx_reference.py')],
                input=json.dumps(request),
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(0, proc.returncode)
            self.assertIn('NoSuchFile', proc.stderr)


if __name__ == '__main__':
    unittest.main()
