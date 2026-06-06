## Summary
- item_id: `l2_decoder_attention_kv_dense_tile_all_measured_l1_clustered_schedule_llama7b_v1`
- run_key: `l2_decoder_attention_kv_dense_tile_all_measured_l1_clustered_schedule_llama7b_v1_run_201267453c414daa`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_kv_dense_tile_all_measured_l1_clustered_schedule_llama7b_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_kv_dense_tile_all_measured_l1_clustered_schedule_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_kv_dense_tile_all_measured_l1_clustered_schedule_llama7b_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_kv_dense_tile_all_measured_l1_clustered_schedule_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_kv_dense_tile_all_measured_l1_clustered_schedule_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `af5a94ebaf7a7b435c4cf99a328d33d02bdb4e2b`
- review_metadata_source_commit: `5d53cf10bcf6bddf233b50cd0d024638a48ef4af`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_kv_dense_tile_all_measured_l1_clustered_schedule`
- comparison_role: `frontier_synthesis`
- expected_direction: `select_dense_tile_clustered_frontier`
- expected_reason: `The job should identify the best dense tile compute source and clustered schedule point after measured L1 local datapath, softmax, FIFO, and router overhead is charged.`
- expectation_status: `unspecified`
- evaluation_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`

## Focused Comparison
- primary_question: `When dense tile PPA from l1_npu_dense_gemm_tile_scaling_v2 is used inside the all-measured L1 clustered schedule model, which die/SRAM/logic/cluster point is selected and what abstraction remains?`
- comparison_role: `frontier_synthesis`
- proposal_outcome: `ranking_recorded`
- comparison_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Submission Recovery
- submission_failure_count: `1`
- retry_request_count: `0`
- last_submission_failure: `work item l2_decoder_attention_kv_dense_tile_all_measured_l1_clustered_schedule_llama7b_v1 is not eligible for submission: developer_loop proposal linkage does not resolve to a proposal`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
