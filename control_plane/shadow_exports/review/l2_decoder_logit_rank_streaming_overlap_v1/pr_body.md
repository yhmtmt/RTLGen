## Summary
- item_id: `l2_decoder_logit_rank_streaming_overlap_v1`
- run_key: `l2_decoder_logit_rank_streaming_overlap_v1_run_c952d59bee64a5ce`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_logit_rank_streaming_overlap_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_logit_rank_streaming_overlap_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_logit_rank_streaming_overlap_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_logit_rank_streaming_overlap_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_logit_rank_streaming_overlap_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `90276bfa2719c9d8318ab565187a6a4d74874c57`
- review_metadata_source_commit: `90276bfa2719c9d8318ab565187a6a4d74874c57`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_logit_rank_streaming_overlap`
- comparison_role: `ranking`
- expected_direction: `iterate`
- expected_reason: `Streaming top-k only becomes compelling if producer/ranker overlap and SRAM traffic reduction survive the ready-valid RTL contract.`
- expectation_status: `unspecified`
- evaluation_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`

## Focused Comparison
- primary_question: `Which producer lane width, producer II, merge II, top-k, and FIFO depth combinations preserve the logit-rank stream contract while recovering materialized-rank latency and reducing memory traffic?`
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
