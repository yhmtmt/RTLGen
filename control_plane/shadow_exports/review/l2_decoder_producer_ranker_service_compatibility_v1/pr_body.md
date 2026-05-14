## Summary
- item_id: `l2_decoder_producer_ranker_service_compatibility_v1`
- run_key: `l2_decoder_producer_ranker_service_compatibility_v1_run_ae633b98acf417cc`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_producer_ranker_service_compatibility_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_producer_ranker_service_compatibility_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_producer_ranker_service_compatibility_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_producer_ranker_service_compatibility_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_producer_ranker_service_compatibility_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `3bbd68263897b8f830d19f2a69d3a84121081efc`
- review_metadata_source_commit: `3bbd68263897b8f830d19f2a69d3a84121081efc`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_producer_ranker_service_compatibility`
- comparison_role: `producer_ranker_service`
- expected_direction: `iterate`
- expected_reason: `Use measured ranker PPA/service and producer cadence to choose the next producer-coupled RTL candidate.`
- expectation_status: `unspecified`
- evaluation_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`

## Focused Comparison
- primary_question: `Which measured r64/k1 ranker point remains off the throughput path when coupled to the output-projection producer service model?`
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
