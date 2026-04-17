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
This set does **not** yet answer LLM accuracy questions. The long-term goal is
to evaluate approximation-induced precision loss as well as schedule/PPA. That
requires a later benchmark stage with real LLM numerical reference checking,
not only this proxy suite.

Generate/regenerate
-------------------
```sh
python3 npu/mapper/examples/gen_llm_smoke_suite_lite.py \
  --out-dir runs/models/llm_smoke_v1
```

Campaign note
-------------
The paired campaign should be treated as bring-up only until scheduler metrics
and accuracy-evaluation hooks are added.
