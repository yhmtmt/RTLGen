LLM Attention Tail Stress Set v1
================================

Purpose
-------
Stage a bounded stress extension of `llm_attention_tail_v1`.
The previous tail campaign showed low softmax occupancy and no dependency-wait
or backpressure pressure. This set increases sequence length and repeated
softmax-bearing blocks before committing to any softmax datapath proposal.

Contents
--------
- `tail_attn4_s256_h64`: four attention-tail proxy blocks at sequence length 256
- `tail_attn6_s128_h64`: six blocks at the previous largest sequence length
- `tail_attn6_s256_h64`: six blocks at sequence length 256

Operator shape
--------------
Each block is:
- `Gemm(score)`
- `Softmax`
- `Gemm(value)`

The value output feeds the next block, so each model has repeated non-terminal
`Softmax` episodes in one inference path.

Current purpose
---------------
This set exists to test whether:
- larger sequence length increases softmax occupancy
- repeated softmax episodes expose dependency waits
- queue backpressure appears under bounded stress
- the next LLM architecture step should target softmax buffering, softmax
  pipeline partitioning, scheduler overlap, or a richer decoder benchmark

Boundary
--------
This is still an ONNX-lite attention-tail proxy. It does not make decoder
quality claims and does not include KV-cache traffic. It is the pressure check
between `llm_attention_tail_v1` and a later practical decoder-style benchmark.

Optional fixtures
-----------------
Deterministic reference and candidate fixtures can be regenerated locally when
numerical comparison is needed. They are intentionally not checked in for this
stress set because the larger `128`/`256` sequence shapes produce large JSON
fixtures.

Generate/regenerate
-------------------
```sh
python3 npu/mapper/examples/gen_llm_attention_tail_stress_suite_lite.py \
  --out-dir runs/models/llm_attention_tail_stress_v1
```

Generate optional numerical fixtures:
```sh
python3 npu/eval/gen_llm_reference_suite.py \
  --manifest runs/models/llm_attention_tail_stress_v1/manifest.json
python3 npu/eval/gen_llm_candidate_suite.py \
  --manifest runs/models/llm_attention_tail_stress_v1/manifest.json
python3 npu/eval/compare_llm_reference.py \
  --reference-json runs/models/llm_attention_tail_stress_v1/reference/tail_attn6_s256_h64.json \
  --candidate-json runs/models/llm_attention_tail_stress_v1/candidate/tail_attn6_s256_h64.json
```
