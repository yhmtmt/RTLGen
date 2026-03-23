# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_mapper_terminal_activation_family_v1`
- `candidate_id`: pending first Layer 2 measurement item

## Evaluations Consumed
- accepted lower-layer prerequisites:
  - standalone sigmoid wrapper from `prop_l1_terminal_sigmoid_block_v1` / PR `#63`
  - integrated sigmoid-enabled `nm1` architecture-block source from `prop_l1_npu_nm1_sigmoid_vec_enable_v1` / PR `#74`

## Baseline Comparison
- the activation-family mapper work is no longer blocked on lower-layer physical grounding
- the accepted integrated source is the reduced proxy `npu_fp16_cpp_nm1_sigmoidproxy`, which is sufficient to ground the next bounded Layer 2 measurement-first campaign
- no Layer 2 activation-family campaign has run yet, so there is still no direct-output judgment for this proposal

## Result
- result: ready_for_measurement
- confidence level: medium
- estimated mapper optimization room: still promising for a bounded nonlinear family on fixed `nm1`
- architecture conclusion robustness: not yet evaluable until the first Layer 2 bounded nonlinear activation reference suite is measured

## Failures and Caveats
- the accepted integrated physical source is a reduced `architecture_block` proxy rather than full `npu_top`
- that is sufficient for this staged bounded Layer 2 follow-on, but it should not be overstated as a full-top architecture ranking result
- the next campaign should remain tightly bounded and measurement-first

## Recommendation
- keep the proposal active and unblocked
- queue `l2_prop_l2_mapper_terminal_activation_family_v1_nm1_measurement_r1` next
- keep the paired comparison dependency-gated on the merged/materialized measurement baseline
