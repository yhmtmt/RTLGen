# Implementation Summary

## Proposal
- `proposal_id`: `prop_l2_decoder_attention_kv_endpoint_router_sram_composition_softmax_recip_lut_v1`
- endpoint/router/SRAM composition for the reciprocal-LUT Llama7B frontier

## Scope
- Request a composition audit after the reciprocal-LUT ready/valid endpoint result.
- Do not replace HBM/DRAM service in this step.

## Files Changed
- proposal documentation

## Local Validation
- generator routing was validated in PR #884 before dispatch.

## Evaluation Request
- requested item: `l2_decoder_attention_kv_endpoint_router_sram_composition_softmax_recip_lut_llama7b_v1`
- cost class: low
- baseline/source: reciprocal-LUT ready/valid endpoint result

## Risks
- The audit may require additional L1 endpoint/router/FIFO/SRAM PPA runs.
- HBM/DRAM remains inherited.
