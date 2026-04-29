LLM Practical Set v1
====================

Purpose
-------
Stage the first practical decoder-style ONNX-lite proxy after the attention-tail
stress ladder. The stress ladder increased repeated softmax pressure but still
showed no wait or backpressure, so this set adds an explicit KV-context proxy
before any softmax datapath proposal is considered.

Contents
--------
- `practical_tail_attn4_s16_h64_kv256`: 16 active tokens, four attention
  episodes, 256-token KV context proxy
- `practical_tail_attn4_s32_h64_kv512`: 32 active tokens, four attention
  episodes, 512-token KV context proxy
- `practical_tail_attn6_s32_h64_kv512`: 32 active tokens, six attention
  episodes, 512-token KV context proxy

Operator shape
--------------
Each block is:
- `Gemm(score)` from active-token hidden state to a KV-context score dimension
- `Softmax`
- `Gemm(value)` from the KV-context probability dimension back to hidden state

This is still a proxy, not a full decoder export. The KV-context pressure is
represented by `score_dim = kv_context_tokens` and by manifest metadata for
`kv_cache_proxy_bytes`.

Boundary
--------
This set does not claim dataset-backed decoder quality. It is a runnable NPU
campaign bridge between repeated attention-tail scheduler evidence and later
decoder-quality proposals bound to `llm_decoder_eval_tiny_v1`.

Generate/regenerate
-------------------
```sh
python3 npu/mapper/examples/gen_llm_practical_suite_lite.py \
  --out-dir runs/models/llm_practical_v1
```

Optional numerical fixtures can be generated with the existing LLM reference
and candidate tools when tensor drift inspection is needed. They are not checked
in by default because this practical slice is intended primarily for campaign
latency, scheduler, and KV-context pressure evidence.
