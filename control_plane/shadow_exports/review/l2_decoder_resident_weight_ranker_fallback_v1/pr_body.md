## Summary
- item_id: `l2_decoder_resident_weight_ranker_fallback_v1`
- run_key: `l2_decoder_resident_weight_ranker_fallback_v1_run_cf7411f0191ca94d`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_resident_weight_ranker_fallback_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_resident_weight_ranker_fallback_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_resident_weight_ranker_fallback_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_resident_weight_ranker_fallback_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_resident_weight_ranker_fallback_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `82d342bd325da144cbff33333a5f5d79b948cc6c`
- review_metadata_source_commit: `82d342bd325da144cbff33333a5f5d79b948cc6c`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_resident_weight_ranker_fallback`
- comparison_role: `producer_ranker_service`
- expected_direction: `iterate`
- expected_reason: `Choose whether resident-weight producer rows should use a buffered serial_lpc4 guard or a rank-tree fallback.`
- expectation_status: `unspecified`
- evaluation_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`

## Focused Comparison
- primary_question: `For cadence rows that outpace the replay-proven serial ranker thresholds, is a small input buffer in front of serial_lpc4 sufficient, or should those rows fall back to the measured r64 rank-tree architecture?`
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
