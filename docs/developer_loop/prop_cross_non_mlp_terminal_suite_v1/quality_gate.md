# Quality Gate

## Proposal
- `proposal_id`: `prop_cross_non_mlp_terminal_suite_v1`
- `title`: `Non-MLP terminal-op suite`

## Why This Gate Is Required
- the selected suite stayed within imported-style softmax-tail graphs, so no
  new numerical-risk gate beyond the accepted fused/non-fused mechanism proof
  was required for this stage

## Reference
- baseline_ref:
  - `runs/campaigns/npu/e2e_eval_onnx_terminal_softmax_suite_submit_nm1_v1__l2_prop_cross_non_mlp_terminal_suite_v1_nm1_measurement_r1/report.md`
  - `runs/campaigns/npu/e2e_eval_onnx_terminal_softmax_suite_fused_output_nm1_v1__l2_prop_cross_non_mlp_terminal_suite_v1_nm1_fused_r1/report.md`

## Checks
- relied on the previously accepted corrected-contract event semantics and
  fused/non-fused schedule legality checks
- no additional model-quality gate was required for this bounded suite

## Local Commands
- none

## Result
- not_required
