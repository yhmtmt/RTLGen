# Analysis Report

## Candidate
- `proposal_id`: `prop_l1_decoder_bf16_recip_norm_datapath_v1`
- `candidate_id`: `l1_decoder_bf16_recip_norm_datapath_v1_r2`

## Evaluations Consumed
- `l1_decoder_bf16_recip_norm_datapath_v1_r2`
- `l1_decoder_bf16_recip_norm_datapath_v1_r2_run_78aed7d4bbe695a5`
- source commit: `604d30b4165ef8b79b16997782979e7313735615`

## Result
- result: `promote`
- confidence level: accepted L1 physical metrics
- best row: `bf16_recip_norm_nangate45_highutil_2ae5d3c9`
- critical path: `4.2869 ns`
- die area: `50690.271025`
- total power: `0.00479 mW`

## Interpretation
The bf16 reciprocal-normalization datapath is substantially larger and slower
than the q8 reciprocal-normalization datapath, which is expected because this
block includes packed-bf16 fixed-point conversion, a reciprocal LUT, multiply,
rounding/clamp logic, and bf16 output reconstruction. The result should be
used as measured PPA evidence for the bf16 normalization row, not as a complete
decoder-softmax macro cost.

## Caveats
- The datapath clamps unsupported IEEE cases.
- Timing did not close at 2.5 ns; the metric records the achieved critical
  path from the accepted OpenROAD run.
- The measurement remains distribution-independent hardware evidence. It does
  not answer quality sensitivity to bf16 or q8 approximation choices.

## Recommendation
- `promote`
- reason: accepted Layer 1 physical metrics were produced for the bf16
  reciprocal-normalization datapath.
- next_action: update the decoder q8 normalization frontier estimator to load
  this artifact and rerun the comparable-dimension quantization outline.
