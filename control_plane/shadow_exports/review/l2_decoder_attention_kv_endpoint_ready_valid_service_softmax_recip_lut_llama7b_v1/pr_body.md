## Summary
- item_id: `l2_decoder_attention_kv_endpoint_ready_valid_service_softmax_recip_lut_llama7b_v1`
- run_key: `l2_decoder_attention_kv_endpoint_ready_valid_service_softmax_recip_lut_llama7b_v1_run_5ce04d3cc6df47c4`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_kv_endpoint_ready_valid_service_softmax_recip_lut_llama7b_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_kv_endpoint_ready_valid_service_softmax_recip_lut_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_kv_endpoint_ready_valid_service_softmax_recip_lut_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_kv_endpoint_ready_valid_service_softmax_recip_lut_v1`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_kv_endpoint_ready_valid_service_softmax_recip_lut_v1` plus `docs/developer_agent_review.md`
- execution_source_commit: `bcc381dd2e2251fccf74a2095c59caf9c38821c6`
- review_metadata_source_commit: `bcc381dd2e2251fccf74a2095c59caf9c38821c6`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_kv_endpoint_ready_valid_service`
- comparison_role: `frontier_closure`
- expected_direction: `close_recip_lut_endpoint_ready_valid_service_for_selected_frontier`
- expected_reason: `Use the corrected profile-complete q12 reciprocal-LUT endpoint on-chip frontier as the source for concrete ready/valid endpoint queue probing.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder endpoint ready/valid service evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_endpoint_ready_valid_service__l2_decoder_attention_kv_endpoint_ready_valid_service_softmax_recip_lut_llama7b_v1.json: decision=ready_valid_endpoint_policy_passed; rtl_passed=True; latency_us=3222.903773; schedule_policy=prefetch_overlap; bank_arbiter_policy=locality_first; endpoint_queue_depth_bytes=2048; bank_queue_depth_bytes=2048; packet_payload_bytes=128.`

## Focused Comparison
- primary_question: `Does the concrete endpoint ready/valid probe preserve the selected q12 reciprocal-LUT frontier without exposing a queue/backpressure bottleneck that changes the architecture conclusion?`
- comparison_role: `frontier_closure`
- proposal_outcome: `ready_valid_endpoint_policy_passed`
- comparison_summary: `Decoder endpoint ready/valid service evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_endpoint_ready_valid_service__l2_decoder_attention_kv_endpoint_ready_valid_service_softmax_recip_lut_llama7b_v1.json: decision=ready_valid_endpoint_policy_passed; rtl_passed=True; latency_us=3222.903773; schedule_policy=prefetch_overlap; bank_arbiter_policy=locality_first; endpoint_queue_depth_bytes=2048; bank_queue_depth_bytes=2048; packet_payload_bytes=128.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
