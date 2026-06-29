## Summary
- item_id: `l2_decoder_attention_composed_datapath_score24_w16_exact_div_reduced_replica_llama7b_v1`
- run_key: `l2_decoder_attention_composed_datapath_score24_w16_exact_div_reduced_replica_llama7b_v1_run_cc11b26ad9434207`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_composed_datapath_score24_w16_exact_div_reduced_replica_llama7b_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_composed_datapath_score24_w16_exact_div_reduced_replica_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_composed_datapath_score24_w16_exact_div_reduced_replica_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_composed_datapath_score24_w16_exact_div_reduced_replica_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_composed_datapath_score24_w16_exact_div_reduced_replica_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `af8c1790d89c94d7b7e6377e487aecacea8def42`
- review_metadata_source_commit: `af8c1790d89c94d7b7e6377e487aecacea8def42`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_composed_datapath_physical_feasibility`
- comparison_role: `score24_quality_reduced_replica_recost`
- expected_direction: `record_score24_area_fit_recost`
- expected_reason: `The mixed/int8 quality-energy frontier selected qkv8_float_exact as the only quality-backed point; this substitutes the closest measured score24/w16 q8/k8/v8 wrapper into the Llama7B schedule.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder composed dual-stream physical feasibility evidence (score24/w16 exact-div reduced-replica recost) recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_composed_datapath_physical_feasibility__l2_decoder_attention_composed_datapath_score24_w16_exact_div_reduced_replica_llama7b_v1.json: decision=dual_stream_feasible; precision_profile=q8_k8_v8_a24_s24_w16_exact_div_int8_compute; best_requested_mode=dual_mac; best_requested_latency_us=1575.373891; best_requested_adjusted_latency_us_if_feasible=7889.749325; best_requested_adjusted_speedup_vs_hbm_closed_source=0.2710911680327689; best_requested_area_fit=True; best_requested_logic_slack_um2=47478504.0692; best_requested_compute_area_over_budget_um2=0.0; best_requested_required_compute_density_gain=0.881161; best_requested_compute_substitution_enabled=True; best_requested_substituted_compute_arch=attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score24_w16_exact_div; best_requested_substituted_compute_area_um2=352041128.0; best_requested_substituted_compute_variant_label=attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score24_w16_exact_div; best_requested_compute_clock_ok=True; best_requested_replica_recost_enabled=True; best_requested_replica_recost_area_fit_replica_count=856; best_requested_replica_recost_macs_per_cycle=109568; best_requested_replica_recost_latency_us=7889.749325; best_feasible_mode=dual_mac; best_feasible_latency_us=7889.749325; recommended_next_step=promote dual-stream schedule into a measured RTL/PPA wrapper.`

## Focused Comparison
- primary_question: `What Llama7B latency/area/energy point remains when the measured score24/w16 exact-div composed datapath is constrained to the area-fit replica count?`
- comparison_role: `score24_quality_reduced_replica_recost`
- proposal_outcome: `dual_stream_feasible`
- comparison_summary: `Decoder composed dual-stream physical feasibility evidence (score24/w16 exact-div reduced-replica recost) recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_composed_datapath_physical_feasibility__l2_decoder_attention_composed_datapath_score24_w16_exact_div_reduced_replica_llama7b_v1.json: decision=dual_stream_feasible; precision_profile=q8_k8_v8_a24_s24_w16_exact_div_int8_compute; best_requested_mode=dual_mac; best_requested_latency_us=1575.373891; best_requested_adjusted_latency_us_if_feasible=7889.749325; best_requested_adjusted_speedup_vs_hbm_closed_source=0.2710911680327689; best_requested_area_fit=True; best_requested_logic_slack_um2=47478504.0692; best_requested_compute_area_over_budget_um2=0.0; best_requested_required_compute_density_gain=0.881161; best_requested_compute_substitution_enabled=True; best_requested_substituted_compute_arch=attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score24_w16_exact_div; best_requested_substituted_compute_area_um2=352041128.0; best_requested_substituted_compute_variant_label=attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score24_w16_exact_div; best_requested_compute_clock_ok=True; best_requested_replica_recost_enabled=True; best_requested_replica_recost_area_fit_replica_count=856; best_requested_replica_recost_macs_per_cycle=109568; best_requested_replica_recost_latency_us=7889.749325; best_feasible_mode=dual_mac; best_feasible_latency_us=7889.749325; recommended_next_step=promote dual-stream schedule into a measured RTL/PPA wrapper.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
