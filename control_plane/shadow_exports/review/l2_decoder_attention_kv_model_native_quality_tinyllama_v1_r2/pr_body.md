## Summary
- item_id: `l2_decoder_attention_kv_model_native_quality_tinyllama_v1_r2`
- run_key: `l2_decoder_attention_kv_model_native_quality_tinyllama_v1_r2_run_764cc492574688b7`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_kv_model_native_quality_tinyllama_v1_r2/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_kv_model_native_quality_tinyllama_v1_r2.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_kv_model_native_quality_tinyllama_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_kv_model_native_quality_tinyllama_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_kv_model_native_quality_tinyllama_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `9604548806761a0e1cefdf273ff960660504e6ec`
- review_metadata_source_commit: `9604548806761a0e1cefdf273ff960660504e6ec`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_kv_model_native_quality`
- comparison_role: `frontier_synthesis`
- expected_direction: `iterate`
- expected_reason: `Use native trained-checkpoint KV feedback quality to decide whether the frontier should proceed to larger 7B-class/QAT confirmation or retreat to KV8/safer formats.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_model_native_quality__l2_decoder_attention_kv_model_native_quality_tinyllama_v1_r2.json: decision=decoder_evidence_recorded.`

## Focused Comparison
- primary_question: `Does post-training KV4 cache quantization preserve next-token ranking on a trained native-GQA checkpoint closely enough to keep GQA8/KV4 on the LLaMA-class frontier before QAT?`
- comparison_role: `frontier_synthesis`
- proposal_outcome: `decoder_evidence_recorded`
- comparison_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_model_native_quality__l2_decoder_attention_kv_model_native_quality_tinyllama_v1_r2.json: decision=decoder_evidence_recorded.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
