## Summary
- item_id: `l2_decoder_pwl_frontier_detail_v1`
- run_key: `l2_decoder_pwl_frontier_detail_v1_run_127cfe1326f30a3c`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_pwl_frontier_detail_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_pwl_frontier_detail_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_pwl_frontier_detail_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_pwl_frontier_detail_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_pwl_frontier_detail_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `5d190fce1ad1b3931620cd7b3db5271cb3e8ded0`
- review_metadata_source_commit: `5d190fce1ad1b3931620cd7b3db5271cb3e8ded0`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_pwl_frontier_detail`
- comparison_role: `ranking`
- expected_direction: `iterate`
- expected_reason: `Explain whether bf16 PWL remains the immediate anchor and whether q8 PWL is blocked mainly by exact normalization cost.`
- expectation_status: `unspecified`
- evaluation_summary: `Focused comparison baseline could not be resolved from proposal baseline_refs.`

## Focused Comparison
- primary_question: `Between grid_approx_pwl_bf16_path and grid_approx_pwl_in_q8_w_q8_norm_exact, which path should be the immediate implementation anchor and what remains the open risk?`
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
