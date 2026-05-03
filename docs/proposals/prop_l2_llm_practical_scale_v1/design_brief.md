# LLM Practical Scale Proxy

- `proposal_id`: `prop_l2_llm_practical_scale_v1`
- `item_id`: `l2_llm_practical_scale_v1`

## Context

The current practical LLM proxy reached 32 active tokens, 512 KV-context score
width, and six repeated attention episodes. It still ranked `fp16_nm1` ahead of
`fp16_nm2`, with low softmax occupancy and no dependency wait/backpressure.

The decoder bf16/PWL scale-proxy quality result also passed, but it remains tied
to the tiny decoder model. The next scale check should therefore put pressure on
the architecture side before proposing wider compute arrays.

## Proposed Check

Add `llm_practical_scale_v1`:
- `practical_scale_attn6_s64_h64_kv1024`
- `practical_scale_attn8_s64_h64_kv1024`
- `practical_scale_attn6_s64_h64_kv2048`

Run the existing `fp16_nm1` and `fp16_nm2` physical points over this larger
campaign and inspect scheduler visibility, softmax occupancy, latency, and
energy.

## Decision Use

If `nm2` starts winning or softmax/wait pressure appears, the next proposal
should be a wider compute-array or softmax/datapath-focused architecture point.
If `nm1` still wins and pressure remains low, keep the precision/quality
frontier moving and defer wider arrays until a stronger workload exposes demand.
