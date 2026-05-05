## Summary
- item_id: `l2_decoder_logit_rank_streaming_scale_stability_v1`
- run_key: `l2_decoder_logit_rank_streaming_scale_stability_v1_run_593c263c5b33c31e`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_logit_rank_streaming_scale_stability_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_logit_rank_streaming_scale_stability_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_logit_rank_streaming_scale_stability_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_logit_rank_streaming_scale_stability_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_logit_rank_streaming_scale_stability_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `c06374c1e379b074dda263af5b55f6cca0c6b7c4`
- review_metadata_source_commit: `c06374c1e379b074dda263af5b55f6cca0c6b7c4`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_logit_rank_streaming_overlap`
- comparison_role: `ranking`
- expected_direction: `iterate`
- expected_reason: `Check whether the SRAM-backed decoder streaming frontier remains stable across larger vocabulary and producer-lane scale points.`
- expectation_status: `unspecified`
- evaluation_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`

## Focused Comparison
- primary_question: `Does the SRAM-backed decoder logit-rank streaming frontier remain stable as vocabulary size and producer-lane count increase?`
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
