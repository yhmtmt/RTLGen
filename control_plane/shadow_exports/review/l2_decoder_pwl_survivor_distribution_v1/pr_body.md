## Summary
- item_id: `l2_decoder_pwl_survivor_distribution_v1`
- run_key: `l2_decoder_pwl_survivor_distribution_v1_run_d739ed82f5f932c3`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `11/11 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_pwl_survivor_distribution_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_pwl_survivor_distribution_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_pwl_survivor_distribution_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_pwl_survivor_distribution_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_pwl_survivor_distribution_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `c0687285c736ab63c0ad05b97dc2915721a941e7`
- review_metadata_source_commit: `c0687285c736ab63c0ad05b97dc2915721a941e7`

## Evaluation Mode
- evaluation_mode: `broad_ranking`
- abstraction_layer: `decoder_pwl_survivor_distribution`
- comparison_role: `ranking`
- expected_direction: `iterate`
- expectation_status: `unspecified`
- evaluation_summary: `Broad ranking evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`

## Focused Comparison
- primary_question: `Across the expanded v2 prompt-regime dataset, do q12/unquantized PWL survivor rows preserve exact next-token and top-k behavior while q10/q8/bf16 controls expose the precision boundary?`
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
