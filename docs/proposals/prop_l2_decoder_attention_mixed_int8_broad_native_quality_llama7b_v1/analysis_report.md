# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_decoder_attention_mixed_int8_broad_native_quality_llama7b_v1`
- `candidate_id`: `l2_decoder_attention_mixed_int8_broad_native_quality_llama7b_v1_r2`

## Evaluations Consumed
- `l2_decoder_attention_mixed_int8_broad_native_quality_llama7b_v1_r2`
- `l2_decoder_attention_mixed_int8_broad_native_quality_llama7b_v1_r2_run_a756884b923d650b`
- source commit: `47e6974fc6ffae2e10e5b491bf968a2d5106bfa7`
- review: PR #1007

## Baseline Comparison
- baseline_ref: `None`
- baseline_item_id: `None`
- outcome: `mixed_int8_native_attention_shadow_hold`
- summary: Decoder mixed/int8 native attention quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_broad_native_quality__l2_decoder_attention_mixed_int8_broad_native_quality_llama7b_v1_r2.json: decision=mixed_int8_native_attention_shadow_hold; model_id=mistralai/Mistral-7B-v0.1; attention_heads=32; kv_heads=8; gqa_group_size=4.0; dtype=bfloat16; q_bits=8; k_bits=8; v_bits=8; score_bits=24; weight_bits=16; softmax_mode=float_quantized; comparison_count=64; top1_match_rate=0.96875; topk_contains_rate=1.0; mean_logit_cosine=0.9999025562684435; mean_probability_kl=0.0014115558838723183; max_abs_logit_delta_max=0.53125; next_step=Hold this attention-shadow candidate until safer quantization is proven with a real checkpoint run or broader model sampling.; best_candidate_id=qkv8_float_exact; best_top1_match_rate=1.0; best_topk_contains_rate=1.0; best_mean_logit_cosine=0.9998988400355315; best_mean_probability_kl=0.0012425925766148221; candidate_count=4.

## Result
- result: `iterate`
- confidence level: merged accepted evidence
- estimated optimization room: pending follow-on comparison
- architecture conclusion robustness: staged evidence
- summary: Decoder mixed/int8 native attention quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_broad_native_quality__l2_decoder_attention_mixed_int8_broad_native_quality_llama7b_v1_r2.json: decision=mixed_int8_native_attention_shadow_hold; model_id=mistralai/Mistral-7B-v0.1; attention_heads=32; kv_heads=8; gqa_group_size=4.0; dtype=bfloat16; q_bits=8; k_bits=8; v_bits=8; score_bits=24; weight_bits=16; softmax_mode=float_quantized; comparison_count=64; top1_match_rate=0.96875; topk_contains_rate=1.0; mean_logit_cosine=0.9999025562684435; mean_probability_kl=0.0014115558838723183; max_abs_logit_delta_max=0.53125; next_step=Hold this attention-shadow candidate until safer quantization is proven with a real checkpoint run or broader model sampling.; best_candidate_id=qkv8_float_exact; best_top1_match_rate=1.0; best_topk_contains_rate=1.0; best_mean_logit_cosine=0.9998988400355315; best_mean_probability_kl=0.0012425925766148221; candidate_count=4.

## Failures and Caveats
- no additional caveats recorded during automatic finalization

## Recommendation
- `iterate`
- reason: Decoder mixed/int8 native attention quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_broad_native_quality__l2_decoder_attention_mixed_int8_broad_native_quality_llama7b_v1_r2.json: decision=mixed_int8_native_attention_shadow_hold; model_id=mistralai/Mistral-7B-v0.1; attention_heads=32; kv_heads=8; gqa_group_size=4.0; dtype=bfloat16; q_bits=8; k_bits=8; v_bits=8; score_bits=24; weight_bits=16; softmax_mode=float_quantized; comparison_count=64; top1_match_rate=0.96875; topk_contains_rate=1.0; mean_logit_cosine=0.9999025562684435; mean_probability_kl=0.0014115558838723183; max_abs_logit_delta_max=0.53125; next_step=Hold this attention-shadow candidate until safer quantization is proven with a real checkpoint run or broader model sampling.; best_candidate_id=qkv8_float_exact; best_top1_match_rate=1.0; best_topk_contains_rate=1.0; best_mean_logit_cosine=0.9998988400355315; best_mean_probability_kl=0.0012425925766148221; candidate_count=4.
- next_action: inspect follow-on work after l2_decoder_attention_mixed_int8_broad_native_quality_llama7b_v1_r2
