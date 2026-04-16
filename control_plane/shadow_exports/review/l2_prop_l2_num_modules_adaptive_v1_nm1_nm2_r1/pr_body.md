## Summary
- item_id: `l2_prop_l2_num_modules_adaptive_v1_nm1_nm2_r1`
- run_key: `l2_prop_l2_num_modules_adaptive_v1_nm1_nm2_r1_run_31d1b3461690b595`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `5/5 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_prop_l2_num_modules_adaptive_v1_nm1_nm2_r1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_prop_l2_num_modules_adaptive_v1_nm1_nm2_r1.json`

## Developer Context
- proposal_id: `prop_l2_num_modules_adaptive_v1`
- proposal_path: `docs/proposals/prop_l2_num_modules_adaptive_v1`
- execution_source_commit: `6f6a3231a9abbb80a825beec987b4263d19dcb86`
- review_metadata_source_commit: `ba899ed0e593e1b8ba56739fca6ada1d9e7ce8de`
- reviewer_first_read: `docs/proposals/prop_l2_num_modules_adaptive_v1` plus `docs/developer_agent_review.md`

## Evaluation Mode
- evaluation_mode: `broad_ranking`
- comparison_role: `ranking`
- expected_direction: `unknown`
- expectation_status: `unspecified`
- evaluation_summary: `Focused comparison regressed latency and/or energy versus the matched baseline rows.`

## Focused Comparison
- primary_question: `After the accepted mapper update, does the imported softmax-tail benchmark still clearly prefer nm1 over nm2, or has the module-count conclusion become benchmark- or lowering-dependent?`
- comparison_role: `ranking`
- proposal_outcome: `regressed`
- comparison_summary: `Focused comparison regressed latency and/or energy versus the matched baseline rows.`
- baseline_ref: `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_num_modules_v1`
- latency_delta fp16_nm1/flat_nomacro/logistic_regression: `0.000621` -> `0.0009677500000000001` ms
- energy_delta fp16_nm1/flat_nomacro/logistic_regression: `1.19928762e-07` -> `1.868938155e-07` mJ

## Submission Recovery
- submission_failure_count: `0`
- retry_request_count: `0`
- final_submission_pr: `https://github.com/yhmtmt/RTLGen/pull/210`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
