# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_num_modules_adaptive_v1`
- `candidate_id`: `l2_prop_l2_num_modules_adaptive_v1_nm1_nm2_r1`

## Evaluations Consumed
- `l2_prop_l2_num_modules_adaptive_v1_nm1_nm2_r1`
- `l2_prop_l2_num_modules_adaptive_v1_nm1_nm2_r1_run_31d1b3461690b595`
- source commit: `6f6a3231a9abbb80a825beec987b4263d19dcb86`
- review: PR #212

## Baseline Comparison
- baseline_ref: `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_num_modules_v1`
- outcome: `regressed`
- summary: Focused comparison regressed latency and/or energy versus the matched baseline rows.

## Result
- result: `iterate`
- confidence level: merged accepted evidence
- estimated optimization room: pending follow-on comparison
- architecture conclusion robustness: staged evidence
- summary: Focused comparison regressed latency and/or energy versus the matched baseline rows.

## Failures and Caveats
- no additional caveats recorded during automatic finalization

## Recommendation
- `iterate`
- reason: Focused comparison regressed latency and/or energy versus the matched baseline rows.
- next_action: inspect follow-on work after l2_prop_l2_num_modules_adaptive_v1_nm1_nm2_r1
