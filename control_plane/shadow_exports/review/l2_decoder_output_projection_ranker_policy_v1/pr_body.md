## Summary
- item_id: `l2_decoder_output_projection_ranker_policy_v1`
- run_key: `l2_decoder_output_projection_ranker_policy_v1_run_1a868224fe3be915`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_output_projection_ranker_policy_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_output_projection_ranker_policy_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_output_projection_ranker_policy_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_output_projection_ranker_policy_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_output_projection_ranker_policy_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `584c35acce8179c62a19ba59d72f26aebe41c4a0`
- review_metadata_source_commit: `584c35acce8179c62a19ba59d72f26aebe41c4a0`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_output_projection_ranker_policy`
- comparison_role: `producer_ranker_service`
- expected_direction: `promote`
- expected_reason: `If the promoted serial and rank-tree artifacts cover every cadence row, use this policy as the contract for the next output-projection producer wrapper implementation.`
- expectation_status: `unspecified`
- evaluation_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`

## Focused Comparison
- primary_question: `Does a simple producer-II policy cover the full cadence sweep using only promoted artifacts: serial_lpc1 for II >= the replay-proven threshold and radix-4 rank-tree fallback for faster rows?`
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
