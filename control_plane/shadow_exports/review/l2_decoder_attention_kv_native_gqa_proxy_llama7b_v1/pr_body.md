## Summary
- item_id: `l2_decoder_attention_kv_native_gqa_proxy_llama7b_v1`
- run_key: `l2_decoder_attention_kv_native_gqa_proxy_llama7b_v1_run_cd6063c403d39f20`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_kv_native_gqa_proxy_llama7b_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_kv_native_gqa_proxy_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_kv_native_gqa_proxy_llama7b_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_kv_native_gqa_proxy_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_kv_native_gqa_proxy_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `1fd04443454294c4fc8b97800dd985e00f7c3967`
- review_metadata_source_commit: `1fd04443454294c4fc8b97800dd985e00f7c3967`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_kv_native_gqa_proxy`
- comparison_role: `frontier_synthesis`
- expected_direction: `iterate`
- expected_reason: `Use the native-sharing proxy to decide whether GQA8/KV4 should advance to a model-native or QAT quality run.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_native_gqa_proxy__l2_decoder_attention_kv_native_gqa_proxy_llama7b_v1.json: decision=decoder_evidence_recorded.`

## Focused Comparison
- primary_question: `Do native GQA8/KV8 and native GQA8/KV4 preserve attention top-1, retrieval hits, distribution shape, and value outputs relative to a same-sharing KV16 reference?`
- comparison_role: `frontier_synthesis`
- proposal_outcome: `decoder_evidence_recorded`
- comparison_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_native_gqa_proxy__l2_decoder_attention_kv_native_gqa_proxy_llama7b_v1.json: decision=decoder_evidence_recorded.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
