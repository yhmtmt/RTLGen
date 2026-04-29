## Summary
- item_id: `l2_decoder_probability_sensitivity_v1`
- run_key: `l2_decoder_probability_sensitivity_v1_run_b5838c9e8fa35f57`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `9/9 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_probability_sensitivity_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_probability_sensitivity_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_probability_sensitivity_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_probability_sensitivity_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_probability_sensitivity_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `267ed9b5a9df93860dd846da6a21e351850d58f6`
- review_metadata_source_commit: `267ed9b5a9df93860dd846da6a21e351850d58f6`

## Evaluation Mode
- evaluation_mode: `broad_ranking`
- abstraction_layer: `decoder_probability_sensitivity`
- comparison_role: `ranking`
- expected_direction: `iterate`
- expected_reason: `The map is expected to identify rough quality cliffs and candidate-safe regions for the pinned tiny benchmark, while explicitly avoiding general approximation acceptance claims.`
- expectation_status: `unspecified`
- evaluation_summary: `Broad ranking evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`

## Focused Comparison
- primary_question: `Which coarse probability-path approximation families preserve next-token and top-k quality on the pinned tiny decoder benchmark, and where do cliffs appear?`
- comparison_role: `ranking`
- proposal_outcome: `ranking_recorded`
- comparison_summary: `Broad ranking evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
