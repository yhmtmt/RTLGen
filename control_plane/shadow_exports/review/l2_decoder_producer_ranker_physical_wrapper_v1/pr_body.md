## Summary
- item_id: `l2_decoder_producer_ranker_physical_wrapper_v1`
- run_key: `l2_decoder_producer_ranker_physical_wrapper_v1_run_876f6c046062d123`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `7/7 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_producer_ranker_physical_wrapper_v1/evaluated.json`
- metrics_rows_count: `25`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_producer_ranker_physical_wrapper_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_producer_ranker_physical_wrapper_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_producer_ranker_physical_wrapper_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_producer_ranker_physical_wrapper_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `0b05f529e8920bbdd924612d2f31403e3c7a8d45`
- review_metadata_source_commit: `0b05f529e8920bbdd924612d2f31403e3c7a8d45`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_producer_ranker_physical_wrapper`
- comparison_role: `physical_wrapper`
- expected_direction: `iterate`
- expected_reason: `Use the first measured r64/k1 producer-ranker wrapper PPA before r128 or producer-coupled scaling.`
- expectation_status: `unspecified`
- evaluation_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`

## Focused Comparison
- primary_question: `What is the first bounded physical PPA/timing anchor for the r64/k1 producer-to-ranker ready-valid wrapper after equivalence has passed?`
- comparison_role: `physical_wrapper`
- proposal_outcome: `ranking_recorded`
- comparison_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
