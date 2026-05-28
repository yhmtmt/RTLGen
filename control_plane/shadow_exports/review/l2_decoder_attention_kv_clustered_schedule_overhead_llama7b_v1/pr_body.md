## Summary
- item_id: `l2_decoder_attention_kv_clustered_schedule_overhead_llama7b_v1`
- run_key: `l2_decoder_attention_kv_clustered_schedule_overhead_llama7b_v1_run_13b65d632068a3bd`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_kv_clustered_schedule_overhead_llama7b_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_kv_clustered_schedule_overhead_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_kv_measured_compute_partition_llama7b_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_kv_measured_compute_partition_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_kv_measured_compute_partition_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `82b98cb1a7c967067a2bb4fb0b00423935c549bb`
- review_metadata_source_commit: `82b98cb1a7c967067a2bb4fb0b00423935c549bb`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_kv_clustered_schedule_overhead`
- comparison_role: `frontier_synthesis`
- expected_direction: `iterate`
- expected_reason: `If the frontier survives plausible command/reducer overheads, move to routed command/reducer RTL calibration; if it flips, narrow cluster/reducer architecture first.`
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
