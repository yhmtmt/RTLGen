## Summary
- item_id: `l2_decoder_attention_mixed_int8_quality_backed_frontier_llama7b_v1_r2`
- run_key: `l2_decoder_attention_mixed_int8_quality_backed_frontier_llama7b_v1_r2_run_74c86725291693a3`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `2/2 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_mixed_int8_quality_backed_frontier_llama7b_v1_r2/evaluated.json`
- metrics_rows_count: `0`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_mixed_int8_quality_backed_frontier_llama7b_v1_r2.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_mixed_int8_quality_backed_frontier_llama7b_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_mixed_int8_quality_backed_frontier_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_mixed_int8_quality_backed_frontier_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `6fb163777d6bab1aba60e12381ea9315599fc794`
- review_metadata_source_commit: `6fb163777d6bab1aba60e12381ea9315599fc794`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_mixed_int8_quality_backed_frontier`
- comparison_role: `quality_backed_frontier`
- expected_direction: `unknown`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder mixed/int8 quality-backed frontier evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_quality_backed_frontier__l2_decoder_attention_mixed_int8_quality_backed_frontier_llama7b_v1_r2.json: decision=mixed_int8_quality_backed_frontier_recost_required; quality_passing_candidate_count=1; quality_passing_candidate_ids=['qkv8_float_exact']; quality_best_candidate_id=qkv8_float_exact; quality_best_top1_match_rate=1.0; quality_best_mean_probability_kl=0.0012425925766148221; score32_generation_quality_pass=True; score32_generation_quality_summary={'candidate_id': 'score32_float', 'decision_status': 'mixed_int8_generation_quality_pass', 'free_run_exact_match_rate': 0.75, 'free_run_token_match_rate': 0.84375, 'teacher_forced_candidate_reference_token_prob_mean': 0.44887183254036667, 'teacher_forced_mean_nll_delta': 0.0023279039990386913}; invalidated_energy_candidate_count=1; old_energy_best_candidate_id=die800_dense_gemm_int8_16x8_k1_p1_rep855_lat1575.37_hbm0.983398_tt1024; old_energy_best_latency_us=1575.373891; old_energy_best_token_throughput_per_s=634.7699461778119; old_energy_best_energy_mj=135.75588466251537; old_energy_best_precision_profile=q8_k8_v6_a24_s8_w8_recip_lut_q10_int8_compute; recommended_next_step=Score32 mixed-int8 generation/NLL evidence is passing for candidate score32_float; recost this score/softmax path with exact score/softmax PPA and update frontier ranking against energy/latency/area once rerun.`

## Focused Comparison
- primary_question: `Which mixed/int8 energy rows remain rankable after the broad native and bounded generation/NLL quality gates?`
- comparison_role: `quality_backed_frontier`
- proposal_outcome: `mixed_int8_quality_backed_frontier_recost_required`
- comparison_summary: `Decoder mixed/int8 quality-backed frontier evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_quality_backed_frontier__l2_decoder_attention_mixed_int8_quality_backed_frontier_llama7b_v1_r2.json: decision=mixed_int8_quality_backed_frontier_recost_required; quality_passing_candidate_count=1; quality_passing_candidate_ids=['qkv8_float_exact']; quality_best_candidate_id=qkv8_float_exact; quality_best_top1_match_rate=1.0; quality_best_mean_probability_kl=0.0012425925766148221; score32_generation_quality_pass=True; score32_generation_quality_summary={'candidate_id': 'score32_float', 'decision_status': 'mixed_int8_generation_quality_pass', 'free_run_exact_match_rate': 0.75, 'free_run_token_match_rate': 0.84375, 'teacher_forced_candidate_reference_token_prob_mean': 0.44887183254036667, 'teacher_forced_mean_nll_delta': 0.0023279039990386913}; invalidated_energy_candidate_count=1; old_energy_best_candidate_id=die800_dense_gemm_int8_16x8_k1_p1_rep855_lat1575.37_hbm0.983398_tt1024; old_energy_best_latency_us=1575.373891; old_energy_best_token_throughput_per_s=634.7699461778119; old_energy_best_energy_mj=135.75588466251537; old_energy_best_precision_profile=q8_k8_v6_a24_s8_w8_recip_lut_q10_int8_compute; recommended_next_step=Score32 mixed-int8 generation/NLL evidence is passing for candidate score32_float; recost this score/softmax path with exact score/softmax PPA and update frontier ranking against energy/latency/area once rerun.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
