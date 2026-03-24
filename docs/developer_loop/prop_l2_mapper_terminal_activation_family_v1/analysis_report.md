# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_mapper_terminal_activation_family_v1`
- `candidate_id`: `cand_l2_mapper_terminal_activation_family_v1_r1`

## Evaluations Consumed
- accepted lower-layer prerequisites:
  - standalone sigmoid wrapper from `prop_l1_terminal_sigmoid_block_v1` / PR `#63`
  - integrated sigmoid-enabled `nm1` architecture-block source from `prop_l1_npu_nm1_sigmoid_vec_enable_v1` / PR `#74`
- accepted Layer 2 measurement baseline:
  - work item: `l2_prop_l2_mapper_terminal_activation_family_v1_nm1_measurement_r1`
  - run key: `l2_prop_l2_mapper_terminal_activation_family_v1_nm1_measurement_r1_run_8b59dfa21c40c9c5`
  - merged evidence PR: `#75`
  - source commit under test: `b3c45a2842671dafa41730d15b840aff69c538b2`

## Baseline Comparison
- the activation-family mapper work is no longer blocked on lower-layer physical grounding
- the accepted integrated source remains the reduced proxy `npu_fp16_cpp_nm1_sigmoidproxy`, which is sufficient to ground this bounded Layer 2 measurement-first campaign
- the bounded first-pass suite now has accepted non-fused reference evidence for:
  - `sigmoid_vec_b128_f64`
  - `sigmoid_vec_b256_f256`
  - `sigmoid_vec_flatten_b128_2x4x8`
- aggregate accepted means on `fp16_nm1_sigmoidproxy` / `hier_macro`:
  - latency: `0.007076666666666666 ms`
  - energy: `2.5476e-09 mJ`
  - critical path: `2.7883 ns`
  - die area: `1440000.0 um^2`
  - total power: `0.00036 mW`
- no direct-output candidate has run yet, so there is still no proposal judgment on win/loss for sigmoid direct output

## Result
- result: `baseline_accepted`
- confidence level: `medium`
- estimated mapper optimization room: `still promising for a bounded nonlinear family on fixed nm1`
- architecture conclusion robustness: `not yet evaluable until the paired direct-output candidate is measured against this accepted baseline`

## Failures and Caveats
- the accepted integrated physical source is a reduced `architecture_block` proxy rather than full `npu_top`
- that is sufficient for this staged bounded Layer 2 follow-on, but it should not be overstated as a full-top architecture ranking result
- the accepted result is only a `measurement_only` baseline; it does not answer the direct-output hypothesis yet
- the paired direct-output campaign is still missing as a tracked implementation artifact and must be added before the next queue step

## Recommendation
- `iterate`
- short reason:
  accept the bounded sigmoid-first non-fused baseline and move next to the paired direct-output candidate on the same suite
- follow-on:
  implement and queue `l2_prop_l2_mapper_terminal_activation_family_v1_nm1_fused_r1` with the merged/materialized `r1` baseline as its required dependency
