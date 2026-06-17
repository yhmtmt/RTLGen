## Summary
- item_id: `l2_decoder_attention_kv_endpoint_full_onchip_service_schedule_softmax_recip_lut_llama7b_v1_r2`
- run_key: `l2_decoder_attention_kv_endpoint_full_onchip_service_schedule_softmax_recip_lut_llama7b_v1_r2_run_40c7c348c504d184`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_kv_endpoint_full_onchip_service_schedule_softmax_recip_lut_llama7b_v1_r2/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_kv_endpoint_full_onchip_service_schedule_softmax_recip_lut_llama7b_v1_r2.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_kv_endpoint_full_onchip_service_softmax_recip_lut_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_kv_endpoint_full_onchip_service_softmax_recip_lut_v1`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_kv_endpoint_full_onchip_service_softmax_recip_lut_v1` plus `docs/developer_agent_review.md`
- execution_source_commit: `7db3cc348ff59e57f12c2e2b7cf380a5302f734a`
- review_metadata_source_commit: `7db3cc348ff59e57f12c2e2b7cf380a5302f734a`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_kv_endpoint_full_onchip_service_schedule`
- comparison_role: `frontier_revision`
- expected_direction: `refine_recip_lut_endpoint_frontier_with_profile_complete_onchip_service_policies`
- expected_reason: `Rerun after precision-profile dedupe and tied-latency PPA/precision ranking fixes so q8/q10/q12 all appear in the decision.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder on-chip SRAM/NoC service evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_endpoint_full_onchip_service_schedule__l2_decoder_attention_kv_endpoint_full_onchip_service_schedule_softmax_recip_lut_llama7b_v1_r2.json: decision=onchip_service_schedule_recorded; measured_l1_profile=hd64_kv8_full_value_p8_ppc2_noc128_softmax_int8_q12; latency_us=3222.903773; latency_slowdown_vs_sram_noc_cap=0.993451; total_cycles=538848; topology=mesh2d; scheduler_policy=locality_aware; schedule_policy=prefetch_overlap; bank_arbiter_policy=locality_first; cluster_count=16; bank_count=64; endpoint_queue_depth_bytes=2048; bank_queue_depth_bytes=2048; router_latency_cycles_per_hop=1; packet_payload_bytes=128; onchip_shared_service_cycles=2503; dominant_tile_resource=shared_path.`

## Focused Comparison
- primary_question: `Does the corrected q8/q10/q12 endpoint full-search frontier remain best under explicit on-chip SRAM/NoC service scheduling?`
- comparison_role: `frontier_revision`
- proposal_outcome: `onchip_service_schedule_recorded`
- comparison_summary: `Decoder on-chip SRAM/NoC service evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_endpoint_full_onchip_service_schedule__l2_decoder_attention_kv_endpoint_full_onchip_service_schedule_softmax_recip_lut_llama7b_v1_r2.json: decision=onchip_service_schedule_recorded; measured_l1_profile=hd64_kv8_full_value_p8_ppc2_noc128_softmax_int8_q12; latency_us=3222.903773; latency_slowdown_vs_sram_noc_cap=0.993451; total_cycles=538848; topology=mesh2d; scheduler_policy=locality_aware; schedule_policy=prefetch_overlap; bank_arbiter_policy=locality_first; cluster_count=16; bank_count=64; endpoint_queue_depth_bytes=2048; bank_queue_depth_bytes=2048; router_latency_cycles_per_hop=1; packet_payload_bytes=128; onchip_shared_service_cycles=2503; dominant_tile_resource=shared_path.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
