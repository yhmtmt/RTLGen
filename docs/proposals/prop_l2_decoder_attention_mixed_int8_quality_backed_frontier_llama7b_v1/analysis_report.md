# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_decoder_attention_mixed_int8_quality_backed_frontier_llama7b_v1`
- `candidate_id`: `l2_decoder_attention_mixed_int8_quality_backed_frontier_llama7b_v1`

## Evaluations Consumed
- `l2_decoder_attention_mixed_int8_quality_backed_frontier_llama7b_v1`
- `l2_decoder_attention_mixed_int8_quality_backed_frontier_llama7b_v1_run_aa26060ae07e8159`
- source commit: `427e92c4a71dd4a4c063ed5871876b16e956d559`
- review: PR #1009

## Baseline Comparison
- baseline_ref: `None`
- baseline_item_id: `None`
- outcome: `mixed_int8_quality_backed_frontier_recost_required`
- summary: Decoder mixed/int8 quality-backed frontier evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_quality_backed_frontier__l2_decoder_attention_mixed_int8_quality_backed_frontier_llama7b_v1.json: decision=mixed_int8_quality_backed_frontier_recost_required; quality_passing_candidate_count=1; quality_passing_candidate_ids=['qkv8_float_exact']; quality_best_candidate_id=qkv8_float_exact; quality_best_top1_match_rate=1.0; quality_best_mean_probability_kl=0.0012425925766148221; invalidated_energy_candidate_count=1; old_energy_best_candidate_id=die800_dense_gemm_int8_16x8_k1_p1_rep855_lat1575.37_hbm0.983398_tt1024; old_energy_best_latency_us=1575.373891; old_energy_best_token_throughput_per_s=634.7699461778119; old_energy_best_energy_mj=135.75588466251537; old_energy_best_precision_profile=q8_k8_v6_a24_s8_w8_recip_lut_q10_int8_compute; recommended_next_step=Recompute the Llama7B energy frontier for q8/k8/v8 projection quantization with high-precision or exact score/softmax PPA; do not rank the old s8/w8 reciprocal-LUT energy row.

## Result
- result: `iterate`
- confidence level: merged accepted evidence
- estimated optimization room: pending follow-on comparison
- architecture conclusion robustness: staged evidence
- summary: Decoder mixed/int8 quality-backed frontier evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_quality_backed_frontier__l2_decoder_attention_mixed_int8_quality_backed_frontier_llama7b_v1.json: decision=mixed_int8_quality_backed_frontier_recost_required; quality_passing_candidate_count=1; quality_passing_candidate_ids=['qkv8_float_exact']; quality_best_candidate_id=qkv8_float_exact; quality_best_top1_match_rate=1.0; quality_best_mean_probability_kl=0.0012425925766148221; invalidated_energy_candidate_count=1; old_energy_best_candidate_id=die800_dense_gemm_int8_16x8_k1_p1_rep855_lat1575.37_hbm0.983398_tt1024; old_energy_best_latency_us=1575.373891; old_energy_best_token_throughput_per_s=634.7699461778119; old_energy_best_energy_mj=135.75588466251537; old_energy_best_precision_profile=q8_k8_v6_a24_s8_w8_recip_lut_q10_int8_compute; recommended_next_step=Recompute the Llama7B energy frontier for q8/k8/v8 projection quantization with high-precision or exact score/softmax PPA; do not rank the old s8/w8 reciprocal-LUT energy row.

## Failures and Caveats
- no additional caveats recorded during automatic finalization

## Recommendation
- `iterate`
- reason: Decoder mixed/int8 quality-backed frontier evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_quality_backed_frontier__l2_decoder_attention_mixed_int8_quality_backed_frontier_llama7b_v1.json: decision=mixed_int8_quality_backed_frontier_recost_required; quality_passing_candidate_count=1; quality_passing_candidate_ids=['qkv8_float_exact']; quality_best_candidate_id=qkv8_float_exact; quality_best_top1_match_rate=1.0; quality_best_mean_probability_kl=0.0012425925766148221; invalidated_energy_candidate_count=1; old_energy_best_candidate_id=die800_dense_gemm_int8_16x8_k1_p1_rep855_lat1575.37_hbm0.983398_tt1024; old_energy_best_latency_us=1575.373891; old_energy_best_token_throughput_per_s=634.7699461778119; old_energy_best_energy_mj=135.75588466251537; old_energy_best_precision_profile=q8_k8_v6_a24_s8_w8_recip_lut_q10_int8_compute; recommended_next_step=Recompute the Llama7B energy frontier for q8/k8/v8 projection quantization with high-precision or exact score/softmax PPA; do not rank the old s8/w8 reciprocal-LUT energy row.
- next_action: inspect follow-on work after l2_decoder_attention_mixed_int8_quality_backed_frontier_llama7b_v1
