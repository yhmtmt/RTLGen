# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_mapper_terminal_vecop_direct_output_v1`
- `candidate_id`: `cand_l2_mapper_terminal_vecop_direct_output_v1_r1`

## Evaluations Consumed
- measurement baseline work item:
  `l2_prop_l2_mapper_terminal_vecop_direct_output_v1_nm1_measurement_r2`
- measurement baseline run key:
  `l2_prop_l2_mapper_terminal_vecop_direct_output_v1_nm1_measurement_r2_run_eacb4da28b6e09ba`
- paired candidate work item:
  `l2_prop_l2_mapper_terminal_vecop_direct_output_v1_nm1_fused_r1`
- paired candidate run key:
  `l2_prop_l2_mapper_terminal_vecop_direct_output_v1_nm1_fused_r1_run_9ca3905be8de3980`
- source commits:
  - measurement stage: `37d18aae5dba13086d7b15ac57381e6fa719f40f`
  - paired candidate stage: `af4d14017f2568428121ea9c9516c6284ffcc66b`
- merged evidence PRs:
  - measurement baseline: `#58`
  - paired candidate: `#61`

## Baseline Comparison
- direct comparison used for proposal judgment:
  `runs/campaigns/npu/e2e_eval_onnx_terminal_vecop_suite_submit_nm1_v1__l2_prop_l2_mapper_terminal_vecop_direct_output_v1_nm1_measurement_r2/`
  vs
  `runs/campaigns/npu/e2e_eval_onnx_terminal_vecop_suite_fused_nm1_v1__l2_prop_l2_mapper_terminal_vecop_direct_output_v1_nm1_fused_r1/`
- bounded suite covered:
  - `relu_vec_b128_f64`
  - `relu_vec_b256_f256`
  - `relu_vec_flatten_b128_2x4x8`
- per-model `flat_nomacro` deltas:
  - `relu_vec_b128_f64`: latency `0.0022979999999999997 -> 0.001686 ms`,
    energy `4.43794356e-07 -> 3.25603692e-07 mJ`
  - `relu_vec_b256_f256`: latency `0.016634 -> 0.012438 ms`,
    energy `3.212391348e-06 -> 2.402051436e-06 mJ`
  - `relu_vec_flatten_b128_2x4x8`: latency `0.0022979999999999997 -> 0.001686 ms`,
    energy `4.43794356e-07 -> 3.25603692e-07 mJ`
- same improvement direction holds for `hier_macro`
- aggregate means:
  - `flat_nomacro`: latency `0.007076666666666666 -> 0.0052699999999999995 ms`,
    energy `1.36666002e-06 -> 1.01775294e-06 mJ`
  - `hier_macro`: latency `0.007076666666666666 -> 0.0052699999999999995 ms`,
    energy `1.3972241433333337e-06 -> 1.0405146140000003e-06 mJ`

## Result
- result: `win`
- confidence level:
  `high for the bounded standalone terminal Relu vec-op suite on fixed nm1`
- estimated mapper optimization room:
  `low for this specific paired comparison after the bounded direct-output rule was added`
- architecture conclusion robustness:
  `robust for the current first-pass standalone terminal Relu vec-op family on fixed nm1`

## Failures and Caveats
- PR `#57` was superseded because it mixed the valid measurement payload with
  unrelated notebook-side history; PR `#58` is the accepted clean baseline
  evidence boundary
- PR `#60` was superseded because it exported the paired candidate before the
  merged baseline evidence had been reconciled and materialized; PR `#61` is
  the accepted clean paired-comparison evidence boundary
- the accepted result is intentionally bounded to a standalone terminal `Relu`
  vec-op family on fixed `fp16_nm1`; it is not yet a claim about broader
  activation support or cross-architecture ranking
- the work exposed a real workflow gap in staged developer-loop dependencies,
  now addressed by explicit dependency gating for dependent evaluation items

## Recommendation
- `promote`
- short reason:
  the merged staged evidence shows bounded terminal vec-op direct-output
  lowering improving latency and energy across the whole standalone terminal
  `Relu` suite against the refreshed non-fused baseline
- follow-on:
  move next to broader terminal vec-op or activation-family expansion under the
  new dependency-ordered evaluation model before reopening wider ranking
