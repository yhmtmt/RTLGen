## Summary
- item_id: `l2_decoder_attention_kv_memory_large_context_v2`
- run_key: `l2_decoder_attention_kv_memory_large_context_v2_run_cefe2f845ea1fbfa`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_kv_memory_large_context_v2/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_kv_memory_large_context_v2.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_kv_memory_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_kv_memory_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_kv_memory_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `0ecf2602e7aa9a9fb64c4fa4c0a9b61b257aea83`
- review_metadata_source_commit: `0ecf2602e7aa9a9fb64c4fa4c0a9b61b257aea83`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_kv_memory`
- comparison_role: `ranking`
- expected_direction: `iterate`
- expected_reason: `Use the larger-context attention/KV sweep to decide whether the next concrete RTL/PPA point should be KV-memory hierarchy, NoC coupling, or attention compute datapath.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_memory__l2_decoder_attention_kv_memory_large_context_v2.json: decision=decoder_evidence_recorded.`

## Focused Comparison
- primary_question: `Across GPT-2-like and larger proxy shapes, which attention substage dominates when sequence length, compute throughput, KV memory tier, NoC hops, KV precision, and MHA/GQA/MQA sharing are varied?`
- comparison_role: `ranking`
- proposal_outcome: `decoder_evidence_recorded`
- comparison_summary: `Decoder quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_memory__l2_decoder_attention_kv_memory_large_context_v2.json: decision=decoder_evidence_recorded.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
