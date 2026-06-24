# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_decoder_attention_mixed_int8_native_quality_llama7b_v1`
- `candidate_id`: `l2_decoder_attention_mixed_int8_native_quality_llama7b_v1`

## Evaluations Consumed
- `l2_decoder_attention_mixed_int8_native_quality_llama7b_v1`
- `l2_decoder_attention_mixed_int8_native_quality_llama7b_v1_run_3eaa1b95da533690`
- source commit: `00337aa586851731ca563cb01ff22dd588f3de49`
- review: PR #996

## Baseline Comparison
- baseline_ref: `None`
- baseline_item_id: `None`
- outcome: `mixed_int8_native_attention_shadow_hold`
- summary: Decoder mixed/int8 native attention quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_native_quality__l2_decoder_attention_mixed_int8_native_quality_llama7b_v1.json: decision=mixed_int8_native_attention_shadow_hold; model_id=mistralai/Mistral-7B-v0.1; attention_heads=32; kv_heads=8; gqa_group_size=4.0; dtype=bfloat16; q_bits=8; k_bits=8; v_bits=8; score_bits=8; weight_bits=8; softmax_mode=rtl_recip_lut_q8; comparison_count=16; top1_match_rate=0.625; topk_contains_rate=0.75; mean_logit_cosine=0.9438919461553094; mean_probability_kl=1.0139418966751363; max_abs_logit_delta_max=10.125; next_step=Hold this attention-shadow candidate until safer quantization is proven with a real checkpoint run or broader model sampling.

## Result
- result: `iterate`
- confidence level: merged accepted evidence
- estimated optimization room: pending follow-on comparison
- architecture conclusion robustness: staged evidence
- summary: Decoder mixed/int8 native attention quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_native_quality__l2_decoder_attention_mixed_int8_native_quality_llama7b_v1.json: decision=mixed_int8_native_attention_shadow_hold; model_id=mistralai/Mistral-7B-v0.1; attention_heads=32; kv_heads=8; gqa_group_size=4.0; dtype=bfloat16; q_bits=8; k_bits=8; v_bits=8; score_bits=8; weight_bits=8; softmax_mode=rtl_recip_lut_q8; comparison_count=16; top1_match_rate=0.625; topk_contains_rate=0.75; mean_logit_cosine=0.9438919461553094; mean_probability_kl=1.0139418966751363; max_abs_logit_delta_max=10.125; next_step=Hold this attention-shadow candidate until safer quantization is proven with a real checkpoint run or broader model sampling.

## Failures and Caveats
- no additional caveats recorded during automatic finalization

## Recommendation
- `iterate`
- reason: Decoder mixed/int8 native attention quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_native_quality__l2_decoder_attention_mixed_int8_native_quality_llama7b_v1.json: decision=mixed_int8_native_attention_shadow_hold; model_id=mistralai/Mistral-7B-v0.1; attention_heads=32; kv_heads=8; gqa_group_size=4.0; dtype=bfloat16; q_bits=8; k_bits=8; v_bits=8; score_bits=8; weight_bits=8; softmax_mode=rtl_recip_lut_q8; comparison_count=16; top1_match_rate=0.625; topk_contains_rate=0.75; mean_logit_cosine=0.9438919461553094; mean_probability_kl=1.0139418966751363; max_abs_logit_delta_max=10.125; next_step=Hold this attention-shadow candidate until safer quantization is proven with a real checkpoint run or broader model sampling.
- next_action: inspect follow-on work after l2_decoder_attention_mixed_int8_native_quality_llama7b_v1
