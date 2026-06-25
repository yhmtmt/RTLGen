## Summary
- item_id: `l2_decoder_attention_mixed_int8_score_precision_recovery_llama7b_v1`
- run_key: `l2_decoder_attention_mixed_int8_score_precision_recovery_llama7b_v1_run_c49ecf14ba9e7cb6`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `2/2 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_mixed_int8_score_precision_recovery_llama7b_v1/evaluated.json`
- metrics_rows_count: `0`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_mixed_int8_score_precision_recovery_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_mixed_int8_score_precision_recovery_llama7b_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_mixed_int8_score_precision_recovery_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_mixed_int8_score_precision_recovery_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `68d78c106c9d3b4891657cc2aa259171397aa4ab`
- review_metadata_source_commit: `24c95f827703620a309e3455e06b87ffda7de766`

## Evaluation Mode
- evaluation_mode: `quality_gate`
- abstraction_layer: `decoder_attention_mixed_int8_score_precision_recovery`
- comparison_role: `precision_recovery`
- expected_direction: `recover_quality_gate_or_hold_for_recost`
- expected_reason: `Identify whether score32 or high-precision PWL reciprocal variants recover attention-shadow quality before any PPA recosting.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder mixed/int8 native attention quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_score_precision_recovery__l2_decoder_attention_mixed_int8_score_precision_recovery_llama7b_v1.json: decision=mixed_int8_native_attention_shadow_hold; model_id=mistralai/Mistral-7B-v0.1; attention_heads=32; kv_heads=8; gqa_group_size=4.0; dtype=bfloat16; q_bits=8; k_bits=8; v_bits=8; score_bits=32; weight_bits=16; softmax_mode=float_quantized; comparison_count=64; top1_match_rate=0.96875; topk_contains_rate=1.0; mean_logit_cosine=0.9999025562684435; mean_probability_kl=0.0014115558838723183; max_abs_logit_delta_max=0.53125; next_step=Hold this attention-shadow candidate until safer quantization is proven with a real checkpoint run or broader model sampling.; best_candidate_id=qkv8_float_exact; best_top1_match_rate=1.0; best_topk_contains_rate=1.0; best_mean_logit_cosine=0.9998988400355315; best_mean_probability_kl=0.0012425925766148221; candidate_count=6.`

## Focused Comparison
- primary_question: `Can score-precision recovery or higher-precision PWL-reciprocal settings recover quality while keeping the job as an evidence-only checkpoint for ranking preparation?`
- comparison_role: `precision_recovery`
- proposal_outcome: `mixed_int8_native_attention_shadow_hold`
- comparison_summary: `Decoder mixed/int8 native attention quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_score_precision_recovery__l2_decoder_attention_mixed_int8_score_precision_recovery_llama7b_v1.json: decision=mixed_int8_native_attention_shadow_hold; model_id=mistralai/Mistral-7B-v0.1; attention_heads=32; kv_heads=8; gqa_group_size=4.0; dtype=bfloat16; q_bits=8; k_bits=8; v_bits=8; score_bits=32; weight_bits=16; softmax_mode=float_quantized; comparison_count=64; top1_match_rate=0.96875; topk_contains_rate=1.0; mean_logit_cosine=0.9999025562684435; mean_probability_kl=0.0014115558838723183; max_abs_logit_delta_max=0.53125; next_step=Hold this attention-shadow candidate until safer quantization is proven with a real checkpoint run or broader model sampling.; best_candidate_id=qkv8_float_exact; best_top1_match_rate=1.0; best_topk_contains_rate=1.0; best_mean_logit_cosine=0.9998988400355315; best_mean_probability_kl=0.0012425925766148221; candidate_count=6.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Submission Recovery
- submission_failure_count: `0`
- retry_request_count: `0`
- final_submission_pr: `https://github.com/yhmtmt/RTLGen/pull/1020`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
