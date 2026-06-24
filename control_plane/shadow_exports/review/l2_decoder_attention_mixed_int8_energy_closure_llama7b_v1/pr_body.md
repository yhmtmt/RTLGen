## Summary
- item_id: `l2_decoder_attention_mixed_int8_energy_closure_llama7b_v1`
- run_key: `l2_decoder_attention_mixed_int8_energy_closure_llama7b_v1_run_98acd581d944774d`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_mixed_int8_energy_closure_llama7b_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_mixed_int8_energy_closure_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_mixed_int8_energy_closure_llama7b_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_mixed_int8_energy_closure_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_mixed_int8_energy_closure_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `f0cfd2e8eee0bf001c0a18d914a5ec64ff3b1ee3`
- review_metadata_source_commit: `f0cfd2e8eee0bf001c0a18d914a5ec64ff3b1ee3`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_mixed_int8_energy_closure`
- comparison_role: `frontier_closure`
- expected_direction: `compare_mixed_int8_against_fp16_v3`
- expected_reason: `Record whether mixed/int8 is the energy, latency, or precision-risk frontier under current Llama7B energy accounting.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder mixed/int8 energy closure evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_energy_closure__l2_decoder_attention_mixed_int8_energy_closure_llama7b_v1.json: decision=mixed_precision_int8_compute_improves_latency_not_energy; source_rows_used=3; physical_feasible_rows=3; best_requested_mode=dual_mac; best_requested_adjusted_latency_us_if_feasible=1575.373891; best_requested_substituted_compute_arch=dense_gemm_int8_16x8_k1_p1; best_requested_substituted_compute_area_um2=89549280.0; best_requested_substituted_compute_power_mw=974.7; best_candidate_id=die800_dense_gemm_int8_16x8_k1_p1_rep855_lat1575.37_hbm0.983398_tt1024; best_latency_us=1575.373891; best_token_throughput_per_s=634.7699461778119; best_energy_mj=135.75588466251537; best_die_area_mm2=800.0; best_dominant_energy_component=hbm; recommended_next_step=keep exact-FP16 V3 as the energy baseline and use mixed/int8 as the latency frontier pending real-checkpoint quality validation.`

## Focused Comparison
- primary_question: `Does the mixed/int8 softmax-recip point replace the exact-FP16 dense-GEMM V3 Llama7B frontier when token throughput, energy, area, and precision are considered together?`
- comparison_role: `frontier_closure`
- proposal_outcome: `mixed_precision_int8_compute_improves_latency_not_energy`
- comparison_summary: `Decoder mixed/int8 energy closure evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_energy_closure__l2_decoder_attention_mixed_int8_energy_closure_llama7b_v1.json: decision=mixed_precision_int8_compute_improves_latency_not_energy; source_rows_used=3; physical_feasible_rows=3; best_requested_mode=dual_mac; best_requested_adjusted_latency_us_if_feasible=1575.373891; best_requested_substituted_compute_arch=dense_gemm_int8_16x8_k1_p1; best_requested_substituted_compute_area_um2=89549280.0; best_requested_substituted_compute_power_mw=974.7; best_candidate_id=die800_dense_gemm_int8_16x8_k1_p1_rep855_lat1575.37_hbm0.983398_tt1024; best_latency_us=1575.373891; best_token_throughput_per_s=634.7699461778119; best_energy_mj=135.75588466251537; best_die_area_mm2=800.0; best_dominant_energy_component=hbm; recommended_next_step=keep exact-FP16 V3 as the energy baseline and use mixed/int8 as the latency frontier pending real-checkpoint quality validation.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
