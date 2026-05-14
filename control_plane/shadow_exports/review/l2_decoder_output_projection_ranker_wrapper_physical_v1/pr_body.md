## Summary
- item_id: `l2_decoder_output_projection_ranker_wrapper_physical_v1`
- run_key: `l2_decoder_output_projection_ranker_wrapper_physical_v1_run_12c414cca78e9491`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `8/8 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_output_projection_ranker_wrapper_physical_v1/evaluated.json`
- metrics_rows_count: `26`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_output_projection_ranker_wrapper_physical_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_output_projection_ranker_wrapper_physical_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_output_projection_ranker_wrapper_physical_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_output_projection_ranker_wrapper_physical_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `3cd726e689206ffa9a2b1ea4d737c982a329f0b1`
- review_metadata_source_commit: `3cd726e689206ffa9a2b1ea4d737c982a329f0b1`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_output_projection_ranker_wrapper_physical`
- comparison_role: `producer_ranker_service`
- expected_direction: `iterate`
- expected_reason: `If the muxed policy wrapper PPA is acceptable, integrate it into the output-projection producer wrapper; otherwise split serial and rank-tree wrappers or add clock/path gating.`
- expectation_status: `unspecified`
- evaluation_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`

## Focused Comparison
- primary_question: `What is the PPA overhead of a concrete policy wrapper that contains serial and rank-tree paths plus selection mux/control for r64 and banked r128 producer tiles?`
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
