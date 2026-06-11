## Summary
- item_id: `l2_decoder_attention_kv_dual_stream_physical_feasibility_llama7b_v1`
- run_key: `l2_decoder_attention_kv_dual_stream_physical_feasibility_llama7b_v1_run_682cb12ad6eee971`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_kv_dual_stream_physical_feasibility_llama7b_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_kv_dual_stream_physical_feasibility_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_kv_dual_stream_physical_feasibility_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_kv_dual_stream_physical_feasibility_v1`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_kv_dual_stream_physical_feasibility_v1` plus `docs/developer_agent_review.md`
- execution_source_commit: `efe7890b509de3642e1e3e364251d17f23f21056`
- review_metadata_source_commit: `efe7890b509de3642e1e3e364251d17f23f21056`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_kv_dual_stream_physical_feasibility`
- comparison_role: `frontier_closure`
- expected_direction: `iterate`
- expected_reason: `Use the budget-aware dual-stream feasibility result to choose between denser fused datapath PPA, reduced replica scheduling, or the split_mac conservative frontier.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder dual-stream physical feasibility evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_dual_stream_physical_feasibility__l2_decoder_attention_kv_dual_stream_physical_feasibility_llama7b_v1.json: decision=dual_stream_area_blocked; best_requested_mode=dual_mac; best_requested_latency_us=1575.373891; best_requested_area_fit=False; best_requested_logic_slack_um2=-398874400.4116; best_requested_compute_area_over_budget_um2=398874400.4116; best_requested_required_compute_density_gain=2.011289; best_feasible_mode=split_mac; best_feasible_latency_us=2042.378179; recommended_next_step=measure a denser dual-stream fused attention datapath or reduce compute replicas before promoting dual_mac.`

## Focused Comparison
- primary_question: `Can the dual_mac sub-tile attention schedule be promoted under the current measured logic budget, or is the area-neutral split_mac fallback the current valid frontier?`
- comparison_role: `frontier_closure`
- proposal_outcome: `dual_stream_area_blocked`
- comparison_summary: `Decoder dual-stream physical feasibility evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_dual_stream_physical_feasibility__l2_decoder_attention_kv_dual_stream_physical_feasibility_llama7b_v1.json: decision=dual_stream_area_blocked; best_requested_mode=dual_mac; best_requested_latency_us=1575.373891; best_requested_area_fit=False; best_requested_logic_slack_um2=-398874400.4116; best_requested_compute_area_over_budget_um2=398874400.4116; best_requested_required_compute_density_gain=2.011289; best_feasible_mode=split_mac; best_feasible_latency_us=2042.378179; recommended_next_step=measure a denser dual-stream fused attention datapath or reduce compute replicas before promoting dual_mac.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
