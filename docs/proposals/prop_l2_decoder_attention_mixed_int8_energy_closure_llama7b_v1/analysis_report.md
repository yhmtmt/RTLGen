# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_decoder_attention_mixed_int8_energy_closure_llama7b_v1`
- `candidate_id`: `l2_decoder_attention_mixed_int8_energy_closure_llama7b_v1_r2`

## Evaluations Consumed
- `l2_decoder_attention_mixed_int8_energy_closure_llama7b_v1_r2`
- `l2_decoder_attention_mixed_int8_energy_closure_llama7b_v1_r2_run_8ff0cb50a3908ff7`
- source commit: `44b3a813f2668c50708e2b8b873a6b0af4844802`
- review: PR #993

## Baseline Comparison
- baseline_ref: `None`
- baseline_item_id: `None`
- outcome: `mixed_precision_int8_compute_improves_latency_not_energy`
- summary: Decoder mixed/int8 energy closure evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_energy_closure__l2_decoder_attention_mixed_int8_energy_closure_llama7b_v1_r2.json: decision=mixed_precision_int8_compute_improves_latency_not_energy; source_rows_used=3; physical_feasible_rows=3; best_requested_mode=dual_mac; best_requested_adjusted_latency_us_if_feasible=1575.373891; best_requested_substituted_compute_arch=dense_gemm_int8_16x8_k1_p1; best_requested_substituted_compute_area_um2=89549280.0; best_requested_substituted_compute_power_mw=974.7; best_candidate_id=die800_dense_gemm_int8_16x8_k1_p1_rep855_lat1575.37_hbm0.983398_tt1024; best_latency_us=1575.373891; best_token_throughput_per_s=634.7699461778119; best_energy_mj=135.75588466251537; best_die_area_mm2=800.0; best_dominant_energy_component=hbm; recommended_next_step=keep exact-FP16 V3 as the energy baseline and use mixed/int8 as the latency frontier pending real-checkpoint quality validation.

## Result
- result: `iterate`
- confidence level: merged accepted evidence
- estimated optimization room: pending follow-on comparison
- architecture conclusion robustness: staged evidence
- summary: Decoder mixed/int8 energy closure evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_energy_closure__l2_decoder_attention_mixed_int8_energy_closure_llama7b_v1_r2.json: decision=mixed_precision_int8_compute_improves_latency_not_energy; source_rows_used=3; physical_feasible_rows=3; best_requested_mode=dual_mac; best_requested_adjusted_latency_us_if_feasible=1575.373891; best_requested_substituted_compute_arch=dense_gemm_int8_16x8_k1_p1; best_requested_substituted_compute_area_um2=89549280.0; best_requested_substituted_compute_power_mw=974.7; best_candidate_id=die800_dense_gemm_int8_16x8_k1_p1_rep855_lat1575.37_hbm0.983398_tt1024; best_latency_us=1575.373891; best_token_throughput_per_s=634.7699461778119; best_energy_mj=135.75588466251537; best_die_area_mm2=800.0; best_dominant_energy_component=hbm; recommended_next_step=keep exact-FP16 V3 as the energy baseline and use mixed/int8 as the latency frontier pending real-checkpoint quality validation.

## Failures and Caveats
- no additional caveats recorded during automatic finalization

## Recommendation
- `iterate`
- reason: Decoder mixed/int8 energy closure evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_energy_closure__l2_decoder_attention_mixed_int8_energy_closure_llama7b_v1_r2.json: decision=mixed_precision_int8_compute_improves_latency_not_energy; source_rows_used=3; physical_feasible_rows=3; best_requested_mode=dual_mac; best_requested_adjusted_latency_us_if_feasible=1575.373891; best_requested_substituted_compute_arch=dense_gemm_int8_16x8_k1_p1; best_requested_substituted_compute_area_um2=89549280.0; best_requested_substituted_compute_power_mw=974.7; best_candidate_id=die800_dense_gemm_int8_16x8_k1_p1_rep855_lat1575.37_hbm0.983398_tt1024; best_latency_us=1575.373891; best_token_throughput_per_s=634.7699461778119; best_energy_mj=135.75588466251537; best_die_area_mm2=800.0; best_dominant_energy_component=hbm; recommended_next_step=keep exact-FP16 V3 as the energy baseline and use mixed/int8 as the latency frontier pending real-checkpoint quality validation.
- next_action: inspect follow-on work after l2_decoder_attention_mixed_int8_energy_closure_llama7b_v1_r2
