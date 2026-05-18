## Summary
- item_id: `l2_decoder_attention_kv_physical_hbm_compute_sensitivity_llama7b_v1`
- run_key: `l2_decoder_attention_kv_physical_hbm_compute_sensitivity_llama7b_v1_run_0ab976e60250e88e`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_kv_physical_hbm_compute_sensitivity_llama7b_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_kv_physical_hbm_compute_sensitivity_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_kv_physical_hbm_compute_sensitivity_llama7b_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_kv_physical_hbm_compute_sensitivity_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_kv_physical_hbm_compute_sensitivity_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `fb0eedb654ac6e27bbecb438dd12b5869cf31017`
- review_metadata_source_commit: `fb0eedb654ac6e27bbecb438dd12b5869cf31017`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_kv_physical_hbm_compute_sensitivity`
- comparison_role: `frontier_synthesis`
- expected_direction: `iterate`
- expected_reason: `If lower compute points remain HBM-bound with similar latency, schedule RTL/PPA for smaller compute arrays; if tile attention becomes dominant, keep compute near the transition point.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_physical_hbm_compute_sensitivity__l2_decoder_attention_kv_physical_hbm_compute_sensitivity_llama7b_v1.json: decision=decoder_evidence_recorded.`

## Focused Comparison
- primary_question: `What is the smallest MAC/cycle and vector-op/cycle throughput point that keeps the selected llama7b_proxy 131k KV8 memory/HBM frontier memory-bound?`
- comparison_role: `frontier_synthesis`
- proposal_outcome: `decoder_evidence_recorded`
- comparison_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_physical_hbm_compute_sensitivity__l2_decoder_attention_kv_physical_hbm_compute_sensitivity_llama7b_v1.json: decision=decoder_evidence_recorded.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
