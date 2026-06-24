# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_decoder_attention_mixed_int8_high_score_boundary_llama7b_v1`
- `candidate_id`: `l2_decoder_attention_mixed_int8_high_score_boundary_llama7b_v1`

## Evaluations Consumed
- `l2_decoder_attention_mixed_int8_high_score_boundary_llama7b_v1`
- `l2_decoder_attention_mixed_int8_high_score_boundary_llama7b_v1_run_4644b3dd2daf2900`
- source commit: `766efa521cd4c39c33d52b3294c381a61ea09c95`
- review: PR #1002

## Baseline Comparison
- baseline_ref: `None`
- baseline_item_id: `None`
- outcome: `mixed_int8_native_attention_shadow_pass`
- summary: Decoder mixed/int8 native attention quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_high_score_boundary__l2_decoder_attention_mixed_int8_high_score_boundary_llama7b_v1.json: decision=mixed_int8_native_attention_shadow_pass; model_id=mistralai/Mistral-7B-v0.1; attention_heads=32; kv_heads=8; gqa_group_size=4.0; dtype=bfloat16; q_bits=8; k_bits=8; v_bits=8; score_bits=24; weight_bits=16; softmax_mode=float_quantized; comparison_count=16; top1_match_rate=1.0; topk_contains_rate=1.0; mean_logit_cosine=0.9999591095634982; mean_probability_kl=0.0005788093087387277; max_abs_logit_delta_max=0.4375; next_step=Proceed to broader mixed/int8 attention native-checkpoint checks before frontier scheduling.; best_candidate_id=score24_float; best_top1_match_rate=1.0; best_topk_contains_rate=1.0; best_mean_logit_cosine=0.9999591095634982; best_mean_probability_kl=0.0005788093087387277; candidate_count=9.

## Result
- result: `iterate`
- confidence level: merged accepted evidence
- estimated optimization room: pending follow-on comparison
- architecture conclusion robustness: staged evidence
- summary: Decoder mixed/int8 native attention quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_high_score_boundary__l2_decoder_attention_mixed_int8_high_score_boundary_llama7b_v1.json: decision=mixed_int8_native_attention_shadow_pass; model_id=mistralai/Mistral-7B-v0.1; attention_heads=32; kv_heads=8; gqa_group_size=4.0; dtype=bfloat16; q_bits=8; k_bits=8; v_bits=8; score_bits=24; weight_bits=16; softmax_mode=float_quantized; comparison_count=16; top1_match_rate=1.0; topk_contains_rate=1.0; mean_logit_cosine=0.9999591095634982; mean_probability_kl=0.0005788093087387277; max_abs_logit_delta_max=0.4375; next_step=Proceed to broader mixed/int8 attention native-checkpoint checks before frontier scheduling.; best_candidate_id=score24_float; best_top1_match_rate=1.0; best_topk_contains_rate=1.0; best_mean_logit_cosine=0.9999591095634982; best_mean_probability_kl=0.0005788093087387277; candidate_count=9.

## Failures and Caveats
- no additional caveats recorded during automatic finalization

## Recommendation
- `iterate`
- reason: Decoder mixed/int8 native attention quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_high_score_boundary__l2_decoder_attention_mixed_int8_high_score_boundary_llama7b_v1.json: decision=mixed_int8_native_attention_shadow_pass; model_id=mistralai/Mistral-7B-v0.1; attention_heads=32; kv_heads=8; gqa_group_size=4.0; dtype=bfloat16; q_bits=8; k_bits=8; v_bits=8; score_bits=24; weight_bits=16; softmax_mode=float_quantized; comparison_count=16; top1_match_rate=1.0; topk_contains_rate=1.0; mean_logit_cosine=0.9999591095634982; mean_probability_kl=0.0005788093087387277; max_abs_logit_delta_max=0.4375; next_step=Proceed to broader mixed/int8 attention native-checkpoint checks before frontier scheduling.; best_candidate_id=score24_float; best_top1_match_rate=1.0; best_topk_contains_rate=1.0; best_mean_logit_cosine=0.9999591095634982; best_mean_probability_kl=0.0005788093087387277; candidate_count=9.
- next_action: inspect follow-on work after l2_decoder_attention_mixed_int8_high_score_boundary_llama7b_v1
