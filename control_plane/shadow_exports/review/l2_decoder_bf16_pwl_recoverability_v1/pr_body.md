## Summary
- item_id: `l2_decoder_bf16_pwl_recoverability_v1`
- run_key: `l2_decoder_bf16_pwl_recoverability_v1_run_9dfe86cde2b1cb34`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_bf16_pwl_recoverability_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_bf16_pwl_recoverability_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_bf16_pwl_recoverability_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_bf16_pwl_recoverability_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_bf16_pwl_recoverability_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `8470bd3962219e1a101bc5df97642ce90b27f42f`
- review_metadata_source_commit: `8470bd3962219e1a101bc5df97642ce90b27f42f`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_bf16_pwl_recoverability`
- comparison_role: `ranking`
- expected_direction: `iterate`
- expected_reason: `Use score-gap evidence to decide whether to prototype bf16/PWL-aware fine-tuning before more exact-safe integer hardware.`
- expectation_status: `unspecified`
- evaluation_summary: `Focused comparison baseline could not be resolved from proposal baseline_refs.`

## Focused Comparison
- primary_question: `For bf16/PWL exact-next misses, is the reference token still rank-2 with a small candidate score gap relative to normal correct-sample margins?`
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
