## Summary
- item_id: `l2_prop_cross_non_mlp_terminal_suite_v1_nm1_measurement_r1`
- run_key: `l2_prop_cross_non_mlp_terminal_suite_v1_nm1_measurement_r1_run_cf78984dc7672a8b`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `5/5 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_prop_cross_non_mlp_terminal_suite_v1_nm1_measurement_r1/evaluated.json`
- metrics_rows_count: `6`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_prop_cross_non_mlp_terminal_suite_v1_nm1_measurement_r1.json`

## Developer Context
- proposal_id: `prop_cross_non_mlp_terminal_suite_v1`
- proposal_path: `docs/developer_loop/prop_cross_non_mlp_terminal_suite_v1`
- reviewer_first_read: `docs/developer_loop/prop_cross_non_mlp_terminal_suite_v1` plus `docs/developer_agent_review.md`

## Evaluation Mode
- evaluation_mode: `measurement_only`
- comparison_role: `measurement_only`
- expected_direction: `unknown`
- expected_reason: `Record corrected-contract non-fused nm1 reference metrics for the terminal-sensitive softmax-tail suite before any fused comparison.`
- expectation_status: `not_applicable`
- evaluation_summary: `This item records metrics for the requested architecture point and does not emit a proposal judgment.`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
