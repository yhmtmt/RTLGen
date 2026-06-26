## Summary
- item_id: `l2_decoder_attention_composed_datapath_score32_w16_exact_div_frontier_llama7b_v1`
- run_key: `l2_decoder_attention_composed_datapath_score32_w16_exact_div_frontier_llama7b_v1_run_6da5367766bf7d91`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_composed_datapath_score32_w16_exact_div_frontier_llama7b_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_composed_datapath_score32_w16_exact_div_frontier_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_composed_datapath_score32_w16_exact_div_frontier_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_composed_datapath_score32_w16_exact_div_frontier_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_composed_datapath_score32_w16_exact_div_frontier_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `db2fd8747d03b95ec479c1ac0a489b03745818ab`
- review_metadata_source_commit: `db2fd8747d03b95ec479c1ac0a489b03745818ab`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_composed_datapath_physical_feasibility`
- comparison_role: `score32_quality_recost_frontier`
- expected_direction: `unknown`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder composed dual-stream physical feasibility evidence (score32/w16 exact-div frontier) recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_composed_datapath_physical_feasibility__l2_decoder_attention_composed_datapath_score32_w16_exact_div_frontier_llama7b_v1.json: decision=dual_stream_area_blocked; precision_profile=q8_k8_v8_a32_s32_w16_exact_div_int8_compute; best_requested_mode=dual_mac; best_requested_latency_us=1575.373891; best_requested_adjusted_latency_us_if_feasible=None; best_requested_adjusted_speedup_vs_hbm_closed_source=None; best_requested_area_fit=False; best_requested_logic_slack_um2=-26975519.9308; best_requested_compute_area_over_budget_um2=26975519.9308; best_requested_required_compute_density_gain=1.06752; best_requested_compute_substitution_enabled=True; best_requested_substituted_compute_arch=attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exact_div; best_requested_substituted_compute_area_um2=426495152.0; best_requested_substituted_compute_variant_label=attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exact_div; best_requested_compute_clock_ok=False; best_feasible_mode=None; best_feasible_latency_us=None; recommended_next_step=measure a denser dual-stream fused attention datapath or reduce compute replicas before promoting dual_mac.`

## Focused Comparison
- primary_question: `After measuring the score32/v8/w16 composed wrapper, what latency/area/precision point does it imply when substituted into the Llama7B dual-stream schedule?`
- comparison_role: `score32_quality_recost_frontier`
- proposal_outcome: `dual_stream_area_blocked`
- comparison_summary: `Decoder composed dual-stream physical feasibility evidence (score32/w16 exact-div frontier) recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_composed_datapath_physical_feasibility__l2_decoder_attention_composed_datapath_score32_w16_exact_div_frontier_llama7b_v1.json: decision=dual_stream_area_blocked; precision_profile=q8_k8_v8_a32_s32_w16_exact_div_int8_compute; best_requested_mode=dual_mac; best_requested_latency_us=1575.373891; best_requested_adjusted_latency_us_if_feasible=None; best_requested_adjusted_speedup_vs_hbm_closed_source=None; best_requested_area_fit=False; best_requested_logic_slack_um2=-26975519.9308; best_requested_compute_area_over_budget_um2=26975519.9308; best_requested_required_compute_density_gain=1.06752; best_requested_compute_substitution_enabled=True; best_requested_substituted_compute_arch=attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exact_div; best_requested_substituted_compute_area_um2=426495152.0; best_requested_substituted_compute_variant_label=attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exact_div; best_requested_compute_clock_ok=False; best_feasible_mode=None; best_feasible_latency_us=None; recommended_next_step=measure a denser dual-stream fused attention datapath or reduce compute replicas before promoting dual_mac.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
