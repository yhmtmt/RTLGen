## Summary
- item_id: `l2_prop_l2_mapper_terminal_hardtanh_direct_output_v1_nm1_measurement_r3`
- run_key: `l2_prop_l2_mapper_terminal_hardtanh_direct_output_v1_nm1_measurement_r3_run_442ab23d904cb459`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `5/5 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_prop_l2_mapper_terminal_hardtanh_direct_output_v1_nm1_measurement_r3/evaluated.json`
- metrics_rows_count: `1`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_prop_l2_mapper_terminal_hardtanh_direct_output_v1_nm1_measurement_r3.json`

## Developer Context
- proposal_id: `prop_l2_mapper_terminal_hardtanh_direct_output_v1`
- proposal_path: `docs/proposals/prop_l2_mapper_terminal_hardtanh_direct_output_v1`
- reviewer_first_read: `docs/proposals/prop_l2_mapper_terminal_hardtanh_direct_output_v1` plus `docs/developer_agent_review.md`

## Evaluation Mode
- evaluation_mode: `measurement_only`
- abstraction_layer: `full_architecture`
- comparison_role: `measurement_only`
- expected_direction: `unknown`
- expected_reason: `maintenance-loop split proof baseline retry`
- expectation_status: `not_applicable`
- evaluation_summary: `This item records metrics for the requested architecture point and does not emit a proposal judgment.`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
