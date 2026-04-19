LLM Smoke Set v1
=================

Purpose
-------
Stage the first mapper-runnable LLM-oriented benchmark set. This is still a
bring-up suite, not a product-accuracy suite.

Contents
--------
- `attn1_s32_h64`: one attention-style proxy block
- `attn1_s64_h64`: one block with longer sequence pressure
- `attn2_s32_h64`: two repeated proxy blocks so one model path contains more
  than one non-terminal `Softmax` episode

Operator shape
--------------
These are ONNX-lite attention proxies, not faithful transformer exports. Each
block is:
- `Gemm(score)`
- `Softmax`
- `Gemm(value)`

Current purpose
---------------
This set exists to validate:
- non-terminal `Softmax` lowering
- repeated-softmax schedule visibility
- first LLM-oriented scheduler counters

Boundary
--------
This set does **not** yet answer full LLM accuracy questions. The long-term goal is
to evaluate approximation-induced precision loss as well as schedule/PPA with a
more realistic decoder-style benchmark and reference path.

What exists now
---------------
Deterministic reference fixtures are now generated for this exact model set:
- `runs/models/llm_smoke_v1/reference_manifest.json`
- `runs/models/llm_smoke_v1/reference/<model_id>.json`

These fixtures define:
- one deterministic input tensor per model
- exact reference outputs for the emitted ONNX-lite attention-proxy binaries
- a comparison hook for later candidate-output error metrics

A first candidate-output path also exists now for the same models:
- `runs/models/llm_smoke_v1/candidate_manifest.json`
- `runs/models/llm_smoke_v1/candidate/<model_id>.json`

Current candidate semantics:
- signed-int8 GEMM outputs with clamp/round after each `Gemm`
- descriptor-level `Softmax` quantized to unsigned `Q0.7`, then dequantized to `[0, 1]` for comparison
- deterministic input identical to the reference path

Generate/regenerate
-------------------
```sh
python3 npu/mapper/examples/gen_llm_smoke_suite_lite.py \
  --out-dir runs/models/llm_smoke_v1
python3 npu/eval/gen_llm_reference_suite.py \
  --manifest runs/models/llm_smoke_v1/manifest.json
python3 npu/eval/gen_llm_candidate_suite.py \
  --manifest runs/models/llm_smoke_v1/manifest.json
python3 npu/eval/compare_llm_reference.py \
  --reference-json runs/models/llm_smoke_v1/reference/attn2_s32_h64.json \
  --candidate-json runs/models/llm_smoke_v1/candidate/attn2_s32_h64.json
```

Campaign note
-------------
The paired campaign now has both deterministic reference fixtures and a first
candidate-output comparison path. It should still be treated as bring-up,
not final LLM-accuracy evidence, until a later decoder/data-backed accuracy
stage is added.
