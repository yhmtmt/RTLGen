## Summary
- item_id: `l2_decoder_attention_score32_hbm_controller_replay_rtl_ppa_recost_integrated_frontier_ranking_llama7b_v1`
- run_key: `l2_decoder_attention_score32_hbm_controller_replay_rtl_ppa_recost_integrated_frontier_ranking_llama7b_v1_run_b170d126a0ce27b5`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `2/2 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_score32_hbm_controller_replay_rtl_ppa_recost_integrated_frontier_ranking_llama7b_v1/evaluated.json`
- metrics_rows_count: `0`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_score32_hbm_controller_replay_rtl_ppa_recost_integrated_frontier_ranking_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_score32_hbm_controller_replay_rtl_ppa_recost_integrated_frontier_ranking_llama7b_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_score32_hbm_controller_replay_rtl_ppa_recost_integrated_frontier_ranking_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_score32_hbm_controller_replay_rtl_ppa_recost_integrated_frontier_ranking_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `157ba5f01d2e1ee0d47a86d1eb71a630b23492ed`
- review_metadata_source_commit: `157ba5f01d2e1ee0d47a86d1eb71a630b23492ed`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_score32_integrated_frontier_ranking`
- comparison_role: `score32_hbm_controller_replay_rtl_ppa_recost_integrated_frontier_ranking`
- expected_direction: `record_score32_integrated_frontier_ranking_with_replay_controller_ppa_recost`
- expected_reason: `Fold the measured controller cost into score32 totals and preserve the ranking only if recosted evidence supports it.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder score32 integrated frontier ranking recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_score32_integrated_frontier_ranking__l2_decoder_attention_score32_hbm_controller_replay_rtl_ppa_recost_integrated_frontier_ranking_llama7b_v1.json: decision=score32_integrated_frontier_best_precision_safe_throughput; best_latency_candidate=physical_hbm_gqa8_kv8_service_frontier; best_energy_candidate=physical_hbm_gqa8_kv8_service_frontier; best_precision_safe_candidate=score32_exp_lut_schedule_wrapper_hbm_controller_replay_best; score32_latency_us=12814.257853; score32_total_energy_mj_per_token=467.191305313106; score32_die_area_mm2=800.0; score32_quality_status=mixed_int8_generation_quality_pass; current_recommended_candidate=score32_exp_lut_schedule_wrapper_hbm_controller_replay_best; remaining_abstractions=['HBM replay controller area, active energy, and control timing are backed by measured Nangate45 RTL PPA.', 'does not include vendor HBM current signoff', 'profile_scaled_noc_sram_energy', 'source_backed_aggregate_hbm_energy_not_vendor_current_signoff'].`

## Focused Comparison
- primary_question: `Does exact replay-controller PPA recost change the score32 Llama7B throughput, energy, area, precision, or promotability ranking?`
- comparison_role: `score32_hbm_controller_replay_rtl_ppa_recost_integrated_frontier_ranking`
- proposal_outcome: `score32_integrated_frontier_best_precision_safe_throughput`
- comparison_summary: `Decoder score32 integrated frontier ranking recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_score32_integrated_frontier_ranking__l2_decoder_attention_score32_hbm_controller_replay_rtl_ppa_recost_integrated_frontier_ranking_llama7b_v1.json: decision=score32_integrated_frontier_best_precision_safe_throughput; best_latency_candidate=physical_hbm_gqa8_kv8_service_frontier; best_energy_candidate=physical_hbm_gqa8_kv8_service_frontier; best_precision_safe_candidate=score32_exp_lut_schedule_wrapper_hbm_controller_replay_best; score32_latency_us=12814.257853; score32_total_energy_mj_per_token=467.191305313106; score32_die_area_mm2=800.0; score32_quality_status=mixed_int8_generation_quality_pass; current_recommended_candidate=score32_exp_lut_schedule_wrapper_hbm_controller_replay_best; remaining_abstractions=['HBM replay controller area, active energy, and control timing are backed by measured Nangate45 RTL PPA.', 'does not include vendor HBM current signoff', 'profile_scaled_noc_sram_energy', 'source_backed_aggregate_hbm_energy_not_vendor_current_signoff'].`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
