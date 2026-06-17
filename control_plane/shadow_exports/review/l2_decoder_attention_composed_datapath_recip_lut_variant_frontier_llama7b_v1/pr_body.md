## Summary
- item_id: `l2_decoder_attention_composed_datapath_recip_lut_variant_frontier_llama7b_v1`
- run_key: `l2_decoder_attention_composed_datapath_recip_lut_variant_frontier_llama7b_v1_run_782f0283b9d50921`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_composed_datapath_recip_lut_variant_frontier_llama7b_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_composed_datapath_recip_lut_variant_frontier_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_composed_datapath_recip_lut_variant_frontier_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_composed_datapath_recip_lut_variant_frontier_v1`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_composed_datapath_recip_lut_variant_frontier_v1` plus `docs/developer_agent_review.md`
- execution_source_commit: `45392fae420e5fe965c0841a44bfbe3eb134082c`
- review_metadata_source_commit: `45392fae420e5fe965c0841a44bfbe3eb134082c`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_composed_datapath_physical_feasibility`
- comparison_role: `frontier_closure`
- expected_direction: `record_composed_recip_lut_variant_frontier`
- expected_reason: `Identify whether q8, q10, or q12 reciprocal-LUT composed wrapper is the best measured datapath point.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder composed dual-stream physical feasibility evidence (softmax-recip LUT variant frontier) recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_composed_datapath_physical_feasibility__l2_decoder_attention_composed_datapath_recip_lut_variant_frontier_llama7b_v1.json: decision=dual_stream_feasible; precision_profile=q8_k8_v6_a24_s8_w8_recip_lut_variant_int8_compute; best_requested_mode=dual_mac; best_requested_latency_us=1575.373891; best_requested_adjusted_latency_us_if_feasible=2045.3705757403322; best_requested_adjusted_speedup_vs_hbm_closed_source=1.045698538304037; best_requested_area_fit=True; best_requested_logic_slack_um2=177272072.0692; best_requested_compute_area_over_budget_um2=0.0; best_requested_required_compute_density_gain=0.556287; best_requested_compute_substitution_enabled=True; best_requested_substituted_compute_arch=attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q8; best_requested_substituted_compute_area_um2=222247560.0; best_requested_substituted_compute_variant_label=q8; best_requested_compute_clock_ok=False; best_feasible_mode=dual_mac; best_feasible_latency_us=2045.3705757403322; recommended_next_step=promote dual-stream schedule into a measured RTL/PPA wrapper.`

## Focused Comparison
- primary_question: `Among measured q8/q10/q12 reciprocal-LUT composed dual-stream wrappers, which gives the best effective Llama7B attention latency under the same subtile schedule and quality evidence?`
- comparison_role: `frontier_closure`
- proposal_outcome: `dual_stream_feasible`
- comparison_summary: `Decoder composed dual-stream physical feasibility evidence (softmax-recip LUT variant frontier) recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_composed_datapath_physical_feasibility__l2_decoder_attention_composed_datapath_recip_lut_variant_frontier_llama7b_v1.json: decision=dual_stream_feasible; precision_profile=q8_k8_v6_a24_s8_w8_recip_lut_variant_int8_compute; best_requested_mode=dual_mac; best_requested_latency_us=1575.373891; best_requested_adjusted_latency_us_if_feasible=2045.3705757403322; best_requested_adjusted_speedup_vs_hbm_closed_source=1.045698538304037; best_requested_area_fit=True; best_requested_logic_slack_um2=177272072.0692; best_requested_compute_area_over_budget_um2=0.0; best_requested_required_compute_density_gain=0.556287; best_requested_compute_substitution_enabled=True; best_requested_substituted_compute_arch=attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q8; best_requested_substituted_compute_area_um2=222247560.0; best_requested_substituted_compute_variant_label=q8; best_requested_compute_clock_ok=False; best_feasible_mode=dual_mac; best_feasible_latency_us=2045.3705757403322; recommended_next_step=promote dual-stream schedule into a measured RTL/PPA wrapper.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
