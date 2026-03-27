## Summary
- item_id: `l2_prop_l2_mapper_terminal_relu6_direct_output_v1_nm1_fused_r1`
- run_key: `l2_prop_l2_mapper_terminal_relu6_direct_output_v1_nm1_fused_r1_run_5ae554d9168cdc7b`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `5/5 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_prop_l2_mapper_terminal_relu6_direct_output_v1_nm1_fused_r1/evaluated.json`
- metrics_rows_count: `1`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_prop_l2_mapper_terminal_relu6_direct_output_v1_nm1_fused_r1.json`

## Developer Context
- proposal_id: `prop_l2_mapper_terminal_relu6_direct_output_v1`
- proposal_path: `docs/developer_loop/prop_l2_mapper_terminal_relu6_direct_output_v1`
- reviewer_first_read: `docs/developer_loop/prop_l2_mapper_terminal_relu6_direct_output_v1` plus `docs/developer_agent_review.md`

## Evaluation Mode
- evaluation_mode: `paired_comparison`
- comparison_role: `candidate`
- expected_direction: `unknown`
- expectation_status: `unspecified`
- evaluation_summary: `Focused comparison baseline could not be resolved from proposal baseline_refs.`

## Focused Comparison
- primary_question: `Does bounded terminal ReLU6 direct vec-op output improve latency and energy on fixed nm1 against the non-fused baseline?`
- comparison_role: `candidate`
- proposal_outcome: `unavailable`
- comparison_summary: `Focused comparison baseline could not be resolved from proposal baseline_refs.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
