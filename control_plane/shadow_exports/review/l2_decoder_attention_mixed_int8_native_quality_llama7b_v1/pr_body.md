## Summary
- item_id: `l2_decoder_attention_mixed_int8_native_quality_llama7b_v1`
- run_key: `l2_decoder_attention_mixed_int8_native_quality_llama7b_v1_run_3eaa1b95da533690`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `2/2 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_mixed_int8_native_quality_llama7b_v1/evaluated.json`
- metrics_rows_count: `0`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_mixed_int8_native_quality_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_mixed_int8_native_quality_llama7b_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_mixed_int8_native_quality_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_mixed_int8_native_quality_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `00337aa586851731ca563cb01ff22dd588f3de49`
- review_metadata_source_commit: `00337aa586851731ca563cb01ff22dd588f3de49`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_mixed_int8_native_quality`
- comparison_role: `precision_gate`
- expected_direction: `validate_or_reject_mixed_int8_latency_frontier_precision`
- expected_reason: `The mixed/int8 point has much higher token throughput but higher energy and only proxy quality; native checkpoint evidence is required before it can remain a precision-valid latency frontier.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder mixed/int8 native attention quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_native_quality__l2_decoder_attention_mixed_int8_native_quality_llama7b_v1.json: decision=mixed_int8_native_attention_shadow_hold; model_id=mistralai/Mistral-7B-v0.1; attention_heads=32; kv_heads=8; gqa_group_size=4.0; dtype=bfloat16; q_bits=8; k_bits=8; v_bits=8; score_bits=8; weight_bits=8; softmax_mode=rtl_recip_lut_q8; comparison_count=16; top1_match_rate=0.625; topk_contains_rate=0.75; mean_logit_cosine=0.9438919461553094; mean_probability_kl=1.0139418966751363; max_abs_logit_delta_max=10.125; next_step=Hold this attention-shadow candidate until safer quantization is proven with a real checkpoint run or broader model sampling.`

## Focused Comparison
- primary_question: `Does the mixed/int8 softmax-recip attention path preserve 7B-class checkpoint final-logit rankings closely enough to keep the mixed/int8 point as a precision-valid latency frontier?`
- comparison_role: `precision_gate`
- proposal_outcome: `mixed_int8_native_attention_shadow_hold`
- comparison_summary: `Decoder mixed/int8 native attention quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_native_quality__l2_decoder_attention_mixed_int8_native_quality_llama7b_v1.json: decision=mixed_int8_native_attention_shadow_hold; model_id=mistralai/Mistral-7B-v0.1; attention_heads=32; kv_heads=8; gqa_group_size=4.0; dtype=bfloat16; q_bits=8; k_bits=8; v_bits=8; score_bits=8; weight_bits=8; softmax_mode=rtl_recip_lut_q8; comparison_count=16; top1_match_rate=0.625; topk_contains_rate=0.75; mean_logit_cosine=0.9438919461553094; mean_probability_kl=1.0139418966751363; max_abs_logit_delta_max=10.125; next_step=Hold this attention-shadow candidate until safer quantization is proven with a real checkpoint run or broader model sampling.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
