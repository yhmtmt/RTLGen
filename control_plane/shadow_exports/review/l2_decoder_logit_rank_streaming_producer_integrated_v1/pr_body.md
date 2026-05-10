## Summary
- item_id: `l2_decoder_logit_rank_streaming_producer_integrated_v1`
- run_key: `l2_decoder_logit_rank_streaming_producer_integrated_v1_run_d2fa592f46a90cd0`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_logit_rank_streaming_producer_integrated_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_logit_rank_streaming_producer_integrated_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_logit_rank_streaming_producer_integrated_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_logit_rank_streaming_producer_integrated_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_logit_rank_streaming_producer_integrated_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `c9bca6b1f6d8ac8f0ade88d87ece3bd5962ae64b`
- review_metadata_source_commit: `c9bca6b1f6d8ac8f0ade88d87ece3bd5962ae64b`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_logit_rank_streaming_producer_integrated`
- comparison_role: `ranking`
- expected_direction: `iterate`
- expected_reason: `The expected result is a clearer r64/r128 producer-integrated frontier and an explicit RTL-equivalence checklist before implementing the combined producer/ranker macro.`
- expectation_status: `unspecified`
- evaluation_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`

## Focused Comparison
- primary_question: `For r64 and r128 producer widths, which top-k, producer-II, merge-II, and FIFO choices remain latency- and traffic-competitive while preserving perf-sim/RTL stream equivalence observables?`
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
