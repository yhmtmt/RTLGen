# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_decoder_attention_mixed_int8_score_margin_audit_llama7b_v1`
- `candidate_id`: `l2_decoder_attention_mixed_int8_score_margin_audit_llama7b_v1_r2`

## Evaluations Consumed
- `l2_decoder_attention_mixed_int8_score_margin_audit_llama7b_v1_r2`
- `l2_decoder_attention_mixed_int8_score_margin_audit_llama7b_v1_r2_run_a39a4076a4a85acc`
- source commit: `e325e0b2ca3ab4c2da45d9e8a188638a9e7f8c33`
- review: PR #1025

## Baseline Comparison
- baseline_ref: `None`
- baseline_item_id: `None`
- outcome: `score_margin_audit_narrow_margin_hold`
- summary: Decoder mixed/int8 score-margin audit recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_score_margin_audit__l2_decoder_attention_mixed_int8_score_margin_audit_llama7b_v1_r2.json: decision=score_margin_audit_narrow_margin_hold; candidate_count=6; primary_candidate_id=score32_float; primary_comparison_count=64; primary_top1_miss_count=2; primary_top1_match_rate=0.96875; primary_topk_contains_rate=1.0; primary_miss_topk_contains_rate=1.0; primary_miss_mean_reference_margin=0.125; primary_miss_mean_probability_kl=0.002996711308909919; primary_miss_mean_logit_cosine=0.9999012209502798; primary_miss_max_abs_logit_delta=0.34375; next_step=The misses are concentrated in narrow-margin regions; keep this recovery path blocked until bounded top-k and follow-up scoring checks show stable high-margin behavior.

## Result
- result: `iterate`
- confidence level: merged accepted evidence
- estimated optimization room: pending follow-on comparison
- architecture conclusion robustness: staged evidence
- summary: Decoder mixed/int8 score-margin audit recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_score_margin_audit__l2_decoder_attention_mixed_int8_score_margin_audit_llama7b_v1_r2.json: decision=score_margin_audit_narrow_margin_hold; candidate_count=6; primary_candidate_id=score32_float; primary_comparison_count=64; primary_top1_miss_count=2; primary_top1_match_rate=0.96875; primary_topk_contains_rate=1.0; primary_miss_topk_contains_rate=1.0; primary_miss_mean_reference_margin=0.125; primary_miss_mean_probability_kl=0.002996711308909919; primary_miss_mean_logit_cosine=0.9999012209502798; primary_miss_max_abs_logit_delta=0.34375; next_step=The misses are concentrated in narrow-margin regions; keep this recovery path blocked until bounded top-k and follow-up scoring checks show stable high-margin behavior.

## Failures and Caveats
- no additional caveats recorded during automatic finalization

## Recommendation
- `iterate`
- reason: Decoder mixed/int8 score-margin audit recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_score_margin_audit__l2_decoder_attention_mixed_int8_score_margin_audit_llama7b_v1_r2.json: decision=score_margin_audit_narrow_margin_hold; candidate_count=6; primary_candidate_id=score32_float; primary_comparison_count=64; primary_top1_miss_count=2; primary_top1_match_rate=0.96875; primary_topk_contains_rate=1.0; primary_miss_topk_contains_rate=1.0; primary_miss_mean_reference_margin=0.125; primary_miss_mean_probability_kl=0.002996711308909919; primary_miss_mean_logit_cosine=0.9999012209502798; primary_miss_max_abs_logit_delta=0.34375; next_step=The misses are concentrated in narrow-margin regions; keep this recovery path blocked until bounded top-k and follow-up scoring checks show stable high-margin behavior.
- next_action: inspect follow-on work after l2_decoder_attention_mixed_int8_score_margin_audit_llama7b_v1_r2
