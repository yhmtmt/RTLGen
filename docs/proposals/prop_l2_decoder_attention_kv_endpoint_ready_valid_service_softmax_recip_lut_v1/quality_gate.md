# Quality Gate

## Proposal
- `proposal_id`: `prop_l2_decoder_attention_kv_endpoint_ready_valid_service_softmax_recip_lut_v1`
- `title`: `Ready/valid endpoint service for reciprocal-LUT Llama7B frontier`

## Why This Gate Is Required
The result determines whether the endpoint queue/backpressure part of the
selected frontier can be treated as concrete enough for the follow-on
endpoint/router/SRAM composition audit.

## Reference
- baseline_ref: `l2_decoder_attention_kv_endpoint_full_onchip_service_schedule_softmax_recip_lut_llama7b_v1_r2`
- reference_ref: prior non-recip-LUT ready/valid endpoint service

## Checks
- metric: ready_valid_probe_completed
  - threshold: true
- metric: endpoint_backpressure_reported
  - threshold: present

## Local Commands
- command: generated L2 campaign task command

## Result
- status: pending
- note: awaiting evaluator result
