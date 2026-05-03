## Summary
- item_id: `l2_llm_practical_scale_v1`
- run_key: `l2_llm_practical_scale_v1_run_222ec317f138e8ce`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `5/5 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_llm_practical_scale_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_llm_practical_scale_v1.json`

## Developer Context
- proposal_id: `prop_l2_llm_practical_scale_v1`
- proposal_path: `docs/proposals/prop_l2_llm_practical_scale_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_llm_practical_scale_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `f8465990cb830dc9ac6fc6094b18e2659aae6450`
- review_metadata_source_commit: `f8465990cb830dc9ac6fc6094b18e2659aae6450`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `llm_practical_scale`
- comparison_role: `ranking`
- expected_direction: `iterate`
- expected_reason: `Use the larger practical proxy result to decide whether wider compute-array work is justified or whether precision/quality exploration should remain the frontier.`
- expectation_status: `unspecified`
- evaluation_summary: `Focused comparison baseline could not be resolved from proposal baseline_refs.`

## Focused Comparison
- comparison_role: `ranking`
- proposal_outcome: `unavailable`
- comparison_summary: `Focused comparison baseline could not be resolved from proposal baseline_refs.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
