## Summary
- item_id: `l2_decoder_attention_kv_memory_broad_gqa8_v1`
- run_key: `l2_decoder_attention_kv_memory_broad_gqa8_v1_run_5235c9133f412938`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_kv_memory_broad_gqa8_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_kv_memory_broad_gqa8_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_kv_memory_broad_gqa8_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_kv_memory_broad_gqa8_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_kv_memory_broad_gqa8_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `a914c731cb4e248e1d2f341b92e89178757c8a04`
- review_metadata_source_commit: `a914c731cb4e248e1d2f341b92e89178757c8a04`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_kv_memory`
- comparison_role: `memory_hierarchy`
- expected_direction: `iterate`
- expected_reason: `Use the broadened attention/KV sweep to decide whether the next measured physical work should stay on output-projection memory or shift toward KV/cache/attention data movement.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_memory__l2_decoder_attention_kv_memory_broad_gqa8_v1.json: decision=decoder_evidence_recorded.`

## Focused Comparison
- primary_question: `What focused comparison directly tests this proposal?`
- comparison_role: `memory_hierarchy`
- proposal_outcome: `decoder_evidence_recorded`
- comparison_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_memory__l2_decoder_attention_kv_memory_broad_gqa8_v1.json: decision=decoder_evidence_recorded.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
