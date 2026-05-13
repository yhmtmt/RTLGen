# Implementation Summary

## Scope

- Reuse the existing `decoder_attention_kv_memory` Layer 2 generator hook.
- Require the estimator support merged in PR #480.
- Feed the six merged `attention_kv_tile` frontier metrics files into the report.
- Keep the job low cost; no new RTL or physical implementation is requested.

## Evidence Inputs

- `l1_decoder_attention_kv_tile_frontier_v1`
- `l2_decoder_attention_kv_memory_large_context_v2`
- `runs/index.csv` entries from PR #478

## Out Of Scope

- measured SRAM macro banking
- measured NoC arbitration
- producer-coupled attention RTL
- quality impact of KV precision or sharing
