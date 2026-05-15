## Summary
- item_id: `l2_decoder_attention_kv_memory_131k_capacity_v1`
- run_key: `l2_decoder_attention_kv_memory_131k_capacity_v1_run_9a0f9dbb8cb9e80e`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_kv_memory_131k_capacity_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_kv_memory_131k_capacity_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_kv_memory_131k_capacity_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_kv_memory_131k_capacity_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_kv_memory_131k_capacity_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `35340bfdb7c34865190f190b36a149fc9b60a6f5`
- review_metadata_source_commit: `35340bfdb7c34865190f190b36a149fc9b60a6f5`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_kv_memory`
- comparison_role: `frontier_synthesis`
- expected_direction: `iterate`
- expected_reason: `Use capacity-annotated attention/KV evidence to define the next integrated memory-hierarchy measurement.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_memory__l2_decoder_attention_kv_memory_131k_capacity_v1.json: decision=decoder_evidence_recorded.`

## Focused Comparison
- primary_question: `How much KV-cache capacity and SRAM area does the best 131k attention/KV point require?`
- comparison_role: `frontier_synthesis`
- proposal_outcome: `decoder_evidence_recorded`
- comparison_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_memory__l2_decoder_attention_kv_memory_131k_capacity_v1.json: decision=decoder_evidence_recorded.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
