# Implementation Summary

## Proposal
- `proposal_id`: `prop_l2_decoder_attention_kv_endpoint_ready_valid_service_softmax_recip_lut_v1`
- ready/valid endpoint service for the reciprocal-LUT Llama7B frontier

## Scope
- Request a concrete endpoint ready/valid probe for the corrected q12 reciprocal-LUT frontier.
- Do not change topology, compute array, HBM service, or SRAM sizing in this step.

## Files Changed
- proposal documentation
- generated L2 work item after dispatch

## Local Validation
- generator routing was validated in PR #884 before dispatch

## Evaluation Request
- requested item: `l2_decoder_attention_kv_endpoint_ready_valid_service_softmax_recip_lut_llama7b_v1`
- cost class: low
- baseline/source: `l2_decoder_attention_kv_endpoint_full_onchip_service_schedule_softmax_recip_lut_llama7b_v1_r2`

## Risks
- The evaluator must use source commit `20959c07` or newer.
- The router/SRAM composition audit remains a separate closure step.
