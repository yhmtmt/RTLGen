## Summary
- item_id: `l2_decoder_attention_mixed_precision_int8_compute_physical_feasibility_softmax_recip_lut_llama7b_v1`
- run_key: `l2_decoder_attention_mixed_precision_int8_compute_physical_feasibility_softmax_recip_lut_llama7b_v1_run_796905f7e2a4d756`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_mixed_precision_int8_compute_physical_feasibility_softmax_recip_lut_llama7b_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_mixed_precision_int8_compute_physical_feasibility_softmax_recip_lut_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_mixed_precision_int8_compute_physical_feasibility_softmax_recip_lut_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_mixed_precision_int8_compute_physical_feasibility_softmax_recip_lut_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_mixed_precision_int8_compute_physical_feasibility_softmax_recip_lut_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `1f7289b71ec4d64e0c8b84651091fb6e29f48b8d`
- review_metadata_source_commit: `1f7289b71ec4d64e0c8b84651091fb6e29f48b8d`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_mixed_precision_int8_compute_physical_feasibility`
- comparison_role: `frontier_recovery`
- expected_direction: `recover_dual_mac_with_int8_compute`
- expected_reason: `Record whether measured int8 dense compute recovers the softmax-recip dual_mac schedule from the current split_mac physical frontier.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder mixed-precision int8-compute physical feasibility evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_precision_int8_compute_physical_feasibility__l2_decoder_attention_mixed_precision_int8_compute_physical_feasibility_softmax_recip_lut_llama7b_v1.json: decision=dual_stream_feasible; precision_profile=q8_k8_v6_a24_s8_w8_recip_lut_q10_int8_compute; best_requested_mode=dual_mac; best_requested_latency_us=1575.373891; best_requested_area_fit=True; best_requested_logic_slack_um2=216801992.1716; best_requested_compute_area_over_budget_um2=0.0; best_requested_required_compute_density_gain=0.452383; best_requested_compute_substitution_enabled=True; best_requested_substituted_compute_arch=dense_gemm_int8_16x8_k1_p1; best_requested_substituted_compute_area_um2=89549280.0; best_requested_compute_clock_ok=True; best_feasible_mode=dual_mac; best_feasible_latency_us=1575.373891; recommended_next_step=promote dual-stream schedule into a measured RTL/PPA wrapper.`

## Focused Comparison
- primary_question: `Does measured int8 dense compute make the softmax reciprocal-LUT dual_mac Llama7B schedule physically feasible under the current area budget?`
- comparison_role: `frontier_recovery`
- proposal_outcome: `dual_stream_feasible`
- comparison_summary: `Decoder mixed-precision int8-compute physical feasibility evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_precision_int8_compute_physical_feasibility__l2_decoder_attention_mixed_precision_int8_compute_physical_feasibility_softmax_recip_lut_llama7b_v1.json: decision=dual_stream_feasible; precision_profile=q8_k8_v6_a24_s8_w8_recip_lut_q10_int8_compute; best_requested_mode=dual_mac; best_requested_latency_us=1575.373891; best_requested_area_fit=True; best_requested_logic_slack_um2=216801992.1716; best_requested_compute_area_over_budget_um2=0.0; best_requested_required_compute_density_gain=0.452383; best_requested_compute_substitution_enabled=True; best_requested_substituted_compute_arch=dense_gemm_int8_16x8_k1_p1; best_requested_substituted_compute_area_um2=89549280.0; best_requested_compute_clock_ok=True; best_feasible_mode=dual_mac; best_feasible_latency_us=1575.373891; recommended_next_step=promote dual-stream schedule into a measured RTL/PPA wrapper.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
