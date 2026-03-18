# Analysis Report

## Candidate
- `proposal_id`: `prop_cross_non_mlp_terminal_suite_v1`
- `candidate_id`: `cand_cross_non_mlp_terminal_suite_v1_r1`

## Evaluations Consumed
- measurement baseline work item:
  `l2_prop_cross_non_mlp_terminal_suite_v1_nm1_measurement_r1`
- measurement baseline run key:
  `l2_prop_cross_non_mlp_terminal_suite_v1_nm1_measurement_r1_run_cf78984dc7672a8b`
- paired candidate work item:
  `l2_prop_cross_non_mlp_terminal_suite_v1_nm1_fused_r1`
- paired candidate run key:
  `l2_prop_cross_non_mlp_terminal_suite_v1_nm1_fused_r1_run_40af2795b96518ef`
- source commits:
  - measurement stage: `69a4a7996f232b8dd9d81e35935da1d21fdb26d1`
  - paired candidate stage: `5db83794f4091d2ccaff6ec6e47f034bf5d2a63c`
- merged evidence PRs:
  - measurement baseline: `#49`
  - paired candidate: `#52`

## Baseline Comparison
- direct comparison used for proposal judgment:
  `runs/campaigns/npu/e2e_eval_onnx_terminal_softmax_suite_submit_nm1_v1__l2_prop_cross_non_mlp_terminal_suite_v1_nm1_measurement_r1/`
  vs
  `runs/campaigns/npu/e2e_eval_onnx_terminal_softmax_suite_fused_output_nm1_v1__l2_prop_cross_non_mlp_terminal_suite_v1_nm1_fused_r1/`
- per-model `flat_nomacro` deltas:
  - `softmax_cls_b128_i4_o128`: latency `0.00587 -> 0.004746 ms`,
    energy `1.08353156e-06 -> 8.760546480000001e-07 mJ`
  - `softmax_cls_b128_i8_o16`: latency `0.0014069999999999996 -> 0.001179 ms`,
    energy `2.5971531600000005e-07 -> 2.1762925199999998e-07 mJ`
  - `softmax_cls_b256_i8_o64`: latency `0.006154 -> 0.00503 ms`,
    energy `1.1359545519999999e-06 -> 9.284776400000002e-07 mJ`
- same direction holds for `hier_macro`
- aggregate means:
  - `flat_nomacro`: latency `0.004476999999999999 -> 0.0036516666666666663 ms`,
    energy `8.26400476e-07 -> 6.740538466666667e-07 mJ`
  - `hier_macro`: latency `0.004476999999999999 -> 0.0036516666666666663 ms`,
    energy `9.0853078e-07 -> 7.4078212e-07 mJ`

## Result
- result: `win`
- confidence level: `high for the bounded terminal-sensitive softmax suite`
- estimated mapper optimization room:
  `low for this fixed-architecture paired comparison`
- architecture conclusion robustness:
  `robust for the current supported softmax-tail family under the corrected event contract`

## Failures and Caveats
- the proposal no longer claims a true non-MLP proof; it intentionally used a
  locally generated softmax-tail suite because the current mapper-supported
  ONNX subset is still `Cast/Gemm/Softmax`-centric
- the accepted result demonstrates generalization beyond the original single
  logistic-regression proof, but still within the same terminal-softmax family
- broader non-MLP or terminal-op-family claims require a separate mapper or
  lowering expansion item
- no accepted-run flow or validation failures remain after the short-SHA and
  model-label export fixes were corrected

## Recommendation
- `promote`
- short reason:
  the merged staged evidence shows fused terminal output improves latency and
  energy across the whole bounded terminal-sensitive softmax suite, not just
  the original single-model proof
- follow-on:
  move next to mapper/lowering work that expands terminal-op support beyond the
  current `Cast/Gemm/Softmax` subset before spending more effort on broader
  ranking sweeps
