# Analysis Report

## Candidate
- `proposal_id`: `prop_l1_decoder_q8_recip_norm_datapath_v1`
- `candidate_id`: `l1_decoder_q8_recip_norm_datapath_v1`

## Evaluations Consumed
- pending L1 measurement

## Baseline Comparison
- baseline primitive calibration: `prop_l1_decoder_normalization_arithmetic_calibration_v1`
- baseline q8 frontier: `prop_l2_decoder_q8_normalization_frontier_v1`

## Result
- result: pending
- confidence level: implementation prepared, remote physical measurement not yet consumed
- architecture conclusion robustness: pending q10/q12/q14/q16 integrated PPA rows

## Failures and Caveats
- no remote evaluation evidence has been consumed yet
- bf16 reciprocal/multiply datapaths remain outside this proposal

## Recommendation
- `iterate`
- reason: Merge RTLGen support first, then queue the L1 measurement item from the merged commit.
