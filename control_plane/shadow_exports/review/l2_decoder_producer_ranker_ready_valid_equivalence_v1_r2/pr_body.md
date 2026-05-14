## Summary
- item_id: `l2_decoder_producer_ranker_ready_valid_equivalence_v1_r2`
- run_key: `l2_decoder_producer_ranker_ready_valid_equivalence_v1_r2_run_eec08216096beb47`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `7/7 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_producer_ranker_ready_valid_equivalence_v1_r2/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_producer_ranker_ready_valid_equivalence_v1_r2.json`

## Developer Context
- proposal_id: `prop_l2_decoder_producer_ranker_ready_valid_equivalence_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_producer_ranker_ready_valid_equivalence_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_producer_ranker_ready_valid_equivalence_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `63cabb7e23a44567b0edb6bc19aaedc5de301bfb`
- review_metadata_source_commit: `63cabb7e23a44567b0edb6bc19aaedc5de301bfb`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_producer_ranker_ready_valid_equivalence`
- comparison_role: `equivalence_check`
- expected_direction: `iterate`
- expected_reason: `Confirm producer-ranker stream equivalence before physical wrapper exploration.`
- expectation_status: `unspecified`
- evaluation_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`

## Focused Comparison
- primary_question: `Does the first r64/k1 producer-to-ranker stream target preserve the perf-sim/full-vocabulary ranking semantics under the ready-valid contract?`
- comparison_role: `equivalence_check`
- proposal_outcome: `ranking_recorded`
- comparison_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
