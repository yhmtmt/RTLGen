## Summary
- item_id: `l2_decoder_producer_ranker_policy_calibration_v1`
- run_key: `l2_decoder_producer_ranker_policy_calibration_v1_run_84d609fb8dc0bc54`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_producer_ranker_policy_calibration_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_producer_ranker_policy_calibration_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_producer_ranker_policy_calibration_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_producer_ranker_policy_calibration_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_producer_ranker_policy_calibration_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `6b8c7b9df7c6576321e3ed210a8d4048ba393b56`
- review_metadata_source_commit: `6b8c7b9df7c6576321e3ed210a8d4048ba393b56`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_producer_ranker_policy_calibration`
- comparison_role: `frontier_synthesis`
- expected_direction: `iterate`
- expected_reason: `If calibrated producer/ranker coupling no longer dominates, refresh frontier synthesis; otherwise target producer weight-memory/cache hierarchy.`
- expectation_status: `unspecified`
- evaluation_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`

## Focused Comparison
- primary_question: `Does measured policy-wrapper ranker service still dominate producer/ranker coupling, or was the previous frontier dominated by stale ranker hierarchy latency?`
- comparison_role: `frontier_synthesis`
- proposal_outcome: `ranking_recorded`
- comparison_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
