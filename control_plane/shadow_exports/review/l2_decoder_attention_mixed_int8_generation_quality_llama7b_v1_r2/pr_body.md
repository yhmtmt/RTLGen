## Summary
- item_id: `l2_decoder_attention_mixed_int8_generation_quality_llama7b_v1_r2`
- run_key: `l2_decoder_attention_mixed_int8_generation_quality_llama7b_v1_r2_run_c718c9bd312dd2ce`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `2/2 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_mixed_int8_generation_quality_llama7b_v1_r2/evaluated.json`
- metrics_rows_count: `0`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_mixed_int8_generation_quality_llama7b_v1_r2.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_mixed_int8_generation_quality_llama7b_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_mixed_int8_generation_quality_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_mixed_int8_generation_quality_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `6f833c9b1a2c90c53ea27009845086320ce28d25`
- review_metadata_source_commit: `6f833c9b1a2c90c53ea27009845086320ce28d25`

## Evaluation Mode
- evaluation_mode: `quality_gate`
- abstraction_layer: `decoder_attention_mixed_int8_generation_quality`
- comparison_role: `generation_quality`
- expected_direction: `unknown`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder native-checkpoint KV quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_generation_quality__l2_decoder_attention_mixed_int8_generation_quality_llama7b_v1_r2.json: decision=mixed_int8_generation_quality_pass; model_id=mistralai/Mistral-7B-v0.1; gqa_group_size=4.0; dtype=bfloat16; next_step=Candidate passed the bounded generation-quality gate; route this score configuration into the native-checkpoint quality evidence stream.`

## Focused Comparison
- primary_question: `Does the score32 mixed/int8 attention path preserve bounded greedy generation and teacher-forced reference-token likelihood on a 7B checkpoint?`
- comparison_role: `generation_quality`
- proposal_outcome: `mixed_int8_generation_quality_pass`
- comparison_summary: `Decoder native-checkpoint KV quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_generation_quality__l2_decoder_attention_mixed_int8_generation_quality_llama7b_v1_r2.json: decision=mixed_int8_generation_quality_pass; model_id=mistralai/Mistral-7B-v0.1; gqa_group_size=4.0; dtype=bfloat16; next_step=Candidate passed the bounded generation-quality gate; route this score configuration into the native-checkpoint quality evidence stream.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
