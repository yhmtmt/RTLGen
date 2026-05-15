## Summary
- item_id: `l2_decoder_attention_kv_memory_131k_v1`
- run_key: `l2_decoder_attention_kv_memory_131k_v1_run_f41fbf6dd7737c54`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_kv_memory_131k_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_kv_memory_131k_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_kv_memory_131k_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_kv_memory_131k_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_kv_memory_131k_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `d4a3430c088661edb694e8803e348e748f5dea51`
- review_metadata_source_commit: `d4a3430c088661edb694e8803e348e748f5dea51`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_kv_memory`
- comparison_role: `frontier_synthesis`
- expected_direction: `iterate`
- expected_reason: `Test whether 131k context shifts the next measured block to attention/KV memory hierarchy.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_memory__l2_decoder_attention_kv_memory_131k_v1.json: decision=decoder_evidence_recorded.`

## Focused Comparison
- primary_question: `At 131072-token context, which KV sharing and memory-tier choices keep attention/KV feasible, and does attention/KV become the whole-decoder bottleneck?`
- comparison_role: `frontier_synthesis`
- proposal_outcome: `decoder_evidence_recorded`
- comparison_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_memory__l2_decoder_attention_kv_memory_131k_v1.json: decision=decoder_evidence_recorded.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
