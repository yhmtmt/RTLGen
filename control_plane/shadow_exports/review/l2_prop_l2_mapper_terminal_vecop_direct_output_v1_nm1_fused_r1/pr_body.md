## Summary
- item_id: `l2_prop_l2_mapper_terminal_vecop_direct_output_v1_nm1_fused_r1`
- run_key: `l2_prop_l2_mapper_terminal_vecop_direct_output_v1_nm1_fused_r1_run_9ca3905be8de3980`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `5/5 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_prop_l2_mapper_terminal_vecop_direct_output_v1_nm1_fused_r1/evaluated.json`
- metrics_rows_count: `12`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_prop_l2_mapper_terminal_vecop_direct_output_v1_nm1_fused_r1.json`

## Developer Context
- proposal_id: `prop_l2_mapper_terminal_vecop_direct_output_v1`
- proposal_path: `docs/developer_loop/prop_l2_mapper_terminal_vecop_direct_output_v1/proposal.json`
- reviewer_first_read: `docs/developer_loop/prop_l2_mapper_terminal_vecop_direct_output_v1/proposal.json` plus `docs/developer_agent_review.md`

## Evaluation Mode
- evaluation_mode: `paired_comparison`
- comparison_role: `candidate`
- expected_direction: `better_than_historical`
- expected_reason: `Direct terminal vec-op output should reduce the final writeback tail on at least part of the bounded standalone terminal ReLU suite.`
- expectation_status: `unexpected`
- evaluation_summary: `Paired baseline item could not be resolved for focused candidate comparison.`

## Focused Comparison
- primary_question: `Can a bounded terminal vec-op family establish clean nm1 reference points first, then show a direct-output win on those same points without reopening broader ranking?`
- comparison_role: `candidate`
- proposal_outcome: `unavailable`
- comparison_summary: `Paired baseline item could not be resolved for focused candidate comparison.`
- baseline_ref: `None`
- baseline_item_id: `l2_prop_l2_mapper_terminal_vecop_direct_output_v1_nm1_measurement_r2`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
