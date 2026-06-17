# Implementation Summary

## Proposal
- `proposal_id`: `prop_l2_decoder_attention_kv_subtile_pipeline_schedule_softmax_recip_lut_v1`
- title: Softmax-recip subtile pipeline schedule

## Scope
- Generated and ran
  `l2_decoder_attention_kv_subtile_pipeline_schedule_softmax_recip_lut_llama7b_v1`.
- Consumed the merged softmax-recip HBM-closed on-chip schedule artifact.
- Produced the subtile pipeline schedule artifact for the softmax-recip path.

## Files Changed
- `runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_subtile_pipeline_schedule__l2_decoder_attention_kv_subtile_pipeline_schedule_softmax_recip_lut_llama7b_v1.json`
- `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_kv_subtile_pipeline_schedule_softmax_recip_lut_llama7b_v1.json`
- `docs/proposals/prop_l2_decoder_attention_kv_subtile_pipeline_schedule_softmax_recip_lut_v1/*`

## Local Validation
- Worker result:
  `l2_decoder_attention_kv_subtile_pipeline_schedule_softmax_recip_lut_llama7b_v1_run_6364ceb1a3b8a12f`
- Summary: `6/6 commands succeeded`.

## Evaluation Request
- Cost class: small analytic L2 campaign.
- Baseline/source:
  `l2_decoder_attention_kv_hbm_closed_onchip_schedule_softmax_recip_lut_llama7b_v1`.

## Risks
- `compute_mode=dual_mac` improves latency but still needs explicit area
  accounting or a measured partitioned datapath.
- The schedule model remains analytic and should be validated by a more concrete
  pipeline RTL or microarchitecture model.
