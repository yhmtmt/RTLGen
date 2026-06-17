# Analysis Report

## Candidate
- `proposal_id`: `prop_l1_decoder_attention_endpoint_router_segmented_noc_ppa_v1`
- `candidate_id`: pending evaluation

## Evaluations Consumed
- `l2_decoder_attention_kv_endpoint_router_sram_composition_softmax_recip_lut_llama7b_v1_r3`
- source commit: `c68dce07a65dc284ac5ee3051beedd2e06b5c109`

## Baseline Comparison
- Baseline lane primitives: existing `l1_noc_router_p4_w128_wrapper`, `l1_noc_router_p4_w256_wrapper`, `l1_noc_fifo_w128_d16_wrapper`, and `l1_noc_fifo_w256_d16_wrapper`.
- Boundary evidence: flat `l1_noc_router_p4_w2048_wrapper` and `l1_noc_fifo_w2048_d16_wrapper` failed at utilization 40/50/60.

## Result
- Pending L1 sweep.

## Failures and Caveats
- This proposal measures lane primitives only; it does not prove a placed aggregate 2048-bit network wrapper.
- Scheduler and pipeline composition remain L2 follow-on work after lane PPA is refreshed.

## Recommendation
- Run the requested L1 sweep, then re-run composition with segmented or narrower-link NoC interpretation.
