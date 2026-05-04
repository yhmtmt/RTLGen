## Summary
- item_id: `l2_decoder_gpt2_quality_v1`
- run_key: `l2_decoder_gpt2_quality_v1_run_8ba8c7fe3ad8cf83`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `12/12 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_gpt2_quality_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_gpt2_quality_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_gpt2_quality_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_gpt2_quality_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_gpt2_quality_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `ef58e573b0ddd2059e4d37eaacf40059676e0d8a`
- review_metadata_source_commit: `ef58e573b0ddd2059e4d37eaacf40059676e0d8a`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_gpt2_quality`
- comparison_role: `ranking`
- expected_direction: `iterate`
- expected_reason: `Use the GPT-2 checkpoint result to decide whether bf16/PWL should move to broader GPT-2 prompt stress, QAT recovery, or failure diagnosis.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_trained_v1/decoder_gpt2_quality__l2_decoder_gpt2_quality_v1.json: decision=baseline_exact_safe; exact_safe_after_recovery=True; recovered_count=0; regression_count=0; recommended_next_step=Treat bf16/PWL as exact-safe on this screen without relying on the logit tie-breaker; keep the tie-break row as a ranking-stability guard for broader prompts or larger checkpoints.`

## Focused Comparison
- primary_question: `Does the current bf16/PWL path remain exact-safe on a GPT-2 small next-token workload?`
- comparison_role: `ranking`
- proposal_outcome: `baseline_exact_safe`
- comparison_summary: `Decoder quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_trained_v1/decoder_gpt2_quality__l2_decoder_gpt2_quality_v1.json: decision=baseline_exact_safe; exact_safe_after_recovery=True; recovered_count=0; regression_count=0; recommended_next_step=Treat bf16/PWL as exact-safe on this screen without relying on the logit tie-breaker; keep the tie-break row as a ranking-stability guard for broader prompts or larger checkpoints.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
