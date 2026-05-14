## Summary
- item_id: `l2_decoder_output_projection_cadence_sensitivity_v1`
- run_key: `l2_decoder_output_projection_cadence_sensitivity_v1_run_24542584a9a5ddf0`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_output_projection_cadence_sensitivity_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_output_projection_cadence_sensitivity_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_output_projection_cadence_sensitivity_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_output_projection_cadence_sensitivity_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_output_projection_cadence_sensitivity_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `4c6fb6c8b2e3f7dc92a1e7ec37ca31f52a7ff5ce`
- review_metadata_source_commit: `4c6fb6c8b2e3f7dc92a1e7ec37ca31f52a7ff5ce`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_output_projection_cadence_sensitivity`
- comparison_role: `producer_ranker_service`
- expected_direction: `iterate`
- expected_reason: `Identify when output-projection weight residency causes producer II to cross serial_lpc1/lpc2/lpc4 zero-backpressure thresholds.`
- expectation_status: `unspecified`
- evaluation_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`

## Focused Comparison
- primary_question: `At what output-projection weight residency/cache-hit assumptions does the producer II cross the replay-observed zero-backpressure thresholds for serial_lpc1, lpc2, and lpc4?`
- comparison_role: `producer_ranker_service`
- proposal_outcome: `ranking_recorded`
- comparison_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
