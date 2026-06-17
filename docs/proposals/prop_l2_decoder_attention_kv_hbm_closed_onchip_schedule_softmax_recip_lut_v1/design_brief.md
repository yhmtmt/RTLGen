# Design Brief

## Proposal
- `proposal_id`: `prop_l2_decoder_attention_kv_hbm_closed_onchip_schedule_softmax_recip_lut_v1`
- `title`: Softmax-recip HBM-closed on-chip schedule closure for Llama7B attention

## Problem
The current softmax-recip Llama7B attention frontier has measured SRAM rebalance
and measured HBM service, but the follow-on on-chip schedule closure was still
available only for the older non-softmax path.

## Hypothesis
If on-chip service is re-swept using the softmax-recip measured-HBM source,
the result should reveal whether the remaining frontier is memory-service
limited or still tile-attention limited.

## Evaluation Scope
- Direct comparison: source measured-HBM softmax-recip frontier versus the best
  HBM-closed on-chip schedule row.
- Evaluation mode: `frontier_detail`.
- Dependency: `l2_decoder_attention_kv_measured_hbm_service_softmax_recip_lut_llama7b_v1`
  must be merged and materialized first.
- Excluded first stage: full NoC RTL, new HBM timing model, SRAM repacking,
  precision changes, and KV sharing quality changes.
- Follow-on: run the softmax-recip subtile pipeline schedule if tile attention
  remains dominant.

## Knowledge Inputs
- `npu/eval/estimate_llm_decoder_attention_kv_hbm_closed_onchip_schedule.py`
- `npu/eval/estimate_llm_decoder_attention_kv_onchip_service_schedule.py`
- `runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_measured_hbm_service__l2_decoder_attention_kv_measured_hbm_service_softmax_recip_lut_llama7b_v1.json`

## Candidate Direction
Re-sweep schedule policy, bank arbitration, queue depth, router hop latency,
packet payload, and prefetch overlap over the measured softmax-recip HBM source.

## Direction Gate
- status: approved
- approved_by: developer_agent
- approved_utc: 2026-06-17T11:47:54Z
- note: Required to materialize the softmax-recip source for subtile pipeline scheduling.
