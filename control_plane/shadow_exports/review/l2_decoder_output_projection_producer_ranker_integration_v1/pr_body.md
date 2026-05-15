## Summary
- item_id: `l2_decoder_output_projection_producer_ranker_integration_v1`
- run_key: `l2_decoder_output_projection_producer_ranker_integration_v1_run_568c72f1109a1e46`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_output_projection_producer_ranker_integration_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_output_projection_producer_ranker_integration_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_output_projection_producer_ranker_integration_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_output_projection_producer_ranker_integration_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_output_projection_producer_ranker_integration_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `d0ea782633adba598d6334dbf11dd2125dea7da7`
- review_metadata_source_commit: `d0ea782633adba598d6334dbf11dd2125dea7da7`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_output_projection_producer_ranker_integration`
- comparison_role: `producer_ranker_service`
- expected_direction: `iterate`
- expected_reason: `If additive accounting shows producer-dominated timing and bounded overhead, use it as the producer-side integration baseline; otherwise split or gate the ranker wrapper before monolithic integration.`
- expectation_status: `unspecified`
- evaluation_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`

## Focused Comparison
- primary_question: `When independently measured producer and output-ranker wrapper PPA are accounted together, does the ranker wrapper materially change the producer-side timing, area, or power picture?`
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
