# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_decoder_attention_mixed_int8_score_boundary_llama7b_v1`
- `candidate_id`: `l2_decoder_attention_mixed_int8_score_boundary_llama7b_v1`

## Evaluations Consumed
- `l2_decoder_attention_mixed_int8_score_boundary_llama7b_v1`
- `l2_decoder_attention_mixed_int8_score_boundary_llama7b_v1_run_235802f7765ff1b0`
- source commit: `48d3415f3b62bd1ffc58c7acc0b4f8c932b7e722`
- review: PR #1000

## Baseline Comparison
- baseline_ref: `None`
- baseline_item_id: `None`
- outcome: `mixed_int8_native_attention_shadow_hold`
- summary: Decoder mixed/int8 native attention quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_score_boundary__l2_decoder_attention_mixed_int8_score_boundary_llama7b_v1.json: decision=mixed_int8_native_attention_shadow_hold; model_id=mistralai/Mistral-7B-v0.1; attention_heads=32; kv_heads=8; gqa_group_size=4.0; dtype=bfloat16; q_bits=8; k_bits=8; v_bits=8; score_bits=12; weight_bits=8; softmax_mode=rtl_exact; comparison_count=16; top1_match_rate=0.5625; topk_contains_rate=0.75; mean_logit_cosine=0.9388521451215864; mean_probability_kl=0.988032547806978; max_abs_logit_delta_max=10.3984375; next_step=Hold this attention-shadow candidate until safer quantization is proven with a real checkpoint run or broader model sampling.; best_candidate_id=score10_float; best_top1_match_rate=0.6875; best_topk_contains_rate=1.0; best_mean_logit_cosine=0.9764499680089153; best_mean_probability_kl=0.4291034575331289; candidate_count=8.

## Result
- result: `iterate`
- confidence level: merged accepted evidence
- estimated optimization room: pending follow-on comparison
- architecture conclusion robustness: staged evidence
- summary: Decoder mixed/int8 native attention quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_score_boundary__l2_decoder_attention_mixed_int8_score_boundary_llama7b_v1.json: decision=mixed_int8_native_attention_shadow_hold; model_id=mistralai/Mistral-7B-v0.1; attention_heads=32; kv_heads=8; gqa_group_size=4.0; dtype=bfloat16; q_bits=8; k_bits=8; v_bits=8; score_bits=12; weight_bits=8; softmax_mode=rtl_exact; comparison_count=16; top1_match_rate=0.5625; topk_contains_rate=0.75; mean_logit_cosine=0.9388521451215864; mean_probability_kl=0.988032547806978; max_abs_logit_delta_max=10.3984375; next_step=Hold this attention-shadow candidate until safer quantization is proven with a real checkpoint run or broader model sampling.; best_candidate_id=score10_float; best_top1_match_rate=0.6875; best_topk_contains_rate=1.0; best_mean_logit_cosine=0.9764499680089153; best_mean_probability_kl=0.4291034575331289; candidate_count=8.

## Failures and Caveats
- no additional caveats recorded during automatic finalization

## Recommendation
- `iterate`
- reason: Decoder mixed/int8 native attention quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_score_boundary__l2_decoder_attention_mixed_int8_score_boundary_llama7b_v1.json: decision=mixed_int8_native_attention_shadow_hold; model_id=mistralai/Mistral-7B-v0.1; attention_heads=32; kv_heads=8; gqa_group_size=4.0; dtype=bfloat16; q_bits=8; k_bits=8; v_bits=8; score_bits=12; weight_bits=8; softmax_mode=rtl_exact; comparison_count=16; top1_match_rate=0.5625; topk_contains_rate=0.75; mean_logit_cosine=0.9388521451215864; mean_probability_kl=0.988032547806978; max_abs_logit_delta_max=10.3984375; next_step=Hold this attention-shadow candidate until safer quantization is proven with a real checkpoint run or broader model sampling.; best_candidate_id=score10_float; best_top1_match_rate=0.6875; best_topk_contains_rate=1.0; best_mean_logit_cosine=0.9764499680089153; best_mean_probability_kl=0.4291034575331289; candidate_count=8.
- next_action: inspect follow-on work after l2_decoder_attention_mixed_int8_score_boundary_llama7b_v1
