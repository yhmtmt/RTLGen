## Summary
- item_id: `l2_decoder_q8_norm_distribution_broad_v2`
- run_key: `l2_decoder_q8_norm_distribution_broad_v2_run_f9ecee864b4dcca6`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `11/11 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_q8_norm_distribution_broad_v2/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_q8_norm_distribution_broad_v2.json`

## Developer Context
- proposal_id: `prop_l2_decoder_q8_norm_distribution_broad_v2`
- proposal_path: `docs/proposals/prop_l2_decoder_q8_norm_distribution_broad_v2/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_q8_norm_distribution_broad_v2/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `b77bf8f43863ea656cfb6369a8c8fc60853e63ab`
- review_metadata_source_commit: `b77bf8f43863ea656cfb6369a8c8fc60853e63ab`

## Evaluation Mode
- evaluation_mode: `broad_ranking`
- abstraction_layer: `decoder_q8_normalization_distribution_broad_v2`
- comparison_role: `ranking`
- expected_direction: `iterate`
- expected_reason: `Broaden the distribution screen before choosing q8 reciprocal versus bf16 reciprocal normalization.`
- expectation_status: `unspecified`
- evaluation_summary: `Broad ranking evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`

## Focused Comparison
- primary_question: `Across an expanded 48-sample rough prompt distribution, do bf16 reciprocal normalization and q8 reciprocal q10/q12/q14/q16 preserve exact next-token and top-k behavior relative to the exact reference and q8 exact-normalization baseline?`
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
