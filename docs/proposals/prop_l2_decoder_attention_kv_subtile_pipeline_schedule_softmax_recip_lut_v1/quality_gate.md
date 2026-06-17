# Quality Gate

## Proposal
- `proposal_id`: `prop_l2_decoder_attention_kv_subtile_pipeline_schedule_softmax_recip_lut_v1`
- `title`: Softmax-recip subtile pipeline schedule

## Why This Gate Is Required
This item changes scheduling assumptions, not precision. Numerical quality is
inherited from the softmax-recip path, but online correction remains an
assumption that should be validated before promotion to a final architecture.

## Reference
- baseline_ref:
  `runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_hbm_closed_onchip_schedule__l2_decoder_attention_kv_hbm_closed_onchip_schedule_softmax_recip_lut_llama7b_v1.json`
- result_ref:
  `runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_subtile_pipeline_schedule__l2_decoder_attention_kv_subtile_pipeline_schedule_softmax_recip_lut_llama7b_v1.json`

## Checks
- metric: stream buffer fit
  - threshold: `required_stream_buffer_bytes <= available_local_capacity_bytes`
- metric: numerical precision
  - threshold: unchanged from the softmax-recip source path

## Local Commands
- command: worker run completed with `6/6 commands succeeded`

## Result
- status: pass-with-caveat
- note: Schedule fits measured local capacity; online correction still needs numerical validation.
