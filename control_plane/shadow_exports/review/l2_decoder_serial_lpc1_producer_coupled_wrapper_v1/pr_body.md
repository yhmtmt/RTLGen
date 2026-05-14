## Summary
- item_id: `l2_decoder_serial_lpc1_producer_coupled_wrapper_v1`
- run_key: `l2_decoder_serial_lpc1_producer_coupled_wrapper_v1_run_f4631450c9c19c59`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `7/7 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_serial_lpc1_producer_coupled_wrapper_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_serial_lpc1_producer_coupled_wrapper_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_serial_lpc1_producer_coupled_wrapper_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_serial_lpc1_producer_coupled_wrapper_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_serial_lpc1_producer_coupled_wrapper_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `878525451f0d2820b45544a024515bb2af01c6ef`
- review_metadata_source_commit: `878525451f0d2820b45544a024515bb2af01c6ef`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_serial_lpc1_producer_coupled_wrapper`
- comparison_role: `producer_ranker_service`
- expected_direction: `iterate`
- expected_reason: `Confirm serial_lpc1 measured PPA and focused zero-backpressure RTL replay at the selected producer cadence before using it in the next output-projection producer wrapper.`
- expectation_status: `unspecified`
- evaluation_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`

## Focused Comparison
- primary_question: `Can serial_lpc1 be promoted as the selected producer-coupled ranker wrapper under the current output-projection producer cadence assumption?`
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
