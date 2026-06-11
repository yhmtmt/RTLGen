## Summary
- item_id: `l2_decoder_attention_mixed_precision_physical_feasibility_llama7b_v1`
- run_key: `l2_decoder_attention_mixed_precision_physical_feasibility_llama7b_v1_run_95ef73a3ce675708`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_mixed_precision_physical_feasibility_llama7b_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_mixed_precision_physical_feasibility_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_mixed_precision_physical_feasibility_llama7b_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_mixed_precision_physical_feasibility_llama7b_v1`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_mixed_precision_physical_feasibility_llama7b_v1` plus `docs/developer_agent_review.md`
- execution_source_commit: `df7db11ce15eabd09ff96192c58f49592473a8a3`
- review_metadata_source_commit: `df7db11ce15eabd09ff96192c58f49592473a8a3`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_mixed_precision_physical_feasibility`
- comparison_role: `frontier_closure`
- expected_direction: `iterate`
- expected_reason: `Use measured mixed-precision physical feasibility to decide whether the remaining frontier work is local datapath precision or compute-array density/fusion.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder mixed-precision physical feasibility evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_precision_physical_feasibility__l2_decoder_attention_mixed_precision_physical_feasibility_llama7b_v1.json: decision=dual_stream_area_blocked; precision_profile=q8_k8_v6_a24_s24_w16; best_requested_mode=dual_mac; best_requested_latency_us=1575.373891; best_requested_area_fit=False; best_requested_logic_slack_um2=-397395735.8284; best_requested_compute_area_over_budget_um2=397395735.8284; best_requested_required_compute_density_gain=2.003777; best_feasible_mode=split_mac; best_feasible_latency_us=2042.378179; recommended_next_step=measure a denser dual-stream fused attention datapath or reduce compute replicas before promoting dual_mac.`

## Focused Comparison
- primary_question: `Does quality-approved q8/k8/v6 local datapath PPA make the dual_mac Llama7B schedule physically feasible?`
- comparison_role: `frontier_closure`
- proposal_outcome: `dual_stream_area_blocked`
- comparison_summary: `Decoder mixed-precision physical feasibility evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_precision_physical_feasibility__l2_decoder_attention_mixed_precision_physical_feasibility_llama7b_v1.json: decision=dual_stream_area_blocked; precision_profile=q8_k8_v6_a24_s24_w16; best_requested_mode=dual_mac; best_requested_latency_us=1575.373891; best_requested_area_fit=False; best_requested_logic_slack_um2=-397395735.8284; best_requested_compute_area_over_budget_um2=397395735.8284; best_requested_required_compute_density_gain=2.003777; best_feasible_mode=split_mac; best_feasible_latency_us=2042.378179; recommended_next_step=measure a denser dual-stream fused attention datapath or reduce compute replicas before promoting dual_mac.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
