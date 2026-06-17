# Analysis Report

## Candidate
- `proposal_id`: `prop_l1_decoder_attention_dual_stream_composed_q12_pwl_softmax_v1`
- `candidate_id`: `l1_decoder_attention_dual_stream_composed_q12_pwl_softmax_ppa_v1`

## Evaluations Consumed
- Pending: this proposal creates the PPA item.

## Baseline Comparison
- Baseline PPA: `l1_decoder_attention_dual_stream_composed_softmax_recip_lut_ppa_v1_r3`
- Baseline L2 schedule substitution: `l2_decoder_attention_composed_datapath_recip_lut_variant_frontier_llama7b_v1`

## Result
- Pending evaluation.

## Failures and Caveats
- The q8 S8/W8 reciprocal-LUT composed point remains PPA-best but quality-risky under the current proxy.
- This q12/PWL point is intended to measure the concrete physical cost of reducing that softmax precision risk.

## Recommendation
- Dispatch the L1 PPA item after merge.
