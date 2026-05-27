## Summary
- item_id: `l2_decoder_attention_kv_measured_compute_partition_llama7b_v1`
- run_key: `l2_decoder_attention_kv_measured_compute_partition_llama7b_v1_run_0eaccaaa84c87314`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_kv_measured_compute_partition_llama7b_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_kv_measured_compute_partition_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_kv_measured_compute_partition_llama7b_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_kv_measured_compute_partition_llama7b_v1`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_kv_measured_compute_partition_llama7b_v1` plus `docs/developer_agent_review.md`
- execution_source_commit: `a8aa60dbd7f0dd0eb477d8768b3b23a1f1e1786f`
- review_metadata_source_commit: `a8aa60dbd7f0dd0eb477d8768b3b23a1f1e1786f`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_kv_measured_compute_partition`
- comparison_role: `frontier_synthesis`
- expected_direction: `iterate`
- expected_reason: `If clustered partitioning keeps nm64-flat dominant, move to RTL/PPA command-routing hierarchy; if smaller clusters win or NoC dominates, refine memory/NOC hierarchy before deeper RTL.`
- expectation_status: `unspecified`
- evaluation_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`

## Focused Comparison
- primary_question: `For quality-backed native-GQA KV8 at 131k context, which compute cluster count and memory/NOC split gives the best latency under measured corrected compute PPA and practical die budgets?`
- comparison_role: `frontier_synthesis`
- proposal_outcome: `ranking_recorded`
- comparison_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
