LLM Decoder Tiny v1
===================

Purpose
-------
Reference-side model contract for the first decoder-quality stage.

Current status
--------------
Active ONNX exact-reference pair plus approximation-aware candidate backend.

What exists now:
- `model_contract.json`
- active reference backend config using `command_json_v1`
- active candidate backend config using `command_json_v1`
- explicit ONNX exact-reference binding manifest:
  - `reference_onnx_binding.json`
- fetched exact-reference ONNX assets under:
  - `reference_onnx/model.onnx`
  - `reference_onnx/config.json`
  - `reference_onnx/generation_config.json`
- fetched GPT-2-family tokenizer assets paired with that path
- local exact-reference validation through `npu/eval/run_llm_decoder_onnx_reference.py`
- first approximation-aware candidate runner:
  - `npu/eval/run_llm_decoder_onnx_candidate.py`

Current candidate semantics:
- symmetric logit quantization after exact ONNX inference
- default active mode: `onnx_logits_symmetric_quant_q4`

What does not exist yet:
- hardware-oriented decoder execution backend
- approximation hooks beyond post-logit quantization
- larger-model exact-reference binding beyond this tiny seed model

The active reference pair is `onnx-community/tiny-random-gpt2-ONNX` at commit `90f61e71d6fa8e571d0ab0f95a637a5d7d8ed52f`, using the matched GPT-2 tokenizer assets from the same source. The active candidate backend reuses that same contract and applies deterministic symmetric quantization to logits before argmax, giving the repo its first approximation-aware decoder comparison path.
