# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_mapper_terminal_activation_family_v1`
- `candidate_id`: pending downstream of `prop_l1_npu_nm1_sigmoid_vec_enable_v1`

## Evaluations Consumed
- accepted prerequisite:
  - standalone sigmoid wrapper from `prop_l1_terminal_sigmoid_block_v1`
- active prerequisite still not accepted:
  - integrated sigmoid-enabled `nm1` block from
    `prop_l1_npu_nm1_sigmoid_vec_enable_v1`

## Baseline Comparison
- the activation-family mapper work remains blocked until an integrated `nm1`
  sigmoid physical source is accepted
- recent integrated attempts show the blocker is physical-flow practicality, not
  sigmoid arithmetic legality

## Result
- result: blocked_on_l1
- confidence level: medium
- estimated mapper optimization room: still promising if the integrated source
  can be established
- architecture conclusion robustness: not yet evaluable

## Failures and Caveats
- no Layer 2 sigmoid-family campaign should be queued from the current full-top
  integrated `nm1` attempt until the Layer 1 source is accepted
- the immediate enabling work is control-plane long-run handling and/or a
  smaller integrated physical proof target

## Recommendation
- keep the Layer 2 sigmoid-family proposal blocked
- finish `prop_l1_npu_nm1_sigmoid_vec_enable_v1` first under improved
  long-running sweep controls
