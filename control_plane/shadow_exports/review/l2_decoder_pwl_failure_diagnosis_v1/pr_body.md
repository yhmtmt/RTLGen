## Summary
- item_id: `l2_decoder_pwl_failure_diagnosis_v1`
- run_key: `l2_decoder_pwl_failure_diagnosis_v1_run_7369f3138f1e9470`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_pwl_failure_diagnosis_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_pwl_failure_diagnosis_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_pwl_failure_diagnosis_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_pwl_failure_diagnosis_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_pwl_failure_diagnosis_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `02040671928616df91d2e8d74fc7a51c8859a393`
- review_metadata_source_commit: `02040671928616df91d2e8d74fc7a51c8859a393`

## Evaluation Mode
- evaluation_mode: `broad_ranking`
- abstraction_layer: `decoder_pwl_failure_diagnosis`
- comparison_role: `ranking`
- expected_direction: `iterate`
- expected_reason: `Choose the next decoder frontier job from failure mechanism evidence instead of sweeping reciprocal precision blindly.`
- expectation_status: `unspecified`
- evaluation_summary: `Broad ranking evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`

## Focused Comparison
- primary_question: `For the two broad-v2 shared PWL misses, are exact-token changes explained by the common PWL probability path and narrow margins, or by q8 reciprocal normalization precision?`
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
