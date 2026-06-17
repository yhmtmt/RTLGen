# Quality Gate

## Proposal
- `proposal_id`: `prop_l2_decoder_attention_kv_hbm_closed_onchip_schedule_softmax_recip_lut_v1`
- `title`: Softmax-recip HBM-closed on-chip schedule closure

## Why This Gate Is Required
This item does not change numerical precision or model quality. It only changes
the schedule model source for the softmax-recip Llama7B attention frontier.

## Reference
- baseline_ref:
  `runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_measured_hbm_service__l2_decoder_attention_kv_measured_hbm_service_softmax_recip_lut_llama7b_v1.json`
- result_ref:
  `runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_hbm_closed_onchip_schedule__l2_decoder_attention_kv_hbm_closed_onchip_schedule_softmax_recip_lut_llama7b_v1.json`

## Checks
- metric: source artifact is the softmax-recip measured-HBM artifact
  - threshold: required path appears in the decoder contract
- metric: numerical quality assumptions
  - threshold: unchanged from source

## Local Commands
- command: worker run completed with `6/6 commands succeeded`

## Result
- status: pass
- note: The frontier remains a schedule/performance estimate; numerical quality is inherited.
