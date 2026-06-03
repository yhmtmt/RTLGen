## Summary
- item_id: `l2_decoder_attention_kv_compute_floor_gap_llama7b_v1`
- run_key: `l2_decoder_attention_kv_compute_floor_gap_llama7b_v1_run_7a9e3e4183791924`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_kv_compute_floor_gap_llama7b_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_kv_compute_floor_gap_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_kv_compute_floor_gap_llama7b_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_kv_compute_floor_gap_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_kv_compute_floor_gap_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `36f8bae95d3df28a19037d3b8ad1fb934d8acf68`
- review_metadata_source_commit: `36f8bae95d3df28a19037d3b8ad1fb934d8acf68`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_kv_compute_floor_gap`
- comparison_role: `frontier_synthesis`
- expected_direction: `quantify_compute_gap`
- expected_reason: `The job should report the MAC/cycle and MAC/cycle/mm2 multiplier needed for measured compute blocks to reach the HBM-bound attention floor.`
- expectation_status: `unspecified`
- evaluation_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`

## Focused Comparison
- primary_question: `How far is the current measured NPU compute density from the first HBM-bound Llama7B 131k attention/KV compute floor?`
- comparison_role: `frontier_synthesis`
- proposal_outcome: `ranking_recorded`
- comparison_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Submission Recovery
- submission_failure_count: `1`
- retry_request_count: `0`
- last_submission_failure: `work item l2_decoder_attention_kv_compute_floor_gap_llama7b_v1 is not eligible for submission: developer_loop proposal linkage does not resolve to a proposal`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
