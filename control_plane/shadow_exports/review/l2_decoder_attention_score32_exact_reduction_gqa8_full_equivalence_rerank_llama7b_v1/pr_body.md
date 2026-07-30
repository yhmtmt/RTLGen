## Summary
- item_id: `l2_decoder_attention_score32_exact_reduction_gqa8_full_equivalence_rerank_llama7b_v1`
- run_key: `l2_decoder_attention_score32_exact_reduction_gqa8_full_equivalence_rerank_llama7b_v1_run_b4857cccb14e6108`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `2/2 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_score32_exact_reduction_gqa8_full_equivalence_rerank_llama7b_v1/evaluated.json`
- metrics_rows_count: `0`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_score32_exact_reduction_gqa8_full_equivalence_rerank_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_score32_exact_reduction_gqa8_full_equivalence_rerank_llama7b_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_score32_exact_reduction_gqa8_full_equivalence_rerank_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_score32_exact_reduction_gqa8_full_equivalence_rerank_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `8cc94346b4b3f0bf6d7a9b52df47cb8f3329d64e`
- review_metadata_source_commit: `8cc94346b4b3f0bf6d7a9b52df47cb8f3329d64e`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_score32_exact_reduction_gqa8_full_equivalence_rerank`
- comparison_role: `score32_exact_reduction_gqa8_full_equivalence_rerank`
- expected_direction: `rerank_quality_aware_score32_frontier_after_exact_reduction_and_full_gqa8_equivalence`
- expected_reason: `Apply exact reduction latency only after one-group and four-group full GQA8 equivalence; preserve throughput, bounded energy, area, and precision dimensions.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder score32 exact-reduction full-GQA8 rerank recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_score32_exact_reduction_gqa8_full_equivalence_rerank__l2_decoder_attention_score32_exact_reduction_gqa8_full_equivalence_rerank_llama7b_v1.json: decision=score32_exact_reduction_gqa8_full_equivalence_frontier_recorded; best_latency_candidate=physical_hbm_gqa8_kv8_service_frontier; best_energy_candidate=physical_hbm_gqa8_kv8_service_frontier; best_precision_safe_candidate=score32_exp_lut_schedule_wrapper_hbm_controller_replay_best; best_precision_safe_energy_candidate=die1200_dense_gemm_16x8_k1_p1_mac132736_lat1872.29_hbm0.465654_tt512; score32_latency_us=13488.364723; score32_token_throughput_per_s=74.137971543343; score32_total_energy_mj_per_token=484.704405630618; score32_total_energy_mj_per_token_lower_bound=467.191305313106; score32_energy_estimate_status=conservative_upper_bound_latency_scaled_non_hbm_energy; exact_energy_ranking_status=provisional_pending_reducer_and_global_tree_activity_power_measurement; score32_die_area_mm2=800.0; score32_quality_status=mixed_int8_generation_quality_pass; score32_vs_measured_fp16_throughput_ratio=5.378269614; score32_vs_measured_fp16_energy_ratio=5.935340342; exact_reduction_source_latency_us=12814.257853; exact_reduction_corrected_latency_us=13488.364723; exact_reduction_delta_latency_us=674.10687; one_group_equivalence_item_id=l2_decoder_attention_score32_exact_local16_global_tree_cluster_sram_gqa8_equivalence_llama7b_v1_r7; four_group_equivalence_item_id=l2_decoder_attention_score32_exact_local16_global_tree_cluster_sram_gqa8_rotation_equivalence_llama7b_v1; remaining_abstractions=['Exact reduction latency is now backed by the banked finalized-tree service contract plus one-/four-group RTL equivalence, but dedicated reducer/global-tree activity energy remains unclosed.', 'Full one- and four-group GQA8 equivalence closes functional composition only; full-array postroute PPA and toggle power remain unmeasured.', 'HBM replay controller area, active energy, and control timing are backed by measured Nangate45 RTL PPA.', 'Score32 exact-energy ranking remains provisional until reducer/global-tree activity power is measured.', 'does not include vendor HBM current signoff'].`

## Focused Comparison
- primary_question: `Does the quality-aware score32 frontier remain the best precision-safe throughput point after exact reduction recost and full GQA8 functional closure?`
- comparison_role: `score32_exact_reduction_gqa8_full_equivalence_rerank`
- proposal_outcome: `score32_exact_reduction_gqa8_full_equivalence_frontier_recorded`
- comparison_summary: `Decoder score32 exact-reduction full-GQA8 rerank recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_score32_exact_reduction_gqa8_full_equivalence_rerank__l2_decoder_attention_score32_exact_reduction_gqa8_full_equivalence_rerank_llama7b_v1.json: decision=score32_exact_reduction_gqa8_full_equivalence_frontier_recorded; best_latency_candidate=physical_hbm_gqa8_kv8_service_frontier; best_energy_candidate=physical_hbm_gqa8_kv8_service_frontier; best_precision_safe_candidate=score32_exp_lut_schedule_wrapper_hbm_controller_replay_best; best_precision_safe_energy_candidate=die1200_dense_gemm_16x8_k1_p1_mac132736_lat1872.29_hbm0.465654_tt512; score32_latency_us=13488.364723; score32_token_throughput_per_s=74.137971543343; score32_total_energy_mj_per_token=484.704405630618; score32_total_energy_mj_per_token_lower_bound=467.191305313106; score32_energy_estimate_status=conservative_upper_bound_latency_scaled_non_hbm_energy; exact_energy_ranking_status=provisional_pending_reducer_and_global_tree_activity_power_measurement; score32_die_area_mm2=800.0; score32_quality_status=mixed_int8_generation_quality_pass; score32_vs_measured_fp16_throughput_ratio=5.378269614; score32_vs_measured_fp16_energy_ratio=5.935340342; exact_reduction_source_latency_us=12814.257853; exact_reduction_corrected_latency_us=13488.364723; exact_reduction_delta_latency_us=674.10687; one_group_equivalence_item_id=l2_decoder_attention_score32_exact_local16_global_tree_cluster_sram_gqa8_equivalence_llama7b_v1_r7; four_group_equivalence_item_id=l2_decoder_attention_score32_exact_local16_global_tree_cluster_sram_gqa8_rotation_equivalence_llama7b_v1; remaining_abstractions=['Exact reduction latency is now backed by the banked finalized-tree service contract plus one-/four-group RTL equivalence, but dedicated reducer/global-tree activity energy remains unclosed.', 'Full one- and four-group GQA8 equivalence closes functional composition only; full-array postroute PPA and toggle power remain unmeasured.', 'HBM replay controller area, active energy, and control timing are backed by measured Nangate45 RTL PPA.', 'Score32 exact-energy ranking remains provisional until reducer/global-tree activity power is measured.', 'does not include vendor HBM current signoff'].`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
