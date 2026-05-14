## Summary
- item_id: `l2_decoder_serial_ranker_producer_replay_v1`
- run_key: `l2_decoder_serial_ranker_producer_replay_v1_run_35a320c776d5ea46`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `7/7 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_serial_ranker_producer_replay_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_serial_ranker_producer_replay_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_serial_ranker_producer_replay_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_serial_ranker_producer_replay_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_serial_ranker_producer_replay_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `db08265453e3e44b41d16fc3e9d7fc5ca0b99d50`
- review_metadata_source_commit: `db08265453e3e44b41d16fc3e9d7fc5ca0b99d50`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_serial_ranker_producer_replay`
- comparison_role: `producer_ranker_service`
- expected_direction: `iterate`
- expected_reason: `Confirm serial_lpc1 RTL remains equivalent at producer-model cadence before promoting it to producer-coupled RTL.`
- expectation_status: `unspecified`
- evaluation_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`

## Focused Comparison
- primary_question: `Do serial_lpc1, serial_lpc2, and serial_lpc4 preserve RTL equivalence and show the expected backpressure boundary when driven by producer-like tile cadence?`
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
