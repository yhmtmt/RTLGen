## Summary
- item_id: `l2_decoder_output_projection_weight_fetch_wrapper_v1`
- run_key: `l2_decoder_output_projection_weight_fetch_wrapper_v1_run_bc11f29ede609ac3`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_output_projection_weight_fetch_wrapper_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_output_projection_weight_fetch_wrapper_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_output_projection_weight_fetch_wrapper_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_output_projection_weight_fetch_wrapper_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_output_projection_weight_fetch_wrapper_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `9f11b0f4b1cf60ac956d313b262630c137a2b406`
- review_metadata_source_commit: `9f11b0f4b1cf60ac956d313b262630c137a2b406`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_output_projection_weight_fetch_wrapper`
- comparison_role: `weight_fetch_contract`
- expected_direction: `iterate`
- expected_reason: `If producer-side request/throttle behavior matches perf-sim, queue a measured bounded physical wrapper for control logic while keeping resident storage as macro/proxy.`
- expectation_status: `unspecified`
- evaluation_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`

## Focused Comparison
- comparison_role: `weight_fetch_contract`
- proposal_outcome: `ranking_recorded`
- comparison_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
