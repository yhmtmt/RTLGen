# Implementation Summary

## Proposal
- `proposal_id`: `prop_l2_decoder_attention_kv_hbm_closed_onchip_schedule_softmax_recip_lut_v1`
- title: Softmax-recip HBM-closed on-chip schedule closure

## Scope
- Generated the L2 campaign item
  `l2_decoder_attention_kv_hbm_closed_onchip_schedule_softmax_recip_lut_llama7b_v1`.
- Consumed the softmax-recip measured-HBM artifact as the source.
- Produced the HBM-closed on-chip schedule artifact for the softmax-recip path.

## Files Changed
- `runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_hbm_closed_onchip_schedule__l2_decoder_attention_kv_hbm_closed_onchip_schedule_softmax_recip_lut_llama7b_v1.json`
- `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_kv_hbm_closed_onchip_schedule_softmax_recip_lut_llama7b_v1.json`
- `docs/proposals/prop_l2_decoder_attention_kv_hbm_closed_onchip_schedule_softmax_recip_lut_v1/*`

## Local Validation
- Worker result:
  `l2_decoder_attention_kv_hbm_closed_onchip_schedule_softmax_recip_lut_llama7b_v1_run_23c73d0286366557`
- Summary: `6/6 commands succeeded`.

## Evaluation Request
- Cost class: small analytic L2 campaign.
- Baseline/source:
  `l2_decoder_attention_kv_measured_hbm_service_softmax_recip_lut_llama7b_v1`.
- Next dependent item:
  `l2_decoder_attention_kv_subtile_pipeline_schedule_softmax_recip_lut_llama7b_v1`.

## Risks
- HBM controller area/power remains analytic.
- NoC/queue service remains modeled, not full routed RTL.
- Subtile pipeline benefit still needs evaluation on this softmax-recip source.
