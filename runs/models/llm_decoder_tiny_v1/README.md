LLM Decoder Tiny v1
===================

Purpose
-------
Reference-side model contract for the first decoder-quality stage.

Current status
--------------
Active ONNX exact-reference pair.

What exists now:
- `model_contract.json`
- active reference backend config using `command_json_v1`
- placeholder candidate backend config for later approximation work
- executable backend interface that can call an external CPU, emulation, or hardware-target runner via `command_json_v1`
- explicit ONNX exact-reference binding manifest:
  - `reference_onnx_binding.json`
- fetched exact-reference ONNX assets under:
  - `reference_onnx/model.onnx`
  - `reference_onnx/config.json`
  - `reference_onnx/generation_config.json`
- fetched GPT-2-family tokenizer assets paired with that path
- local exact-reference validation through `npu/eval/run_llm_decoder_onnx_reference.py`

What does not exist yet:
- approximation-aware candidate backend for the same model pair
- hardware-oriented decoder execution backend
- larger-model exact-reference binding beyond this tiny seed model

The first active exact-reference pair is `onnx-community/tiny-random-gpt2-ONNX` at commit `90f61e71d6fa8e571d0ab0f95a637a5d7d8ed52f`, using the matched GPT-2 tokenizer assets from the same source. The candidate side is still placeholder-only; this contract now gives the repo a real CPU exact-reference path to compare against future approximation-aware or hardware-oriented backends.
