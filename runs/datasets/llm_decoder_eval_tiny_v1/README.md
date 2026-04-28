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
Active ONNX exact-reference and explicit softmax/normalization candidate binding.

What exists now:
- `manifest.json`
- `samples.jsonl`
- `reference_manifest.json`
- `candidate_manifest.json`
- `npu/eval/llm_decoder_contract.schema.json`
- `npu/eval/validate_llm_decoder_contract.py`
- fetched GPT-2-family tokenizer/model binding for reference artifacts
- active ONNX exact-reference generation via `decoder_backend_v1` + `command_json_v1`
- active ONNX candidate generation with configurable softmax and normalization modes
- replay-backed frozen-artifact loading via `replay_v1` for later emulation-vs-hardware equivalence checks

What does not exist yet:
- hardware-oriented candidate backend
- continuation/perplexity metrics
- larger decoder prompt set

Current binding
---------------
- tokenizer: `runs/tokenizers/llm_decoder_gpt2_bpe_stub_v1/manifest.json`
- model contract: `runs/models/llm_decoder_tiny_v1/model_contract.json`
- exact reference runner: `npu/eval/run_llm_decoder_onnx_reference.py`
- active candidate runner: `npu/eval/run_llm_decoder_onnx_candidate.py`

The reference side is a real ONNX Runtime exact-reference path. The candidate side now exposes both exact and approximate probability paths; the active mode uses q4 quantization on shifted logits inside the PWL softmax path, q4 quantization on softmax weights before normalization, and quantized reciprocal normalization. Both sides also trace `present.*` KV-cache outputs, with q4 trace quantization active on the candidate side.

Comparison
----------
- reference vs candidate summary: `python3 npu/eval/compare_llm_decoder_quality.py --reference-manifest runs/datasets/llm_decoder_eval_tiny_v1/reference_manifest.json --candidate-manifest runs/datasets/llm_decoder_eval_tiny_v1/candidate_manifest.json`
- contract validation: `python3 npu/eval/validate_llm_decoder_contract.py --dataset-manifest runs/datasets/llm_decoder_eval_tiny_v1/manifest.json`
