## Summary
- item_id: `l2_decoder_attention_kv_all_measured_l1_clustered_schedule_v1_r4`
- run_key: `l2_decoder_attention_kv_all_measured_l1_clustered_schedule_v1_r4_run_8c98027c0b8f2e42`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_kv_all_measured_l1_clustered_schedule_v1_r4/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_kv_all_measured_l1_clustered_schedule_v1_r4.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_kv_all_measured_l1_clustered_schedule_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_kv_all_measured_l1_clustered_schedule_v1`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_kv_all_measured_l1_clustered_schedule_v1` plus `docs/developer_agent_review.md`
- execution_source_commit: `9d811c441c132b740a1de93b7bf203135dba392b`
- review_metadata_source_commit: `9d811c441c132b740a1de93b7bf203135dba392b`

## Evaluation Mode
- evaluation_mode: `broad_ranking`
- abstraction_layer: `decoder_attention_kv_all_measured_l1_clustered_schedule`
- comparison_role: `ranking`
- expected_direction: `quantify_frontier_shift`
- expected_reason: `This retry should complete without materializing millions of rows and should show whether measured softmax generator cost changes the full-value L1 clustered frontier.`
- expectation_status: `met_with_caveats`
- evaluation_summary: `All-measured local L1 ranking evidence was recorded; the current best remains fp16_nm1 flat_nomacro, with SRAM/global-NoC service still analytic.`

## Focused Comparison
- primary_question: `Does the all-measured L1 cost stack change the Llama7B 131k native-GQA KV8 clustered attention frontier relative to the prior full-value clustered schedule?`
- comparison_role: `ranking`
- proposal_outcome: `iterate_baseline_recorded`
- comparison_summary: `All-measured local L1 ranking evidence was recorded; the current best remains fp16_nm1 flat_nomacro, with SRAM/global-NoC service still analytic.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Submission Recovery
- submission_failure_count: `1`
- retry_request_count: `0`
- last_submission_failure: `work item l2_decoder_attention_kv_all_measured_l1_clustered_schedule_v1_r4 is not eligible for submission: developer_loop proposal linkage does not resolve to a proposal`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
