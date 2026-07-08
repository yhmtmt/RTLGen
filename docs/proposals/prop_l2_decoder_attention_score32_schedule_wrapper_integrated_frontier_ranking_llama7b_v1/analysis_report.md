# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_decoder_attention_score32_schedule_wrapper_integrated_frontier_ranking_llama7b_v1`
- `candidate_id`: `l2_decoder_attention_score32_schedule_wrapper_integrated_frontier_ranking_llama7b_v1`

## Evaluations Consumed
- `l2_decoder_attention_score32_schedule_wrapper_integrated_frontier_ranking_llama7b_v1`
- `l2_decoder_attention_score32_schedule_wrapper_integrated_frontier_ranking_llama7b_v1_run_bba2bd89e20c5cba`
- source commit: `6143775a9fe6c30a6b48e5fcc08df02be11e5632`
- review: PR #1221

## Baseline Comparison
- baseline_ref: `None`
- baseline_item_id: `None`
- outcome: `score32_integrated_frontier_best_precision_safe_throughput`
- summary: Decoder score32 integrated frontier ranking recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_score32_integrated_frontier_ranking__l2_decoder_attention_score32_schedule_wrapper_integrated_frontier_ranking_llama7b_v1.json: decision=score32_integrated_frontier_best_precision_safe_throughput; best_latency_candidate=physical_hbm_gqa8_kv8_service_frontier; best_energy_candidate=physical_hbm_gqa8_kv8_service_frontier; best_precision_safe_candidate=score32_exp_lut_schedule_wrapper_hbm_service_best; score32_latency_us=12814.257853; score32_total_energy_mj_per_token=467.1899085587987; score32_die_area_mm2=800.0; score32_quality_status=mixed_int8_generation_quality_pass; current_recommended_candidate=score32_exp_lut_schedule_wrapper_hbm_service_best; remaining_abstractions=['HBM energy uses calibrated command-class pJ values, not vendor signoff current traces.', 'HBM/DRAM service and energy are reused from the score32 HBM closure because the wrapper recost does not change token memory traffic.', 'HBM/DRAM service is command/burst/row-hit accounting, not cycle-accurate controller RTL.', 'profile_scaled_noc_sram_energy', 'source_backed_aggregate_hbm_energy_not_vendor_current_signoff'].

## Result
- result: `iterate`
- confidence level: merged accepted evidence
- estimated optimization room: pending follow-on comparison
- architecture conclusion robustness: staged evidence
- summary: Decoder score32 integrated frontier ranking recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_score32_integrated_frontier_ranking__l2_decoder_attention_score32_schedule_wrapper_integrated_frontier_ranking_llama7b_v1.json: decision=score32_integrated_frontier_best_precision_safe_throughput; best_latency_candidate=physical_hbm_gqa8_kv8_service_frontier; best_energy_candidate=physical_hbm_gqa8_kv8_service_frontier; best_precision_safe_candidate=score32_exp_lut_schedule_wrapper_hbm_service_best; score32_latency_us=12814.257853; score32_total_energy_mj_per_token=467.1899085587987; score32_die_area_mm2=800.0; score32_quality_status=mixed_int8_generation_quality_pass; current_recommended_candidate=score32_exp_lut_schedule_wrapper_hbm_service_best; remaining_abstractions=['HBM energy uses calibrated command-class pJ values, not vendor signoff current traces.', 'HBM/DRAM service and energy are reused from the score32 HBM closure because the wrapper recost does not change token memory traffic.', 'HBM/DRAM service is command/burst/row-hit accounting, not cycle-accurate controller RTL.', 'profile_scaled_noc_sram_energy', 'source_backed_aggregate_hbm_energy_not_vendor_current_signoff'].

## Failures and Caveats
- no additional caveats recorded during automatic finalization

## Recommendation
- `iterate`
- reason: Decoder score32 integrated frontier ranking recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_score32_integrated_frontier_ranking__l2_decoder_attention_score32_schedule_wrapper_integrated_frontier_ranking_llama7b_v1.json: decision=score32_integrated_frontier_best_precision_safe_throughput; best_latency_candidate=physical_hbm_gqa8_kv8_service_frontier; best_energy_candidate=physical_hbm_gqa8_kv8_service_frontier; best_precision_safe_candidate=score32_exp_lut_schedule_wrapper_hbm_service_best; score32_latency_us=12814.257853; score32_total_energy_mj_per_token=467.1899085587987; score32_die_area_mm2=800.0; score32_quality_status=mixed_int8_generation_quality_pass; current_recommended_candidate=score32_exp_lut_schedule_wrapper_hbm_service_best; remaining_abstractions=['HBM energy uses calibrated command-class pJ values, not vendor signoff current traces.', 'HBM/DRAM service and energy are reused from the score32 HBM closure because the wrapper recost does not change token memory traffic.', 'HBM/DRAM service is command/burst/row-hit accounting, not cycle-accurate controller RTL.', 'profile_scaled_noc_sram_energy', 'source_backed_aggregate_hbm_energy_not_vendor_current_signoff'].
- next_action: inspect follow-on work after l2_decoder_attention_score32_schedule_wrapper_integrated_frontier_ranking_llama7b_v1
