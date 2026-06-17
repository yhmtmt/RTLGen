# Quality Gate

## Proposal
- `proposal_id`: `prop_l2_decoder_attention_kv_dual_stream_physical_feasibility_softmax_recip_lut_v1`
- `title`: Softmax-recip dual-stream physical feasibility

## Why This Gate Is Required
This item does not change numerical precision. It prevents a schedule-only
dual-MAC latency from being promoted without physical area feasibility.

## Reference
- baseline_ref:
  `runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_subtile_pipeline_schedule__l2_decoder_attention_kv_subtile_pipeline_schedule_softmax_recip_lut_llama7b_v1.json`
- result_ref:
  `runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_dual_stream_physical_feasibility__l2_decoder_attention_kv_dual_stream_physical_feasibility_softmax_recip_lut_llama7b_v1.json`

## Checks
- metric: `dual_mac` area fit
  - threshold: must not be promoted if `area_fit=false`
- metric: feasible fallback
  - threshold: record best `physical_feasible=true` row

## Local Commands
- command: worker run completed with `6/6 commands succeeded`

## Result
- status: pass
- note: Dual-MAC is area-blocked; split-MAC is the valid current frontier.
