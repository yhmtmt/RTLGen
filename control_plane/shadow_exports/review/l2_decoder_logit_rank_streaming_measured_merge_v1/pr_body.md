## Summary
- item_id: `l2_decoder_logit_rank_streaming_measured_merge_v1`
- run_key: `l2_decoder_logit_rank_streaming_measured_merge_v1_run_968cf67b49c4dc06`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_logit_rank_streaming_measured_merge_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_logit_rank_streaming_measured_merge_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_logit_rank_streaming_measured_merge_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_logit_rank_streaming_measured_merge_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_logit_rank_streaming_measured_merge_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `948415f211bcc6b8cf094956245aabcd4c80b719`
- review_metadata_source_commit: `948415f211bcc6b8cf094956245aabcd4c80b719`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_logit_rank_streaming_overlap`
- comparison_role: `ranking`
- expected_direction: `iterate`
- expected_reason: `Use the measured merge/FIFO-calibrated model to decide whether the next frontier is memory/NoC hierarchy or flat rank datapath scaling.`
- expectation_status: `unspecified`
- evaluation_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`

## Focused Comparison
- primary_question: `Does the rank-only streaming hierarchy remain a useful frontier once candidate merge/FIFO timing, area, and power come from the measured Nangate45 block?`
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
