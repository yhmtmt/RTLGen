## Summary
- item_id: `l2_decoder_bf16_pwl_scale_probe_v1`
- run_key: `l2_decoder_bf16_pwl_scale_probe_v1_run_f84883ea80390554`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `11/11 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_bf16_pwl_scale_probe_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_bf16_pwl_scale_probe_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_bf16_pwl_scale_probe_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_bf16_pwl_scale_probe_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_bf16_pwl_scale_probe_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `3e1537796e6e183d81eddd9a004d88cdb5885387`
- review_metadata_source_commit: `3e1537796e6e183d81eddd9a004d88cdb5885387`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_bf16_pwl_scale_probe`
- comparison_role: `ranking`
- expected_direction: `iterate`
- expected_reason: `Use the scale-proxy result to decide whether bf16/PWL recovery should move to larger imported-model confirmation or return to diagnosis.`
- expectation_status: `unspecified`
- evaluation_summary: `Focused comparison baseline could not be resolved from proposal baseline_refs.`

## Focused Comparison
- primary_question: `Does bf16/PWL plus logit tie-break remain exact-safe when prompt diversity and ranking pressure are increased in the tiny decoder harness?`
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
