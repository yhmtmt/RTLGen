# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_decoder_attention_mixed_int8_q12_pwl_proxy_audit_llama7b_v1`
- `candidate_id`: `l2_decoder_attention_mixed_int8_q12_pwl_proxy_audit_llama7b_v1`

## Evaluations Consumed
- `l2_decoder_attention_mixed_int8_q12_pwl_proxy_audit_llama7b_v1`
- `l2_decoder_attention_mixed_int8_q12_pwl_proxy_audit_llama7b_v1_run_6d8b014f4068f1d0`
- source commit: `fc78bdce1b0901c66e6be30c9e142402fe57f6b1`
- review: PR #1018

## Baseline Comparison
- baseline_ref: `None`
- baseline_item_id: `None`
- outcome: `q12_pwl_proxy_quality_rejected`
- summary: Decoder mixed/int8 q12/PWL proxy audit evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_q12_pwl_proxy_audit__l2_decoder_attention_mixed_int8_q12_pwl_proxy_audit_llama7b_v1.json: decision=q12_pwl_proxy_quality_rejected; q12_candidate_id=qkv8_q12_pwl_recip_q12_bucket8; q12_decision_status=mixed_int8_native_attention_shadow_hold; q12_top1_match_rate=0.96875; q12_topk_contains_rate=1.0; q12_mean_probability_kl=0.014237412876954065; q12_quality_passed=False; q12_proxy_pass=False; composed_metrics_path=runs/designs/npu_blocks/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_q12_pwl_recip_q12/metrics.csv; composed_value_bits=6; composed_best_critical_path_ns=30.8676; composed_best_total_power_mw=23.7; composed_best_die_area_um2=6250000.0; v8_full_value_metrics_path=runs/designs/activations/attention_kv_full_value_hd64_kv8_v8_tl16_b128_p8_ppc2_w24_a40_wrapper/metrics.csv; v8_full_value_best_critical_path_ns=0.8825; v8_full_value_best_total_power_mw=0.0339; v8_full_value_best_die_area_um2=130100.883025; recommended_next_step=Do not use q12/PWL composed proxy as quality-backed for frontier decisions; improve the qkv8_q12_pwl_recip_q12_bucket8 quality gate and top-1/top-k equality before re-running this audit.

## Result
- result: `iterate`
- confidence level: merged accepted evidence
- estimated optimization room: pending follow-on comparison
- architecture conclusion robustness: staged evidence
- summary: Decoder mixed/int8 q12/PWL proxy audit evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_q12_pwl_proxy_audit__l2_decoder_attention_mixed_int8_q12_pwl_proxy_audit_llama7b_v1.json: decision=q12_pwl_proxy_quality_rejected; q12_candidate_id=qkv8_q12_pwl_recip_q12_bucket8; q12_decision_status=mixed_int8_native_attention_shadow_hold; q12_top1_match_rate=0.96875; q12_topk_contains_rate=1.0; q12_mean_probability_kl=0.014237412876954065; q12_quality_passed=False; q12_proxy_pass=False; composed_metrics_path=runs/designs/npu_blocks/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_q12_pwl_recip_q12/metrics.csv; composed_value_bits=6; composed_best_critical_path_ns=30.8676; composed_best_total_power_mw=23.7; composed_best_die_area_um2=6250000.0; v8_full_value_metrics_path=runs/designs/activations/attention_kv_full_value_hd64_kv8_v8_tl16_b128_p8_ppc2_w24_a40_wrapper/metrics.csv; v8_full_value_best_critical_path_ns=0.8825; v8_full_value_best_total_power_mw=0.0339; v8_full_value_best_die_area_um2=130100.883025; recommended_next_step=Do not use q12/PWL composed proxy as quality-backed for frontier decisions; improve the qkv8_q12_pwl_recip_q12_bucket8 quality gate and top-1/top-k equality before re-running this audit.

## Failures and Caveats
- no additional caveats recorded during automatic finalization

## Recommendation
- `iterate`
- reason: Decoder mixed/int8 q12/PWL proxy audit evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_q12_pwl_proxy_audit__l2_decoder_attention_mixed_int8_q12_pwl_proxy_audit_llama7b_v1.json: decision=q12_pwl_proxy_quality_rejected; q12_candidate_id=qkv8_q12_pwl_recip_q12_bucket8; q12_decision_status=mixed_int8_native_attention_shadow_hold; q12_top1_match_rate=0.96875; q12_topk_contains_rate=1.0; q12_mean_probability_kl=0.014237412876954065; q12_quality_passed=False; q12_proxy_pass=False; composed_metrics_path=runs/designs/npu_blocks/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_q12_pwl_recip_q12/metrics.csv; composed_value_bits=6; composed_best_critical_path_ns=30.8676; composed_best_total_power_mw=23.7; composed_best_die_area_um2=6250000.0; v8_full_value_metrics_path=runs/designs/activations/attention_kv_full_value_hd64_kv8_v8_tl16_b128_p8_ppc2_w24_a40_wrapper/metrics.csv; v8_full_value_best_critical_path_ns=0.8825; v8_full_value_best_total_power_mw=0.0339; v8_full_value_best_die_area_um2=130100.883025; recommended_next_step=Do not use q12/PWL composed proxy as quality-backed for frontier decisions; improve the qkv8_q12_pwl_recip_q12_bucket8 quality gate and top-1/top-k equality before re-running this audit.
- next_action: inspect follow-on work after l2_decoder_attention_mixed_int8_q12_pwl_proxy_audit_llama7b_v1
