## Summary
- item_id: `l2_decoder_producer_ranker_coupled_noc_v1`
- run_key: `l2_decoder_producer_ranker_coupled_noc_v1_run_1ebeb9be7174ab96`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_producer_ranker_coupled_noc_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_producer_ranker_coupled_noc_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_producer_ranker_coupled_noc_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_producer_ranker_coupled_noc_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_producer_ranker_coupled_noc_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `0b7b404216d47d5bde3b8a7c3e343d14039a06f3`
- review_metadata_source_commit: `0b7b404216d47d5bde3b8a7c3e343d14039a06f3`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_producer_ranker_coupled_noc`
- comparison_role: `ranking`
- expected_direction: `iterate`
- expected_reason: `The expected output is a coupled producer/ranker frontier used to choose the next combined RTL target.`
- expectation_status: `unspecified`
- evaluation_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`

## Focused Comparison
- primary_question: `Do the r64/r128 ranker winners remain useful when producer II is derived from shared-GEMM output projection and memory bandwidth is reduced by NoC contention?`
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
