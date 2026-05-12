# Decoder attention/KV tile stream measurement

- item_id: `item_l1_decoder_attention_kv_tile_stream_v1`
- layer: `layer1`
- kind: `circuit`
- status: `promoted_to_proposal`
- priority: `high`
- owner: `developer_agent`
- created_utc: `2026-05-12T02:30:00Z`
- updated_utc: `2026-05-12T02:30:00Z`
- proposal_id: `prop_l1_decoder_attention_kv_tile_stream_v1`
- proposal_path: `docs/proposals/prop_l1_decoder_attention_kv_tile_stream_v1/proposal.json`
- triggered_by_proposal: `prop_l2_decoder_attention_kv_memory_v1`
- triggering_evidence: `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_kv_memory_large_context_v2.json`

## Problem
- The current attention/KV model finds all focus points dominated by `qk_score`, and long-context best cases still spend most cycles KV-limited.
- The model is analytical; it needs a measured RTL/PPA anchor before we rely on it for memory hierarchy and NoC choices.

## Candidate Idea
- Measure a standalone attention/KV tile stream block after the RTLGen op lands.
- Start with one smoke point, then expand to a small frontier sweep over `head_dim`, `kv_bits`, lanes, and stream width.

## Why It Might Matter
- Directly calibrates the dominant long-context bottleneck.
- Separates real tile datapath PPA from current planning constants for shared SRAM, HBM, remote HBM, and NoC hop bandwidth.

## Required Work
- l1 change? `yes`, supplied by `item_l1_decoder_attention_kv_tile_op_v1`.
- l2 change? `no`.
- mapper change? `no`.
- quality gate required? `yes`.

## Evaluation Sketch
- `l1_decoder_attention_kv_tile_smoke_v1`: one bounded macro-style Nangate45 point.
- `l1_decoder_attention_kv_tile_frontier_v1`: follow-up sweep over selected width/precision points after smoke passes.

## Inputs / Sources
- `docs/proposals/prop_l1_decoder_attention_kv_tile_stream_v1/proposal.json`
- `runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_memory__l2_decoder_attention_kv_memory_large_context_v2.json`
- `runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_stage_breakdown__l2_decoder_stage_breakdown_large_array_v2.json`

## Open Questions
- Whether `kv_bits=4` should use packed int4 datapath logic immediately or first use unpacked int4 lanes with equivalent bit width for timing.
- Whether the frontier sweep should include `value_mix` in the first measured block or reserve it for a second block.

## Promotion Rule
- Promote after the proposal workspace is merged and the source-enabling RTLGen op is available on `master`.
