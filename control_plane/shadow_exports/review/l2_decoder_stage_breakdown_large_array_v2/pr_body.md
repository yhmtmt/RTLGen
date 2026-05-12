## Summary
- item_id: `l2_decoder_stage_breakdown_large_array_v2`
- run_key: `l2_decoder_stage_breakdown_large_array_v2_run_2b9f8ac94697fafe`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_stage_breakdown_large_array_v2/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_stage_breakdown_large_array_v2.json`

## Developer Context
- proposal_id: `prop_l2_decoder_stage_breakdown_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_stage_breakdown_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_stage_breakdown_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `0ecf2602e7aa9a9fb64c4fa4c0a9b61b257aea83`
- review_metadata_source_commit: `0ecf2602e7aa9a9fb64c4fa4c0a9b61b257aea83`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_stage_breakdown`
- comparison_role: `ranking`
- expected_direction: `iterate`
- expected_reason: `Use the larger-array stage breakdown to keep the overall decoder bottleneck visible before narrowing attention/KV RTL work.`
- expectation_status: `unspecified`
- evaluation_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`

## Focused Comparison
- primary_question: `Which decoder stage dominates latency and traffic across GPT-2-like and larger proxy shapes when sequence length, compute throughput, memory bandwidth, and weight residency are varied?`
- comparison_role: `ranking`
- proposal_outcome: `ranking_recorded`
- comparison_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
