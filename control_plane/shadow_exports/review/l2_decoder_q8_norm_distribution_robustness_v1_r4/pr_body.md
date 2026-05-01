## Summary
- item_id: `l2_decoder_q8_norm_distribution_robustness_v1_r4`
- run_key: `l2_decoder_q8_norm_distribution_robustness_v1_r4_run_d0c02f87b02c0c5e`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `11/11 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_q8_norm_distribution_robustness_v1_r4/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_q8_norm_distribution_robustness_v1_r4.json`

## Developer Context
- proposal_id: `prop_l2_decoder_q8_norm_distribution_robustness_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_q8_norm_distribution_robustness_v1`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_q8_norm_distribution_robustness_v1` plus `docs/developer_agent_review.md`
- execution_source_commit: `53588088b357b5177cfc030f90d5c58426bd3d58`
- review_metadata_source_commit: `53588088b357b5177cfc030f90d5c58426bd3d58`

## Evaluation Mode
- evaluation_mode: `broad_ranking`
- abstraction_layer: `decoder_q8_normalization_distribution`
- comparison_role: `ranking`
- expected_direction: `iterate`
- expected_reason: `Retry should confirm the worker temp-checkout venv path fix allows reference/candidate artifact generation to complete.`
- expectation_status: `unspecified`
- evaluation_summary: `Broad ranking evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`

## Focused Comparison
- primary_question: `Across the distribution dataset, do bf16 reciprocal normalization and q8 reciprocal q10/q12/q14/q16 preserve exact next-token and top-k behavior relative to the reference and q8 exact normalization baseline?`
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
