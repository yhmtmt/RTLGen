## Summary
- item_id: `l2_decoder_resident_ranktree_fallback_promotion_v1`
- run_key: `l2_decoder_resident_ranktree_fallback_promotion_v1_run_a710850369bd2872`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_resident_ranktree_fallback_promotion_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_resident_ranktree_fallback_promotion_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_resident_ranktree_fallback_promotion_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_resident_ranktree_fallback_promotion_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_resident_ranktree_fallback_promotion_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `1e78f669391143bd638c632f3fa903c02672a4f2`
- review_metadata_source_commit: `1e78f669391143bd638c632f3fa903c02672a4f2`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_resident_ranktree_fallback_promotion`
- comparison_role: `producer_ranker_service`
- expected_direction: `promote`
- expected_reason: `If all unsafe resident-weight rows use zero-buffer rank-tree recommendations and the selected radix has clean RTL simulation plus measured PPA, use it as the producer-coupled fallback implementation target.`
- expectation_status: `unspecified`
- evaluation_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`

## Focused Comparison
- primary_question: `Can the resident-weight ranker fallback policy be promoted to the measured radix-4 r64 rank-tree while preserving RTL simulation evidence, physical metrics, and zero-buffer service coverage?`
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
