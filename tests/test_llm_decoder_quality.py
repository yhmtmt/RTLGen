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
        cls.backend_mod = _load_module('decoder_backend_test', 'npu/eval/decoder_backend.py')

    def test_space_prefix_tokenizer_preserves_single_next_token(self):
        prompt = 'The capital of France is'
        continuation = ' Paris'
        self.assertEqual(
            ['The', ' capital', ' of', ' France', ' is'],
            self.decoder.tokenize_space_prefix_words(prompt),
        )
        self.assertEqual([' Paris'], self.decoder.tokenize_space_prefix_words(continuation))

    def test_load_tokenizer_bundle_reads_special_token_metadata(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            vocab_json = td_path / 'vocab.json'
            vocab_json.write_text(
                json.dumps(
                    {
                        'version': 0.1,
                        'tokenizer_id': 'llm_decoder_wordpiece_stub_v1',
                        'tokens': ['[PAD]', '[BOS]', '[EOS]', '[UNK]', 'The', 'capital'],
                    }
                ),
                encoding='utf-8',
            )
            tokenizer_manifest = {
                'tokenizer_id': 'llm_decoder_wordpiece_stub_v1',
                'kind': 'wordpiece_stub',
                'status': 'stub_bundle_contract',
                'backend_interface': 'decoder_tokenizer_v1',
                'vocab_json': 'vocab.json',
                'special_tokens': {
                    'bos': '[BOS]',
                    'eos': '[EOS]',
                    'unk': '[UNK]',
                    'pad': '[PAD]',
                },
            }
            bundle = self.decoder.load_tokenizer_bundle(tokenizer_manifest, manifest_path=td_path / 'manifest.json')
            self.assertEqual('llm_decoder_wordpiece_stub_v1', bundle['tokenizer_id'])
            self.assertEqual('wordpiece_stub', bundle['kind'])
            self.assertEqual(1, bundle['special_tokens']['bos']['id'])
            self.assertTrue(bundle['special_tokens']['unk']['present_in_vocab'])
            self.assertEqual(4, bundle['vocab']['The'])

    def test_load_tokenizer_bundle_rejects_duplicate_tokens(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            vocab_json = td_path / 'vocab.json'
            vocab_json.write_text(
                json.dumps(
                    {
                        'version': 0.1,
                        'tokenizer_id': 'dup_case',
                        'tokens': ['[PAD]', '[PAD]'],
                    }
                ),
                encoding='utf-8',
            )
            tokenizer_manifest = {
                'tokenizer_id': 'dup_case',
                'kind': 'wordpiece_stub',
                'vocab_json': str(vocab_json),
            }
            with self.assertRaises(ValueError):
                self.decoder.load_tokenizer_bundle(tokenizer_manifest, manifest_path=td_path / 'manifest.json')

    def test_tokenize_decoder_text_supports_wordpiece_stub(self):
        bundle = {
            'kind': 'wordpiece_stub',
            'vocab': {'Paris': 0},
            'special_tokens': {},
            'unk_supported': False,
        }
        self.assertEqual(['Paris'], self.decoder.tokenize_decoder_text(' Paris', bundle))

    def test_build_decoder_reference_doc_supports_wordpiece_stub_bundle(self):
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
            'tokenizer_id': 'llm_decoder_wordpiece_stub_v1',
            'kind': 'wordpiece_stub',
            'status': 'stub_bundle_contract',
            'backend_interface': 'decoder_tokenizer_v1',
            'special_tokens': {'unk': '[UNK]'},
            'unk_supported': True,
        }
        vocab = {
            '[UNK]': 0,
            'The': 1,
            'capital': 2,
            'of': 3,
            'France': 4,
            'is': 5,
            'Paris': 6,
        }
        bundle = self.decoder.build_tokenizer_bundle(
            tokenizer_manifest,
            vocab=vocab,
            manifest_path='runs/tokenizers/llm_decoder_wordpiece_stub_v1/manifest.json',
        )
        model_contract = {
            'model_id': 'llm_decoder_tiny_v1',
            'status': 'file_backed_tokenizer_stub',
            'execution_backend': 'decoder_backend_v1',
        }
        doc = self.decoder.build_decoder_reference_doc(
            dataset_manifest=dataset_manifest,
            sample=sample,
            tokenizer_manifest=tokenizer_manifest,
            vocab=vocab,
            tokenizer_bundle=bundle,
            model_contract=model_contract,
            dataset_manifest_path='runs/datasets/llm_decoder_eval_tiny_v1/manifest.json',
            tokenizer_manifest_path='runs/tokenizers/llm_decoder_wordpiece_stub_v1/manifest.json',
            model_contract_path='runs/models/llm_decoder_tiny_v1/model_contract.json',
            backend_config={'backend_id': 'placeholder_v1'},
        )
        self.assertEqual(['The', 'capital', 'of', 'France', 'is'], doc['prompt']['tokens'])
        self.assertEqual(6, doc['reference']['next_token_id'])
        self.assertEqual('stub_bundle_contract', doc['tokenizer']['status'])

    def test_backend_config_resolution_prefers_dataset_over_model(self):
        dataset_manifest = {
            'decoder_backend_configs': {
                'candidate': {
                    'backend_id': 'placeholder_v1',
                    'runtime_target': 'dataset_override',
                    'candidate_rule': 'last_token_plus_parity_shift',
                    'equivalence_group': 'dataset_group',
                }
            }
        }
        model_contract = {
            'backend_configs': {
                'candidate': {
                    'backend_id': 'placeholder_v1',
                    'runtime_target': 'model_default',
                    'equivalence_group': 'model_group',
                }
            }
        }
        cfg = self.decoder.resolve_decoder_backend_config(dataset_manifest, model_contract, role='candidate')
        self.assertEqual('placeholder_v1', cfg['backend_id'])
        self.assertEqual('candidate', cfg['role'])
        self.assertEqual('dataset_override', cfg['runtime_target'])
        self.assertEqual('dataset_group', cfg['equivalence_group'])
        self.assertEqual('decoder_backend_v1', cfg['interface'])

    def test_build_decoder_reference_doc_binds_backend_metadata(self):
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
            'execution_backend': 'decoder_backend_v1',
        }
        backend_config = {
            'backend_id': 'placeholder_v1',
            'runtime_target': 'software_reference',
            'equivalence_group': 'placeholder_v1',
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
            backend_config=backend_config,
        )
        self.assertEqual('llm_decoder_eval_tiny_v1', doc['dataset_id'])
        self.assertEqual('llm_decoder_space_prefix_v1', doc['tokenizer']['tokenizer_id'])
        self.assertEqual('llm_decoder_tiny_v1', doc['model_binding']['model_id'])
        self.assertEqual('placeholder_v1', doc['backend']['backend_id'])
        self.assertEqual('reference', doc['backend']['role'])
        self.assertEqual('placeholder_v1', doc['backend']['equivalence_group'])
        self.assertEqual(['The', ' capital', ' of', ' France', ' is'], doc['prompt']['tokens'])
        self.assertEqual(' Paris', doc['reference']['next_token_text'])
        self.assertEqual(5, doc['reference']['next_token_id'])

    def test_build_decoder_candidate_doc_is_deterministic_and_comparable(self):
        dataset_manifest = {
            'dataset_id': 'llm_decoder_eval_tiny_v1',
            'task': 'greedy_next_token',
        }
        sample = {
            'sample_id': 'math_two_plus_two',
            'prompt': '2 + 2 =',
            'expected_continuation': ' 4',
        }
        tokenizer_manifest = {
            'tokenizer_id': 'llm_decoder_space_prefix_v1',
            'kind': 'space_prefix_words',
        }
        vocab = {
            '2': 0,
            ' +': 1,
            ' 2': 2,
            ' =': 3,
            ' 4': 4,
        }
        model_contract = {
            'model_id': 'llm_decoder_tiny_v1',
            'status': 'reference_only_placeholder',
            'execution_backend': 'decoder_backend_v1',
        }
        reference = self.decoder.build_decoder_reference_doc(
            dataset_manifest=dataset_manifest,
            sample=sample,
            tokenizer_manifest=tokenizer_manifest,
            vocab=vocab,
            model_contract=model_contract,
            dataset_manifest_path='runs/datasets/llm_decoder_eval_tiny_v1/manifest.json',
            tokenizer_manifest_path='runs/tokenizers/llm_decoder_space_prefix_v1/manifest.json',
            model_contract_path='runs/models/llm_decoder_tiny_v1/model_contract.json',
            backend_config={'backend_id': 'placeholder_v1'},
        )
        candidate = self.decoder.build_decoder_candidate_doc(
            dataset_manifest=dataset_manifest,
            sample=sample,
            tokenizer_manifest=tokenizer_manifest,
            vocab=vocab,
            model_contract=model_contract,
            dataset_manifest_path='runs/datasets/llm_decoder_eval_tiny_v1/manifest.json',
            tokenizer_manifest_path='runs/tokenizers/llm_decoder_space_prefix_v1/manifest.json',
            model_contract_path='runs/models/llm_decoder_tiny_v1/model_contract.json',
            backend_config={'backend_id': 'placeholder_v1'},
        )
        self.assertEqual(
            'space_prefix_placeholder_last_token_plus_parity_shift',
            candidate['candidate_semantics'],
        )
        self.assertEqual('candidate', candidate['backend']['role'])
        self.assertEqual('placeholder_v1', candidate['backend']['equivalence_group'])
        self.assertEqual(3, candidate['candidate']['next_token_id'])
        self.assertEqual(' =', candidate['candidate']['next_token_text'])
        metrics = self.decoder.compare_decoder_reference_docs(reference, candidate)
        self.assertEqual(0, metrics['aggregate']['next_token_id_match'])
        self.assertEqual(0, metrics['aggregate']['next_token_text_match'])


    def test_command_json_backend_executes_reference_runner(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            runner = td_path / 'runner.py'
            runner.write_text(
                """
import json
import sys
req = json.load(sys.stdin)
sample = req['sample']
out = {
    'reference': {
        'expected_continuation': sample['expected_continuation'],
        'next_token_text': sample['expected_continuation'],
        'next_token_id': 5,
        'next_token_rank': 1,
        'selected_tensors': [],
    },
    'notes': 'command runner reference ok',
    'backend_runtime': {'runner': 'unit_test', 'role': req['role']},
}
json.dump(out, sys.stdout)
""".strip(),
                encoding='utf-8',
            )
            dataset_manifest = {'dataset_id': 'llm_decoder_eval_tiny_v1', 'task': 'greedy_next_token'}
            tokenizer_manifest = {'tokenizer_id': 'llm_decoder_space_prefix_v1', 'kind': 'space_prefix_words'}
            model_contract = {
                'model_id': 'llm_decoder_tiny_v1',
                'status': 'reference_only_placeholder',
                'execution_backend': 'decoder_backend_v1',
            }
            vocab = {'The': 0, ' capital': 1, ' of': 2, ' France': 3, ' is': 4, ' Paris': 5}
            sample = {
                'sample_id': 'geo_france_capital',
                'prompt': 'The capital of France is',
                'expected_continuation': ' Paris',
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
                backend_config={
                    'backend_id': 'command_json_v1',
                    'command': [sys.executable, str(runner)],
                    'equivalence_group': 'cpu_reference_v1',
                    'runtime_target': 'cpu_reference',
                },
            )
            self.assertEqual('command_json_v1', doc['backend']['backend_id'])
            self.assertEqual('reference', doc['backend']['role'])
            self.assertEqual('cpu_reference_v1', doc['backend']['equivalence_group'])
            self.assertEqual(' Paris', doc['reference']['next_token_text'])
            self.assertEqual('unit_test', doc['backend_runtime']['runner'])
            self.assertEqual([sys.executable, str(runner)], doc['backend_invocation']['command'])

    def test_command_json_backend_executes_candidate_runner(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            runner = td_path / 'runner.py'
            runner.write_text(
                """
import json
import sys
req = json.load(sys.stdin)
out = {
    'candidate': {
        'next_token_id': 3,
        'next_token_text': ' =',
        'confidence': 0.75,
    },
    'candidate_semantics': 'external_command_stub',
    'notes': 'command runner candidate ok',
}
json.dump(out, sys.stdout)
""".strip(),
                encoding='utf-8',
            )
            dataset_manifest = {'dataset_id': 'llm_decoder_eval_tiny_v1', 'task': 'greedy_next_token'}
            tokenizer_manifest = {'tokenizer_id': 'llm_decoder_space_prefix_v1', 'kind': 'space_prefix_words'}
            model_contract = {
                'model_id': 'llm_decoder_tiny_v1',
                'status': 'reference_only_placeholder',
                'execution_backend': 'decoder_backend_v1',
            }
            vocab = {'2': 0, ' +': 1, ' 2': 2, ' =': 3, ' 4': 4}
            sample = {
                'sample_id': 'math_two_plus_two',
                'prompt': '2 + 2 =',
                'expected_continuation': ' 4',
            }
            doc = self.decoder.build_decoder_candidate_doc(
                dataset_manifest=dataset_manifest,
                sample=sample,
                tokenizer_manifest=tokenizer_manifest,
                vocab=vocab,
                model_contract=model_contract,
                dataset_manifest_path='runs/datasets/llm_decoder_eval_tiny_v1/manifest.json',
                tokenizer_manifest_path='runs/tokenizers/llm_decoder_space_prefix_v1/manifest.json',
                model_contract_path='runs/models/llm_decoder_tiny_v1/model_contract.json',
                backend_config={
                    'backend_id': 'command_json_v1',
                    'command': [sys.executable, str(runner)],
                    'equivalence_group': 'hardware_emulation_v1',
                    'runtime_target': 'hardware_emulation',
                },
            )
            self.assertEqual('command_json_v1', doc['backend']['backend_id'])
            self.assertEqual('candidate', doc['backend']['role'])
            self.assertEqual('hardware_emulation_v1', doc['backend']['equivalence_group'])
            self.assertEqual(3, doc['candidate']['next_token_id'])
            self.assertEqual(' =', doc['candidate']['next_token_text'])
            self.assertEqual('external_command_stub', doc['candidate_semantics'])
            self.assertEqual([sys.executable, str(runner)], doc['backend_invocation']['command'])

    def test_replay_backend_rehydrates_reference_doc_from_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            replay_doc = {
                'version': 0.1,
                'dataset_id': 'old_dataset',
                'sample_id': 'geo_france_capital',
                'task': 'greedy_next_token',
                'dataset_manifest': 'old/manifest.json',
                'tokenizer': {
                    'tokenizer_id': 'llm_decoder_space_prefix_v1',
                    'kind': 'space_prefix_words',
                    'manifest_path': 'old/tokenizer_manifest.json',
                },
                'model_binding': {
                    'model_id': 'llm_decoder_tiny_v1',
                    'status': 'reference_only_placeholder',
                    'contract_path': 'old/model_contract.json',
                    'execution_backend': 'decoder_backend_v1',
                },
                'backend': {
                    'backend_id': 'placeholder_v1',
                    'role': 'reference',
                },
                'prompt': {
                    'text': 'The capital of France is',
                    'tokens': ['The', ' capital', ' of', ' France', ' is'],
                    'token_ids': [0, 1, 2, 3, 4],
                    'token_count': 5,
                },
                'reference': {
                    'expected_continuation': ' Paris',
                    'next_token_text': ' Paris',
                    'next_token_id': 5,
                    'next_token_rank': 1,
                    'selected_tensors': [],
                },
            }
            replay_doc_path = td_path / 'reference_doc.json'
            replay_doc_path.write_text(json.dumps(replay_doc), encoding='utf-8')
            replay_manifest = td_path / 'reference_manifest.json'
            replay_manifest.write_text(
                json.dumps(
                    {
                        'version': 0.1,
                        'dataset_id': 'llm_decoder_eval_tiny_v1',
                        'backend_config': {'backend_id': 'placeholder_v1', 'role': 'reference'},
                        'samples': [
                            {
                                'sample_id': 'geo_france_capital',
                                'reference_json': str(replay_doc_path),
                            }
                        ],
                    }
                ),
                encoding='utf-8',
            )
            dataset_manifest = {'dataset_id': 'llm_decoder_eval_tiny_v1', 'task': 'greedy_next_token'}
            tokenizer_manifest = {'tokenizer_id': 'llm_decoder_space_prefix_v1', 'kind': 'space_prefix_words'}
            model_contract = {
                'model_id': 'llm_decoder_tiny_v1',
                'status': 'reference_only_placeholder',
                'execution_backend': 'decoder_backend_v1',
            }
            vocab = {'The': 0, ' capital': 1, ' of': 2, ' France': 3, ' is': 4, ' Paris': 5}
            sample = {
                'sample_id': 'geo_france_capital',
                'prompt': 'The capital of France is',
                'expected_continuation': ' Paris',
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
                backend_config={
                    'backend_id': 'replay_v1',
                    'replay_manifest': str(replay_manifest),
                    'equivalence_group': 'frozen_reference_v1',
                },
            )
            self.assertEqual('replay_v1', doc['backend']['backend_id'])
            self.assertEqual('reference', doc['backend']['role'])
            self.assertEqual('frozen_reference_v1', doc['backend']['equivalence_group'])
            self.assertEqual(' Paris', doc['reference']['next_token_text'])
            self.assertEqual(str(replay_manifest), doc['replay_source']['replay_manifest'])
            self.assertEqual(str(replay_doc_path), doc['replay_source']['sample_entry']['reference_json'])
            self.assertEqual('placeholder_v1', doc['replay_source']['source_backend']['backend_id'])

    def test_replay_backend_rehydrates_candidate_doc_from_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            replay_doc = {
                'version': 0.1,
                'dataset_id': 'old_dataset',
                'sample_id': 'math_two_plus_two',
                'task': 'greedy_next_token',
                'dataset_manifest': 'old/manifest.json',
                'tokenizer': {
                    'tokenizer_id': 'llm_decoder_space_prefix_v1',
                    'kind': 'space_prefix_words',
                    'manifest_path': 'old/tokenizer_manifest.json',
                },
                'model_binding': {
                    'model_id': 'llm_decoder_tiny_v1',
                    'status': 'reference_only_placeholder',
                    'contract_path': 'old/model_contract.json',
                    'execution_backend': 'decoder_backend_v1',
                },
                'backend': {
                    'backend_id': 'placeholder_v1',
                    'role': 'candidate',
                },
                'prompt': {
                    'text': '2 + 2 =',
                    'tokens': ['2', ' +', ' 2', ' ='],
                    'token_ids': [0, 1, 2, 3],
                    'token_count': 4,
                },
                'reference': {
                    'expected_continuation': ' 4',
                    'next_token_text': ' 4',
                    'next_token_id': 4,
                    'next_token_rank': 1,
                    'selected_tensors': [],
                },
                'candidate_semantics': 'frozen_candidate_replay',
                'candidate': {
                    'next_token_id': 3,
                    'next_token_text': ' =',
                    'confidence': 1.0,
                },
            }
            replay_doc_path = td_path / 'candidate_doc.json'
            replay_doc_path.write_text(json.dumps(replay_doc), encoding='utf-8')
            replay_manifest = td_path / 'candidate_manifest.json'
            replay_manifest.write_text(
                json.dumps(
                    {
                        'version': 0.1,
                        'dataset_id': 'llm_decoder_eval_tiny_v1',
                        'backend_config': {'backend_id': 'placeholder_v1', 'role': 'candidate'},
                        'samples': [
                            {
                                'sample_id': 'math_two_plus_two',
                                'candidate_json': str(replay_doc_path),
                            }
                        ],
                    }
                ),
                encoding='utf-8',
            )
            dataset_manifest = {'dataset_id': 'llm_decoder_eval_tiny_v1', 'task': 'greedy_next_token'}
            tokenizer_manifest = {'tokenizer_id': 'llm_decoder_space_prefix_v1', 'kind': 'space_prefix_words'}
            model_contract = {
                'model_id': 'llm_decoder_tiny_v1',
                'status': 'reference_only_placeholder',
                'execution_backend': 'decoder_backend_v1',
            }
            vocab = {'2': 0, ' +': 1, ' 2': 2, ' =': 3, ' 4': 4}
            sample = {
                'sample_id': 'math_two_plus_two',
                'prompt': '2 + 2 =',
                'expected_continuation': ' 4',
            }
            doc = self.decoder.build_decoder_candidate_doc(
                dataset_manifest=dataset_manifest,
                sample=sample,
                tokenizer_manifest=tokenizer_manifest,
                vocab=vocab,
                model_contract=model_contract,
                dataset_manifest_path='runs/datasets/llm_decoder_eval_tiny_v1/manifest.json',
                tokenizer_manifest_path='runs/tokenizers/llm_decoder_space_prefix_v1/manifest.json',
                model_contract_path='runs/models/llm_decoder_tiny_v1/model_contract.json',
                backend_config={
                    'backend_id': 'replay_v1',
                    'replay_manifest': str(replay_manifest),
                    'equivalence_group': 'frozen_candidate_v1',
                },
            )
            self.assertEqual('replay_v1', doc['backend']['backend_id'])
            self.assertEqual('candidate', doc['backend']['role'])
            self.assertEqual('frozen_candidate_v1', doc['backend']['equivalence_group'])
            self.assertEqual(3, doc['candidate']['next_token_id'])
            self.assertEqual(' =', doc['candidate']['next_token_text'])
            self.assertEqual('frozen_candidate_replay', doc['candidate_semantics'])
            self.assertEqual(str(replay_doc_path), doc['replay_source']['replay_doc'])
            self.assertIn('Replay-backed decoder fixture loaded from frozen artifacts.', doc['notes'])

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
                        'execution_backend': 'decoder_backend_v1',
                        'backend_configs': {
                            'reference': {'backend_id': 'placeholder_v1'}
                        },
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
            self.assertEqual('placeholder_v1', manifest['backend_config']['backend_id'])
            self.assertEqual(1, len(manifest['samples']))
            ref_doc = json.loads((out_dir / 'color_banana.json').read_text(encoding='utf-8'))
            self.assertEqual(' yellow', ref_doc['reference']['next_token_text'])
            self.assertEqual('reference', ref_doc['backend']['role'])

    def test_decoder_candidate_suite_generator_emits_candidate_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            sample_file = td_path / 'samples.jsonl'
            sample_file.write_text(
                json.dumps(
                    {
                        'sample_id': 'geo_france_capital',
                        'prompt': 'The capital of France is',
                        'expected_continuation': ' Paris',
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
                        'tokens': ['The', ' capital', ' of', ' France', ' is', ' Paris'],
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
                        'execution_backend': 'decoder_backend_v1',
                        'backend_configs': {
                            'candidate': {'backend_id': 'placeholder_v1'}
                        },
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
            out_dir = td_path / 'candidate'
            out_manifest = td_path / 'candidate_manifest.json'
            subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / 'npu/eval/gen_llm_decoder_candidate_suite.py'),
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
            self.assertEqual('placeholder_v1', manifest['backend_config']['backend_id'])
            self.assertEqual(
                'space_prefix_placeholder_last_token_plus_parity_shift',
                manifest['candidate_semantics'],
            )
            candidate_doc = json.loads((out_dir / 'geo_france_capital.json').read_text(encoding='utf-8'))
            self.assertIn('candidate', candidate_doc)
            self.assertEqual('candidate', candidate_doc['backend']['role'])


if __name__ == '__main__':
    unittest.main()
