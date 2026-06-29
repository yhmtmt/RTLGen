# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_decoder_attention_mixed_int8_score_precision_recovery_llama7b_v1`
- `candidate_id`: `l2_decoder_attention_mixed_int8_score_precision_recovery_llama7b_v1_r2`

## Evaluations Consumed
- `l2_decoder_attention_mixed_int8_score_precision_recovery_llama7b_v1_r2`
- `l2_decoder_attention_mixed_int8_score_precision_recovery_llama7b_v1_r2_run_b003994effb2b0c5`
- source commit: `4cbba8c266e16f2bff24d5e2e54eab0461ab90c9`
- review: PR #1073

## Baseline Comparison
- baseline_ref: `None`
- baseline_item_id: `None`
- outcome: `mixed_int8_native_attention_shadow_hold`
- summary: Decoder mixed/int8 native attention quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_score_precision_recovery__l2_decoder_attention_mixed_int8_score_precision_recovery_llama7b_v1_r2.json: decision=mixed_int8_native_attention_shadow_hold; model_id=mistralai/Mistral-7B-v0.1; attention_heads=32; kv_heads=8; gqa_group_size=4.0; dtype=bfloat16; q_bits=8; k_bits=8; v_bits=8; score_bits=32; weight_bits=16; softmax_mode=float_quantized; comparison_count=64; top1_match_rate=0.984375; topk_contains_rate=1.0; mean_logit_cosine=0.9998751206989908; mean_probability_kl=0.0017210117614710435; max_abs_logit_delta_max=0.6875; next_step=Hold this attention-shadow candidate until safer quantization is proven with a real checkpoint run or broader model sampling.; best_candidate_id=qkv8_float_exact; best_top1_match_rate=1.0; best_topk_contains_rate=1.0; best_mean_logit_cosine=0.9998988400355315; best_mean_probability_kl=0.0012425925766148221; candidate_count=7.

## Result
- result: `iterate`
- confidence level: merged accepted evidence
- estimated optimization room: pending follow-on comparison
- architecture conclusion robustness: staged evidence
- summary: Decoder mixed/int8 native attention quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_score_precision_recovery__l2_decoder_attention_mixed_int8_score_precision_recovery_llama7b_v1_r2.json: decision=mixed_int8_native_attention_shadow_hold; model_id=mistralai/Mistral-7B-v0.1; attention_heads=32; kv_heads=8; gqa_group_size=4.0; dtype=bfloat16; q_bits=8; k_bits=8; v_bits=8; score_bits=32; weight_bits=16; softmax_mode=float_quantized; comparison_count=64; top1_match_rate=0.984375; topk_contains_rate=1.0; mean_logit_cosine=0.9998751206989908; mean_probability_kl=0.0017210117614710435; max_abs_logit_delta_max=0.6875; next_step=Hold this attention-shadow candidate until safer quantization is proven with a real checkpoint run or broader model sampling.; best_candidate_id=qkv8_float_exact; best_top1_match_rate=1.0; best_topk_contains_rate=1.0; best_mean_logit_cosine=0.9998988400355315; best_mean_probability_kl=0.0012425925766148221; candidate_count=7.

## Failures and Caveats
- no additional caveats recorded during automatic finalization

## Recommendation
- `iterate`
- reason: Decoder mixed/int8 native attention quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_score_precision_recovery__l2_decoder_attention_mixed_int8_score_precision_recovery_llama7b_v1_r2.json: decision=mixed_int8_native_attention_shadow_hold; model_id=mistralai/Mistral-7B-v0.1; attention_heads=32; kv_heads=8; gqa_group_size=4.0; dtype=bfloat16; q_bits=8; k_bits=8; v_bits=8; score_bits=32; weight_bits=16; softmax_mode=float_quantized; comparison_count=64; top1_match_rate=0.984375; topk_contains_rate=1.0; mean_logit_cosine=0.9998751206989908; mean_probability_kl=0.0017210117614710435; max_abs_logit_delta_max=0.6875; next_step=Hold this attention-shadow candidate until safer quantization is proven with a real checkpoint run or broader model sampling.; best_candidate_id=qkv8_float_exact; best_top1_match_rate=1.0; best_topk_contains_rate=1.0; best_mean_logit_cosine=0.9998988400355315; best_mean_probability_kl=0.0012425925766148221; candidate_count=7.
- next_action: inspect follow-on work after l2_decoder_attention_mixed_int8_score_precision_recovery_llama7b_v1_r2
