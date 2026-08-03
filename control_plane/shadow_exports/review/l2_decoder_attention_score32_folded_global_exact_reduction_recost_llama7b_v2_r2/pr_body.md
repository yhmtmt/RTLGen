## Summary
- item_id: `l2_decoder_attention_score32_folded_global_exact_reduction_recost_llama7b_v2_r2`
- run_key: `l2_decoder_attention_score32_folded_global_exact_reduction_recost_llama7b_v2_r2_run_536314512ca84a0d`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `2/2 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_score32_folded_global_exact_reduction_recost_llama7b_v2_r2/evaluated.json`
- metrics_rows_count: `0`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_score32_folded_global_exact_reduction_recost_llama7b_v2_r2.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_score32_folded_global_exact_reduction_recost_llama7b_v2`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_score32_folded_global_exact_reduction_recost_llama7b_v2/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_score32_folded_global_exact_reduction_recost_llama7b_v2/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `04c539aaed4292785bfda00c6acfa3f6015aa55d`
- review_metadata_source_commit: `04c539aaed4292785bfda00c6acfa3f6015aa55d`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_score32_folded_global_exact_reduction_recost`
- comparison_role: `score32_folded_global_exact_reduction_recost`
- expected_direction: `record_bounded_folded_global_exact_reduction_recost`
- expected_reason: `Retry with item-specific evidence paths after preserving the successful no-diff r1 run.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_score32_folded_global_exact_reduction_recost__l2_decoder_attention_score32_folded_global_exact_reduction_recost_llama7b_v2_r2.json: decision=decoder_evidence_recorded.`

## Focused Comparison
- primary_question: `What bounded global exact-reduction timing and measured-component PPA estimate remain once the 986-cycle producer assumption is withdrawn and the measured folded c16 tree plus measured L8/b4 finalizer components are composed conservatively?`
- comparison_role: `score32_folded_global_exact_reduction_recost`
- proposal_outcome: `decoder_evidence_recorded`
- comparison_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_score32_folded_global_exact_reduction_recost__l2_decoder_attention_score32_folded_global_exact_reduction_recost_llama7b_v2_r2.json: decision=decoder_evidence_recorded.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
