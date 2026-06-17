# Quality Gate

## Proposal
- `proposal_id`: `prop_l2_decoder_attention_kv_endpoint_router_sram_composition_softmax_recip_lut_v1`
- `title`: `Endpoint/router/SRAM composition for reciprocal-LUT Llama7B frontier`

## Why This Gate Is Required
The result determines whether the on-chip endpoint/router/SRAM path can be
treated as compositionally closed for the selected q12 Llama7B frontier.

## Reference
- baseline_ref: `l2_decoder_attention_kv_endpoint_ready_valid_service_softmax_recip_lut_llama7b_v1`
- reference_ref: corrected q12 endpoint full on-chip service r2 result

## Checks
- metric: composition_audit_completed
  - threshold: true
- metric: remaining_l1_ppa_gaps
  - threshold: reported

## Local Commands
- command: generated L2 campaign task command

## Result
- status: pending
- note: awaiting evaluator result
