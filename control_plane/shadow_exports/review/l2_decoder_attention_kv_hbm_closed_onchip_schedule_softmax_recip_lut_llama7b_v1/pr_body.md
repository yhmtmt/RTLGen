## Summary
- item_id: `l2_decoder_attention_kv_hbm_closed_onchip_schedule_softmax_recip_lut_llama7b_v1`
- run_key: `l2_decoder_attention_kv_hbm_closed_onchip_schedule_softmax_recip_lut_llama7b_v1_run_23c73d0286366557`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_kv_hbm_closed_onchip_schedule_softmax_recip_lut_llama7b_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_kv_hbm_closed_onchip_schedule_softmax_recip_lut_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_kv_hbm_closed_onchip_schedule_softmax_recip_lut_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_kv_hbm_closed_onchip_schedule_softmax_recip_lut_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_kv_hbm_closed_onchip_schedule_softmax_recip_lut_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `7540125e5410eadb3b3ac1327aa0859e59087cd8`
- review_metadata_source_commit: `7540125e5410eadb3b3ac1327aa0859e59087cd8`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_kv_hbm_closed_onchip_schedule`
- comparison_role: `frontier_closure`
- expected_direction: `record_softmax_recip_hbm_closed_onchip_schedule_frontier`
- expected_reason: `Record whether re-sweeping on-chip SRAM/NoC service knobs changes the current softmax-recip measured-HBM Llama7B attention frontier before subtile pipelining.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder HBM-closed on-chip schedule evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_hbm_closed_onchip_schedule__l2_decoder_attention_kv_hbm_closed_onchip_schedule_softmax_recip_lut_llama7b_v1.json: decision=hbm_closed_onchip_schedule_recorded; latency_us=2138.84136; latency_slowdown_vs_hbm_closed_source=1.0; dominant_tile_resource=tile_attention; schedule_policy=static_wave; bank_arbiter_policy=locality_first; endpoint_queue_depth_bytes=1024; bank_queue_depth_bytes=1024; router_latency_cycles_per_hop=1; packet_payload_bytes=64; tile_hbm_cycles=1301; tile_attention_cycles=1354; onchip_shared_service_cycles=225.`

## Focused Comparison
- primary_question: `Does re-optimizing on-chip SRAM and NoC service knobs on top of the softmax-recip measured-HBM Llama7B frontier change latency or the dominant resource?`
- comparison_role: `frontier_closure`
- proposal_outcome: `hbm_closed_onchip_schedule_recorded`
- comparison_summary: `Decoder HBM-closed on-chip schedule evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_hbm_closed_onchip_schedule__l2_decoder_attention_kv_hbm_closed_onchip_schedule_softmax_recip_lut_llama7b_v1.json: decision=hbm_closed_onchip_schedule_recorded; latency_us=2138.84136; latency_slowdown_vs_hbm_closed_source=1.0; dominant_tile_resource=tile_attention; schedule_policy=static_wave; bank_arbiter_policy=locality_first; endpoint_queue_depth_bytes=1024; bank_queue_depth_bytes=1024; router_latency_cycles_per_hop=1; packet_payload_bytes=64; tile_hbm_cycles=1301; tile_attention_cycles=1354; onchip_shared_service_cycles=225.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Submission Recovery
- submission_failure_count: `2`
- retry_request_count: `0`
- last_submission_failure: `work item l2_decoder_attention_kv_hbm_closed_onchip_schedule_softmax_recip_lut_llama7b_v1 is not eligible for submission: developer_loop proposal is still a template placeholder`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
