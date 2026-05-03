## Summary
- item_id: `l2_decoder_trained_tiny_quality_v1`
- run_key: `l2_decoder_trained_tiny_quality_v1_run_61435f2f5c602eb9`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `11/11 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_trained_tiny_quality_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_trained_tiny_quality_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_trained_tiny_quality_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_trained_tiny_quality_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_trained_tiny_quality_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `4b3085f0866e3940d56722d190f8630d06b5e3a5`
- review_metadata_source_commit: `4b3085f0866e3940d56722d190f8630d06b5e3a5`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_trained_tiny_quality`
- comparison_role: `ranking`
- expected_direction: `iterate`
- expected_reason: `Use the trained-weight tiny result to decide whether bf16/PWL recovery should move to distilgpt2/GPT-2 confirmation or return to logit-margin diagnosis.`
- expectation_status: `unspecified`
- evaluation_summary: `Focused comparison baseline could not be resolved from proposal baseline_refs.`

## Focused Comparison
- primary_question: `Does the current decoder bf16/PWL plus logit tie-break recovery remain exact-safe on a trained tiny GPT-2-family decoder workload?`
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
