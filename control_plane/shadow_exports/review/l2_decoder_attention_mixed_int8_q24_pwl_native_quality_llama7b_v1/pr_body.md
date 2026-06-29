## Summary
- item_id: `l2_decoder_attention_mixed_int8_q24_pwl_native_quality_llama7b_v1`
- run_key: `l2_decoder_attention_mixed_int8_q24_pwl_native_quality_llama7b_v1_run_f6300eea3bd1e4c3`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `2/2 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_mixed_int8_q24_pwl_native_quality_llama7b_v1/evaluated.json`
- metrics_rows_count: `0`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_mixed_int8_q24_pwl_native_quality_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_mixed_int8_q24_pwl_native_quality_llama7b_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_mixed_int8_q24_pwl_native_quality_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_mixed_int8_q24_pwl_native_quality_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `d85cc4c3effe9e61aa4b4c4fa2e651e1f191995a`
- review_metadata_source_commit: `4ae37b2faba4f0d2f887f2b96d409a9996329191`

## Evaluation Mode
- evaluation_mode: `quality_gate`
- abstraction_layer: `decoder_attention_mixed_int8_q24_pwl_native_quality`
- comparison_role: `precision_validation`
- expected_direction: `validate_or_reject_q24_pwl_hardware_target`
- expected_reason: `q24/PWL passed bounded generation/NLL evidence in PR #1066; verify it on broader native attention-shadow quality before PPA and frontier recost.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder mixed/int8 native attention quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_q24_pwl_native_quality__l2_decoder_attention_mixed_int8_q24_pwl_native_quality_llama7b_v1.json: decision=mixed_int8_native_attention_shadow_hold; model_id=mistralai/Mistral-7B-v0.1; attention_heads=32; kv_heads=8; gqa_group_size=4.0; dtype=bfloat16; q_bits=8; k_bits=8; v_bits=8; score_bits=24; weight_bits=24; softmax_mode=pwl_recip_lut_q24_bucket8; comparison_count=64; top1_match_rate=0.96875; topk_contains_rate=1.0; mean_logit_cosine=0.9990928666267411; mean_probability_kl=0.013084711899708064; max_abs_logit_delta_max=2.25; next_step=Hold this attention-shadow candidate until safer quantization is proven with a real checkpoint run or broader model sampling.; best_candidate_id=qkv8_float_exact; best_top1_match_rate=1.0; best_topk_contains_rate=1.0; best_mean_logit_cosine=0.9998988400355315; best_mean_probability_kl=0.0012425925766148221; candidate_count=4.`

## Focused Comparison
- primary_question: `Does q8/k8/v8 with q24/PWL reciprocal-LUT softmax preserve native 7B attention-shadow quality relative to float-exact and score24 float controls?`
- comparison_role: `precision_validation`
- proposal_outcome: `mixed_int8_native_attention_shadow_hold`
- comparison_summary: `Decoder mixed/int8 native attention quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_q24_pwl_native_quality__l2_decoder_attention_mixed_int8_q24_pwl_native_quality_llama7b_v1.json: decision=mixed_int8_native_attention_shadow_hold; model_id=mistralai/Mistral-7B-v0.1; attention_heads=32; kv_heads=8; gqa_group_size=4.0; dtype=bfloat16; q_bits=8; k_bits=8; v_bits=8; score_bits=24; weight_bits=24; softmax_mode=pwl_recip_lut_q24_bucket8; comparison_count=64; top1_match_rate=0.96875; topk_contains_rate=1.0; mean_logit_cosine=0.9990928666267411; mean_probability_kl=0.013084711899708064; max_abs_logit_delta_max=2.25; next_step=Hold this attention-shadow candidate until safer quantization is proven with a real checkpoint run or broader model sampling.; best_candidate_id=qkv8_float_exact; best_top1_match_rate=1.0; best_topk_contains_rate=1.0; best_mean_logit_cosine=0.9998988400355315; best_mean_probability_kl=0.0012425925766148221; candidate_count=4.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
