# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_decoder_attention_mixed_int8_quality_energy_frontier_llama7b_v1`
- `candidate_id`: `l2_decoder_attention_mixed_int8_quality_energy_frontier_llama7b_v1`

## Evaluations Consumed
- `l2_decoder_attention_mixed_int8_quality_energy_frontier_llama7b_v1`
- `l2_decoder_attention_mixed_int8_quality_energy_frontier_llama7b_v1_run_f98c514043c1cafa`
- source commit: `aee481ec8ebcf4cb07ee75b731ffdb48994c9aa2`
- review: PR #1076

## Baseline Comparison
- baseline_ref: `None`
- baseline_item_id: `None`
- outcome: `mixed_int8_quality_energy_frontier_composed_measurement_required`
- summary: Decoder mixed/int8 quality/energy frontier evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_quality_energy_frontier__l2_decoder_attention_mixed_int8_quality_energy_frontier_llama7b_v1.json: decision=mixed_int8_quality_energy_frontier_composed_measurement_required; quality_best_candidate_id=qkv8_float_exact; quality_best_top1_match_rate=1.0; score32_top1_match_rate=0.984375; q24_pwl_top1_match_rate=0.96875; best_fp16_softmax_proxy_candidate_id=qkv8_float_exact_fp16_softmax_nm2_proxy; best_fp16_softmax_proxy_critical_path_ns=5.476841177082706; best_fp16_softmax_proxy_die_area_um2=2250000.0; best_fp16_softmax_proxy_total_power_mw=0.189074; non_quality_backed_measured_recost_count=2; recommended_next_step=Measure a composed q8/k8/v8 attention wrapper that keeps qkv8_float_exact quality semantics and substitutes a floating/near-exact softmax datapath; do not rank score32 exact-div or PWL rows as quality-backed frontier points.

## Result
- result: `iterate`
- confidence level: merged accepted evidence
- estimated optimization room: pending follow-on comparison
- architecture conclusion robustness: staged evidence
- summary: Decoder mixed/int8 quality/energy frontier evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_quality_energy_frontier__l2_decoder_attention_mixed_int8_quality_energy_frontier_llama7b_v1.json: decision=mixed_int8_quality_energy_frontier_composed_measurement_required; quality_best_candidate_id=qkv8_float_exact; quality_best_top1_match_rate=1.0; score32_top1_match_rate=0.984375; q24_pwl_top1_match_rate=0.96875; best_fp16_softmax_proxy_candidate_id=qkv8_float_exact_fp16_softmax_nm2_proxy; best_fp16_softmax_proxy_critical_path_ns=5.476841177082706; best_fp16_softmax_proxy_die_area_um2=2250000.0; best_fp16_softmax_proxy_total_power_mw=0.189074; non_quality_backed_measured_recost_count=2; recommended_next_step=Measure a composed q8/k8/v8 attention wrapper that keeps qkv8_float_exact quality semantics and substitutes a floating/near-exact softmax datapath; do not rank score32 exact-div or PWL rows as quality-backed frontier points.

## Failures and Caveats
- no additional caveats recorded during automatic finalization

## Recommendation
- `iterate`
- reason: Decoder mixed/int8 quality/energy frontier evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_quality_energy_frontier__l2_decoder_attention_mixed_int8_quality_energy_frontier_llama7b_v1.json: decision=mixed_int8_quality_energy_frontier_composed_measurement_required; quality_best_candidate_id=qkv8_float_exact; quality_best_top1_match_rate=1.0; score32_top1_match_rate=0.984375; q24_pwl_top1_match_rate=0.96875; best_fp16_softmax_proxy_candidate_id=qkv8_float_exact_fp16_softmax_nm2_proxy; best_fp16_softmax_proxy_critical_path_ns=5.476841177082706; best_fp16_softmax_proxy_die_area_um2=2250000.0; best_fp16_softmax_proxy_total_power_mw=0.189074; non_quality_backed_measured_recost_count=2; recommended_next_step=Measure a composed q8/k8/v8 attention wrapper that keeps qkv8_float_exact quality semantics and substitutes a floating/near-exact softmax datapath; do not rank score32 exact-div or PWL rows as quality-backed frontier points.
- next_action: inspect follow-on work after l2_decoder_attention_mixed_int8_quality_energy_frontier_llama7b_v1
