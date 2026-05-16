## Summary
- item_id: `l2_decoder_attention_kv_spill_scheduler_llama7b_v1`
- run_key: `l2_decoder_attention_kv_spill_scheduler_llama7b_v1_run_0c27d568676e85f0`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_kv_spill_scheduler_llama7b_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_kv_spill_scheduler_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_kv_spill_scheduler_llama7b_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_kv_spill_scheduler_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_kv_spill_scheduler_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `1ad3f620e14078742a9bd8e6e3eff6a912888168`
- review_metadata_source_commit: `1ad3f620e14078742a9bd8e6e3eff6a912888168`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_kv_spill_scheduler`
- comparison_role: `frontier_synthesis`
- expected_direction: `iterate`
- expected_reason: `Use tile-level spill scheduling to choose the next concrete memory/NoC RTL or controller measurement.`
- expectation_status: `unspecified`
- evaluation_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`

## Focused Comparison
- primary_question: `How much of the llama7b_proxy 131k spill latency can be hidden by tile-level prefetch scheduling and finite HBM parallelism?`
- comparison_role: `frontier_synthesis`
- proposal_outcome: `ranking_recorded`
- comparison_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Submission Recovery
- submission_failure_count: `0`
- retry_request_count: `0`
- final_submission_pr: `https://github.com/yhmtmt/RTLGen/pull/595`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
