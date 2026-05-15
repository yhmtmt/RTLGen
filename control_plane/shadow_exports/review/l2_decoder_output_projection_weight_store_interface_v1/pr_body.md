## Summary
- item_id: `l2_decoder_output_projection_weight_store_interface_v1`
- run_key: `l2_decoder_output_projection_weight_store_interface_v1_run_e393c69b92bd41cf`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_output_projection_weight_store_interface_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_output_projection_weight_store_interface_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_output_projection_weight_store_interface_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_output_projection_weight_store_interface_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_output_projection_weight_store_interface_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `205f77703ca5ca868d880f363bbfb4454b5f544e`
- review_metadata_source_commit: `205f77703ca5ca868d880f363bbfb4454b5f544e`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_output_projection_weight_store_interface`
- comparison_role: `weight_store_contract`
- expected_direction: `iterate`
- expected_reason: `If the bounded sharded interface matches perf-sim, use the contract for a measured producer-side weight-fetch wrapper while keeping full storage PPA from the feasibility model.`
- expectation_status: `unspecified`
- evaluation_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`

## Focused Comparison
- comparison_role: `weight_store_contract`
- proposal_outcome: `ranking_recorded`
- comparison_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
