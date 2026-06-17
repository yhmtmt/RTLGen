## Summary
- item_id: `l2_decoder_attention_kv_dual_stream_physical_feasibility_softmax_recip_lut_llama7b_v1`
- run_key: `l2_decoder_attention_kv_dual_stream_physical_feasibility_softmax_recip_lut_llama7b_v1_run_c8741aed35a796c1`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_kv_dual_stream_physical_feasibility_softmax_recip_lut_llama7b_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_kv_dual_stream_physical_feasibility_softmax_recip_lut_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_kv_dual_stream_physical_feasibility_softmax_recip_lut_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_kv_dual_stream_physical_feasibility_softmax_recip_lut_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_kv_dual_stream_physical_feasibility_softmax_recip_lut_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `a4846f80f6d8eeb052c209d3de8ea3ae0d78ef97`
- review_metadata_source_commit: `a4846f80f6d8eeb052c209d3de8ea3ae0d78ef97`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_kv_dual_stream_physical_feasibility`
- comparison_role: `frontier_closure`
- expected_direction: `record_softmax_recip_dual_stream_physical_feasibility`
- expected_reason: `Quantify whether the softmax-recip subtile pipeline selected dual_mac schedule fits the measured logic budget, or whether the current physically valid frontier must use split/shared MAC.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder dual-stream physical feasibility evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_dual_stream_physical_feasibility__l2_decoder_attention_kv_dual_stream_physical_feasibility_softmax_recip_lut_llama7b_v1.json: decision=dual_stream_area_blocked; precision_profile=exact_q8_kv8_v16_s24_w16; best_requested_mode=dual_mac; best_requested_latency_us=1575.373891; best_requested_area_fit=False; best_requested_logic_slack_um2=-397947652.4116; best_requested_compute_area_over_budget_um2=397947652.4116; best_requested_required_compute_density_gain=2.008939; best_requested_compute_substitution_enabled=False; best_requested_substituted_compute_arch=None; best_requested_substituted_compute_area_um2=None; best_requested_compute_clock_ok=True; best_feasible_mode=split_mac; best_feasible_latency_us=2042.378179; recommended_next_step=measure a denser dual-stream fused attention datapath or reduce compute replicas before promoting dual_mac.`

## Focused Comparison
- primary_question: `Does the softmax-recip dual_mac subtile pipeline fit the measured logic budget, or must the current frontier fall back to split/shared MAC?`
- comparison_role: `frontier_closure`
- proposal_outcome: `dual_stream_area_blocked`
- comparison_summary: `Decoder dual-stream physical feasibility evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_dual_stream_physical_feasibility__l2_decoder_attention_kv_dual_stream_physical_feasibility_softmax_recip_lut_llama7b_v1.json: decision=dual_stream_area_blocked; precision_profile=exact_q8_kv8_v16_s24_w16; best_requested_mode=dual_mac; best_requested_latency_us=1575.373891; best_requested_area_fit=False; best_requested_logic_slack_um2=-397947652.4116; best_requested_compute_area_over_budget_um2=397947652.4116; best_requested_required_compute_density_gain=2.008939; best_requested_compute_substitution_enabled=False; best_requested_substituted_compute_arch=None; best_requested_substituted_compute_area_um2=None; best_requested_compute_clock_ok=True; best_feasible_mode=split_mac; best_feasible_latency_us=2042.378179; recommended_next_step=measure a denser dual-stream fused attention datapath or reduce compute replicas before promoting dual_mac.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Submission Recovery
- submission_failure_count: `1`
- retry_request_count: `0`
- last_submission_failure: `work item l2_decoder_attention_kv_dual_stream_physical_feasibility_softmax_recip_lut_llama7b_v1 is not eligible for submission: developer_loop proposal linkage does not resolve to a proposal`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
