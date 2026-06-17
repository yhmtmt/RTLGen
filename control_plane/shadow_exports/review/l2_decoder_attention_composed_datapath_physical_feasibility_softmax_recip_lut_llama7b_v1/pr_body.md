## Summary
- item_id: `l2_decoder_attention_composed_datapath_physical_feasibility_softmax_recip_lut_llama7b_v1`
- run_key: `l2_decoder_attention_composed_datapath_physical_feasibility_softmax_recip_lut_llama7b_v1_run_6e84877c9451a7de`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_composed_datapath_physical_feasibility_softmax_recip_lut_llama7b_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_composed_datapath_physical_feasibility_softmax_recip_lut_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_composed_datapath_physical_feasibility_softmax_recip_lut_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_composed_datapath_physical_feasibility_softmax_recip_lut_v1`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_composed_datapath_physical_feasibility_softmax_recip_lut_v1` plus `docs/developer_agent_review.md`
- execution_source_commit: `0284e5722a44b45e8b91120fa7e9d2abacde97e5`
- review_metadata_source_commit: `0284e5722a44b45e8b91120fa7e9d2abacde97e5`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_composed_datapath_physical_feasibility`
- comparison_role: `frontier_closure`
- expected_direction: `record_softmax_recip_composed_datapath_physical_feasibility`
- expected_reason: `Quantify whether measured composed wrapper area and clock keep the softmax-recip int8 dual-MAC point ahead of the split/shared-MAC fallback.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder composed dual-stream physical feasibility evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_composed_datapath_physical_feasibility__l2_decoder_attention_composed_datapath_physical_feasibility_softmax_recip_lut_llama7b_v1.json: decision=dual_stream_feasible; precision_profile=q8_k8_v6_a24_s8_w8_recip_lut_q10_int8_compute; best_requested_mode=dual_mac; best_requested_latency_us=1575.373891; best_requested_adjusted_latency_us_if_feasible=2088.8565949348113; best_requested_adjusted_speedup_vs_hbm_closed_source=1.0239290847098579; best_requested_area_fit=True; best_requested_logic_slack_um2=168128417.0692; best_requested_compute_area_over_budget_um2=0.0; best_requested_required_compute_density_gain=0.579174; best_requested_compute_substitution_enabled=True; best_requested_substituted_compute_arch=attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q10; best_requested_substituted_compute_area_um2=231391215.0; best_requested_compute_clock_ok=False; best_feasible_mode=dual_mac; best_feasible_latency_us=2088.8565949348113; recommended_next_step=promote dual-stream schedule into a measured RTL/PPA wrapper.`

## Focused Comparison
- primary_question: `After substituting the measured q10 composed dual-stream softmax-recip wrapper, what is the physically effective dual-MAC latency and does it remain the best least-abstract frontier?`
- comparison_role: `frontier_closure`
- proposal_outcome: `dual_stream_feasible`
- comparison_summary: `Decoder composed dual-stream physical feasibility evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_composed_datapath_physical_feasibility__l2_decoder_attention_composed_datapath_physical_feasibility_softmax_recip_lut_llama7b_v1.json: decision=dual_stream_feasible; precision_profile=q8_k8_v6_a24_s8_w8_recip_lut_q10_int8_compute; best_requested_mode=dual_mac; best_requested_latency_us=1575.373891; best_requested_adjusted_latency_us_if_feasible=2088.8565949348113; best_requested_adjusted_speedup_vs_hbm_closed_source=1.0239290847098579; best_requested_area_fit=True; best_requested_logic_slack_um2=168128417.0692; best_requested_compute_area_over_budget_um2=0.0; best_requested_required_compute_density_gain=0.579174; best_requested_compute_substitution_enabled=True; best_requested_substituted_compute_arch=attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q10; best_requested_substituted_compute_area_um2=231391215.0; best_requested_compute_clock_ok=False; best_feasible_mode=dual_mac; best_feasible_latency_us=2088.8565949348113; recommended_next_step=promote dual-stream schedule into a measured RTL/PPA wrapper.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
