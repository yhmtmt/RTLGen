## Summary
- item_id: `l2_decoder_bf16_pwl_recovery_v1`
- run_key: `l2_decoder_bf16_pwl_recovery_v1_run_62684540654fde9a`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `11/11 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_bf16_pwl_recovery_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_bf16_pwl_recovery_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_bf16_pwl_recovery_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_bf16_pwl_recovery_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_bf16_pwl_recovery_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `7f626ef14576dfe41bfad363d6b24602dae52935`
- review_metadata_source_commit: `7f626ef14576dfe41bfad363d6b24602dae52935`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_bf16_pwl_recovery`
- comparison_role: `ranking`
- expected_direction: `iterate`
- expected_reason: `If logit tie-breaking recovers the zero-gap bf16/PWL misses without regressions, keep bf16/PWL as the low-cost frontier before full QAT or q12 fallback.`
- expectation_status: `unspecified`
- evaluation_summary: `Focused comparison baseline could not be resolved from proposal baseline_refs.`

## Focused Comparison
- primary_question: `Does bf16/PWL with logit tie-breaking recover the two broad-v2 exact-next misses while preserving top-k containment and avoiding regressions?`
- comparison_role: `ranking`
- proposal_outcome: `unavailable`
- comparison_summary: `Focused comparison baseline could not be resolved from proposal baseline_refs.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
