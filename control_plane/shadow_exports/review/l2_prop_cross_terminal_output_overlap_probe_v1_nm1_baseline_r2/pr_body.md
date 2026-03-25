## Summary
- item_id: `l2_prop_cross_terminal_output_overlap_probe_v1_nm1_baseline_r2`
- run_key: `l2_prop_cross_terminal_output_overlap_probe_v1_nm1_baseline_r2_run_99f5bf377842ef74`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `5/5 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_prop_cross_terminal_output_overlap_probe_v1_nm1_baseline_r2/evaluated.json`
- metrics_rows_count: `6`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_prop_cross_terminal_output_overlap_probe_v1_nm1_baseline_r2.json`

## Developer Context
- proposal_id: `prop_cross_terminal_output_overlap_probe_v1`
- proposal_path: `docs/developer_loop/prop_cross_terminal_output_overlap_probe_v1/proposal.json`
- reviewer_first_read: `docs/developer_loop/prop_cross_terminal_output_overlap_probe_v1/proposal.json` plus `docs/developer_agent_review.md`

## Evaluation Mode
- evaluation_mode: `measurement_only`
- comparison_role: `measurement_only`
- expected_direction: `unknown`
- expected_reason: `Record the non-fused softmax-tail baseline on the corrected event contract before the focused fused comparison.`
- expectation_status: `not_applicable`
- evaluation_summary: `This item records metrics for the requested architecture point and does not emit a proposal judgment.`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
