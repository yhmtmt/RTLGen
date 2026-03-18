# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_mapper_terminal_op_generalization_v1`
- `candidate_id`: `cand_l2_mapper_terminal_op_generalization_v1_r1`

## Evaluations Consumed
- measurement baseline work item:
  `l2_prop_l2_mapper_terminal_op_generalization_v1_nm1_measurement_r1`
- measurement baseline run key:
  `l2_prop_l2_mapper_terminal_op_generalization_v1_nm1_measurement_r1_run_8308af94f8150433`
- paired candidate work item:
  `l2_prop_l2_mapper_terminal_op_generalization_v1_nm1_fused_r1`
- paired candidate run key:
  `l2_prop_l2_mapper_terminal_op_generalization_v1_nm1_fused_r1_run_baa0b349b4e529b5`
- source commits:
  - measurement stage: `fec11e31cc03c66e7e053b823621912977abb8a6`
  - paired candidate stage: `f111f8cd99a77f455c4d4cc0f87d144033fe2c4b`
- merged evidence PRs:
  - measurement baseline: `#54`
  - paired candidate: `#56`

## Baseline Comparison
- direct comparison used for proposal judgment:
  `runs/campaigns/npu/e2e_eval_onnx_terminal_direct_output_suite_submit_nm1_v1__l2_prop_l2_mapper_terminal_op_generalization_v1_nm1_measurement_r1/`
  vs
  `runs/campaigns/npu/e2e_eval_onnx_terminal_direct_output_suite_fused_nm1_v1__l2_prop_l2_mapper_terminal_op_generalization_v1_nm1_fused_r1/`
- per-model `flat_nomacro` deltas:
  - `linear_tail_b128_f8_o64`: latency `0.002278 -> 0.001666 ms`,
    energy `4.39931916e-07 -> 3.21741252e-07 mJ`
  - `linear_tail_b256_f8_o128`: latency `0.0071779999999999995 -> 0.00503 ms`,
    energy `1.386229716e-06 -> 9.7140366e-07 mJ`
  - `relu_tail_b128_f8_o128`: latency `0.003914 -> 0.0027900000000000004 ms`,
    energy `7.55879508e-07 -> 5.3881038e-07 mJ`
- same improvement direction holds for `hier_macro`
- aggregate means:
  - `flat_nomacro`: latency `0.004456666666666667 -> 0.003162 ms`,
    energy `8.6068038e-07 -> 6.10651764e-07 mJ`
  - `hier_macro`: latency `0.004456666666666667 -> 0.003162 ms`,
    energy `8.799287233333336e-07 -> 6.243084420000001e-07 mJ`

## Result
- result: `win`
- confidence level:
  `high for the bounded terminal linear plus terminal Relu family on fixed nm1`
- estimated mapper optimization room:
  `low for this specific paired comparison after the bounded direct-output rule was added`
- architecture conclusion robustness:
  `robust for the current first-pass terminal linear plus terminal Relu family on the corrected evaluation contract`

## Failures and Caveats
- the accepted result is intentionally bounded to terminal linear plus terminal
  `Relu` on fixed `fp16_nm1`; it is not yet a claim about broader terminal-op
  support or cross-architecture ranking
- the work uncovered and corrected two tooling issues during review:
  missing multimodel evidence export and over-truncated suite summaries in PR
  bodies; neither remains a blocker in the accepted evidence
- broader terminal-op families such as vector-only tails or additional terminal
  activations remain out of scope for this proposal
- no accepted-run legality or review-payload gaps remain after PRs `#54` and
  `#56`

## Recommendation
- `promote`
- short reason:
  the merged staged evidence shows the generalized direct-output lowering
  improves latency and energy across the whole bounded terminal linear plus
  terminal `Relu` suite against the refreshed non-fused baseline
- follow-on:
  move next to mapper/lowering expansion for broader terminal-op families
  before reopening broader architecture ranking or `nm1`/`nm2` comparisons
