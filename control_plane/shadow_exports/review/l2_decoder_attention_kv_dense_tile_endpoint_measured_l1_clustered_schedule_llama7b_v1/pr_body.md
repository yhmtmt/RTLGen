## Summary
- item_id: `l2_decoder_attention_kv_dense_tile_endpoint_measured_l1_clustered_schedule_llama7b_v1`
- run_key: `l2_decoder_attention_kv_dense_tile_endpoint_measured_l1_clustered_schedule_llama7b_v1_run_d756569e0753efd0`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_kv_dense_tile_endpoint_measured_l1_clustered_schedule_llama7b_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_kv_dense_tile_endpoint_measured_l1_clustered_schedule_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_kv_dense_tile_endpoint_measured_l1_clustered_schedule_v1`
- proposal_path: `docs/proposals/npu/prop_l2_decoder_attention_kv_dense_tile_endpoint_measured_l1_clustered_schedule_v1/proposal.json`
- reviewer_first_read: `docs/proposals/npu/prop_l2_decoder_attention_kv_dense_tile_endpoint_measured_l1_clustered_schedule_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `f70c220539bf8ade4457882bf477edfad4a37b6d`
- review_metadata_source_commit: `06405f2978db203b85a4b779c7a1993eb2befbd8`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_kv_dense_tile_endpoint_measured_l1_clustered_schedule`
- comparison_role: `standalone`
- expected_direction: `unknown`
- expectation_status: `unspecified`
- evaluation_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`

## Focused Comparison
- primary_question: `Does adding one measured on-chip endpoint service block per cluster materially change the dense-tile all-measured Llama7B 131k schedule frontier?`
- comparison_role: `standalone`
- proposal_outcome: `ranking_recorded`
- comparison_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Submission Recovery
- submission_failure_count: `1`
- retry_request_count: `0`
- last_submission_failure: `work item l2_decoder_attention_kv_dense_tile_endpoint_measured_l1_clustered_schedule_llama7b_v1 is not eligible for submission: developer_loop proposal linkage does not resolve to a proposal`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
