LLM Decoder Tiny v1
===================

Purpose
-------
Reference-side model contract for the first decoder-quality stage.

Current status
--------------
Active ONNX exact-reference pair plus explicit softmax/normalization candidate backends.

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
- candidate runner with both exact and approximate probability paths:
  - `npu/eval/run_llm_decoder_onnx_candidate.py`

Prepared candidate modes:
- exact softmax + exact normalization
- approximate PWL softmax + quantized reciprocal normalization

Active candidate semantics:
- `onnx_logits_fp_softmax_approx_pwl_in_q4_w_q4_norm_recip_q10_prob_fp`

What does not exist yet:
- hardware-oriented decoder execution backend
- approximation hooks inside the transformer itself beyond post-logit probability shaping
- larger-model exact-reference binding beyond this tiny seed model

The active reference pair is `onnx-community/tiny-random-gpt2-ONNX` at commit `90f61e71d6fa8e571d0ab0f95a637a5d7d8ed52f`, using the matched GPT-2 tokenizer assets from the same source. The active candidate backend reuses that same contract and now exposes both normal and approximate softmax/normalization paths, which is the first explicit probability-path emulation backend in the repo.
