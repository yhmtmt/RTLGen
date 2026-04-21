LLM Decoder Eval Tiny v1
========================

Purpose
-------
Tiny curated prompt set for the first decoder-quality gate.

This dataset is intentionally small and inference-oriented. It is not a training
set and not a benchmark for model capability. Its role is to provide a stable,
cheap acceptance slice for approximate-hardware evaluation.

Current status
--------------
Active ONNX exact-reference dataset binding.

What exists now:
- `manifest.json`
- `samples.jsonl`
- `reference_manifest.json`
- `candidate_manifest.json`
- fetched GPT-2-family tokenizer/model binding for reference artifacts
- active ONNX exact-reference generation via `decoder_backend_v1` + `command_json_v1`
- placeholder candidate generation under the same tokenizer/model contract
- replay-backed frozen-artifact loading via `replay_v1` for later emulation-vs-hardware equivalence checks

What does not exist yet:
- approximation-aware candidate backend
- continuation/perplexity metrics
- larger decoder prompt set

Current binding
---------------
- tokenizer: `runs/tokenizers/llm_decoder_gpt2_bpe_stub_v1/manifest.json`
- model contract: `runs/models/llm_decoder_tiny_v1/model_contract.json`
- exact reference runner: `npu/eval/run_llm_decoder_onnx_reference.py`

The reference side is now a real ONNX Runtime exact-reference path. The candidate side is still intentionally synthetic so the repo can keep the equivalence/reporting contract stable while the approximation-aware backend is built.

Comparison
----------
- reference vs candidate summary: `python3 npu/eval/compare_llm_decoder_quality.py --reference-manifest runs/datasets/llm_decoder_eval_tiny_v1/reference_manifest.json --candidate-manifest runs/datasets/llm_decoder_eval_tiny_v1/candidate_manifest.json`
