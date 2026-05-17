## Summary
- item_id: `l2_decoder_attention_kv_physical_hbm_memory_noc_llama7b_v1`
- run_key: `l2_decoder_attention_kv_physical_hbm_memory_noc_llama7b_v1_run_78ecb788959c7790`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_kv_physical_hbm_memory_noc_llama7b_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_kv_physical_hbm_memory_noc_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_kv_physical_hbm_memory_noc_llama7b_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_kv_physical_hbm_memory_noc_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_kv_physical_hbm_memory_noc_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `e1785713f19a572eeb0ae1e02bf9473303327592`
- review_metadata_source_commit: `e1785713f19a572eeb0ae1e02bf9473303327592`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_kv_physical_hbm_memory_noc`
- comparison_role: `frontier_synthesis`
- expected_direction: `iterate`
- expected_reason: `If best 131k points remain HBM-bound, prioritize HBM service and KV compression/QAT; if SRAM/NoC dominates at large die sizes, select those points for detailed memory hierarchy modeling.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_physical_hbm_memory_noc__l2_decoder_attention_kv_physical_hbm_memory_noc_llama7b_v1.json: decision=decoder_evidence_recorded.`

## Focused Comparison
- primary_question: `How does the best memory and NoC architecture move with die size when llama7b_proxy is restricted to quality-backed native-GQA KV8/KV16 at 131k context?`
- comparison_role: `frontier_synthesis`
- proposal_outcome: `decoder_evidence_recorded`
- comparison_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_physical_hbm_memory_noc__l2_decoder_attention_kv_physical_hbm_memory_noc_llama7b_v1.json: decision=decoder_evidence_recorded.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
