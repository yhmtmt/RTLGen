# Design Brief

## Proposal
- `proposal_id`: `prop_l2_decoder_attention_kv_subtile_pipeline_schedule_softmax_recip_lut_v1`
- `title`: Softmax-recip subtile pipeline schedule for Llama7B attention

## Problem
The softmax-recip HBM-closed on-chip schedule result leaves tile attention at
`1354` cycles while measured HBM service is `1301` cycles. The next useful
frontier target is the attention compute schedule rather than more HBM bandwidth.

## Hypothesis
Subdividing the tile into streaming QK/softmax/V subtiles can overlap HBM,
QK, statistics, value, and local SRAM work while fitting inside the measured
local SRAM capacity.

## Evaluation Scope
- Direct comparison: subtile pipeline rows versus
  `l2_decoder_attention_kv_hbm_closed_onchip_schedule_softmax_recip_lut_llama7b_v1`.
- Evaluation mode: `frontier_detail`.
- Dependency: HBM-closed softmax-recip artifact must be merged and materialized.
- Excluded first-stage comparisons: new HBM timing, SRAM repacking, NoC RTL,
  precision changes, and KV quality changes.
- Follow-on: revisit compute-area accounting for dual-MAC mode and consider
  physical pipelined attention datapath evaluation.

## Knowledge Inputs
- `npu/eval/estimate_llm_decoder_attention_kv_subtile_pipeline_schedule.py`
- `runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_hbm_closed_onchip_schedule__l2_decoder_attention_kv_hbm_closed_onchip_schedule_softmax_recip_lut_llama7b_v1.json`

## Candidate Direction
Schedule QK, softmax stats/correction, and value work across legal subtiles
with bounded live stream buffers.

## Direction Gate
- status: approved
- approved_by: developer_agent
- approved_utc: 2026-06-17T11:56:58Z
- note: Directly targets the current tile-attention bottleneck.
