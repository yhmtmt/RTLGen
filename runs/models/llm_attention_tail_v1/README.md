LLM Attention Tail Set v1
=========================

Purpose
-------
Stage the first repeated attention-tail benchmark set after `llm_smoke_v1`.
This suite is still an ONNX-lite proxy, but it is deliberately larger than the
smoke set so scheduler and overlap conclusions are driven by repeated
softmax-bearing paths.

Contents
--------
- `tail_attn2_s32_h64`: two attention-tail proxy blocks
- `tail_attn2_s64_h64`: two blocks at sequence length 64
- `tail_attn3_s64_h64`: three blocks at sequence length 64
- `tail_attn4_s64_h64`: four blocks at sequence length 64
- `tail_attn4_s128_h64`: four blocks at sequence length 128

Operator shape
--------------
Each block is:
- `Gemm(score)`
- `Softmax`
- `Gemm(value)`

The value output feeds the next block, so each model has multiple
non-terminal `Softmax` episodes in one inference path.

Current purpose
---------------
This set exists to validate:
- sequence-length pressure at `32`, `64`, and `128`
- repeated-softmax occupancy and completion behavior
- queue stall attribution
- overlap and backpressure counters
- per-model token-equivalent latency reporting

Boundary
--------
This set does not answer full decoder-quality questions. It provides the
repeated attention-tail performance and tensor-equivalence surface needed
before architecture knobs such as softmax internal pipelining, output
buffering, or queue-depth policy are ranked.

Fixtures
--------
Deterministic reference fixtures:
- `runs/models/llm_attention_tail_v1/reference_manifest.json`
- `runs/models/llm_attention_tail_v1/reference/<model_id>.json`

Deterministic candidate fixtures:
- `runs/models/llm_attention_tail_v1/candidate_manifest.json`
- `runs/models/llm_attention_tail_v1/candidate/<model_id>.json`

Generate/regenerate
-------------------
```sh
python3 npu/mapper/examples/gen_llm_attention_tail_suite_lite.py \
  --out-dir runs/models/llm_attention_tail_v1
python3 npu/eval/gen_llm_reference_suite.py \
  --manifest runs/models/llm_attention_tail_v1/manifest.json
python3 npu/eval/gen_llm_candidate_suite.py \
  --manifest runs/models/llm_attention_tail_v1/manifest.json
python3 npu/eval/compare_llm_reference.py \
  --reference-json runs/models/llm_attention_tail_v1/reference/tail_attn4_s128_h64.json \
  --candidate-json runs/models/llm_attention_tail_v1/candidate/tail_attn4_s128_h64.json
```
