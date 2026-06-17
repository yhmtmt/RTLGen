## Summary
- item_id: `l2_decoder_attention_kv_endpoint_router_sram_composition_softmax_recip_lut_llama7b_v1_r4`
- run_key: `l2_decoder_attention_kv_endpoint_router_sram_composition_softmax_recip_lut_llama7b_v1_r4_run_3556e4f050f260da`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_kv_endpoint_router_sram_composition_softmax_recip_lut_llama7b_v1_r4/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_kv_endpoint_router_sram_composition_softmax_recip_lut_llama7b_v1_r4.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_kv_endpoint_router_sram_composition_softmax_recip_lut_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_kv_endpoint_router_sram_composition_softmax_recip_lut_v1`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_kv_endpoint_router_sram_composition_softmax_recip_lut_v1` plus `docs/developer_agent_review.md`
- execution_source_commit: `768ff27c7ebd8f09b9eb7998ada825f96b703aae`
- review_metadata_source_commit: `768ff27c7ebd8f09b9eb7998ada825f96b703aae`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_kv_endpoint_router_sram_composition`
- comparison_role: `frontier_closure`
- expected_direction: `unknown`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder endpoint/router/SRAM composition evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_endpoint_router_sram_composition__l2_decoder_attention_kv_endpoint_router_sram_composition_softmax_recip_lut_llama7b_v1_r4.json: decision=composition_requires_follow_on_ppa; latency_us=3222.903773; topology=mesh2d; scheduler_policy=locality_aware; reduction_strategy=cluster_tree; cluster_count=16; bank_count=64; link_width_bits=2048; packet_payload_bytes=128; dominant_tile_resource=shared_path; endpoint_width_ratio_vs_measured_ppa=1; router_lanes_for_link=8; fifo_lanes_for_link=8; tile_sram_capacity_fraction_of_selected_local_capacity=0.032113; tile_sram_budget_area_fraction=0.142156; ready_valid_endpoint_passed=True; endpoint_ppa_width_matches_ready_valid_width=True; router_ppa_width_matches_link_width=False; fifo_ppa_width_matches_link_width=False; tile_sram_capacity_covers_selected_local_capacity=False; endpoint_diagnosis=measured_at_ready_valid_width; router_diagnosis=lane_composed_segmented_evidence_available_while_flat_2048_failed; fifo_diagnosis=lane_composed_segmented_evidence_available_while_flat_2048_failed; local_sram_capacity_diagnosis=local_capacity_budget_failed; required_follow_on_ppa=capacity_rebalance_or_smaller_local_sram_required.`

## Focused Comparison
- primary_question: `Does concrete endpoint/router/SRAM composition expose a width, replication, queue, or SRAM area gap that changes the selected Llama7B reciprocal-LUT frontier?`
- comparison_role: `frontier_closure`
- proposal_outcome: `composition_requires_follow_on_ppa`
- comparison_summary: `Decoder endpoint/router/SRAM composition evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_endpoint_router_sram_composition__l2_decoder_attention_kv_endpoint_router_sram_composition_softmax_recip_lut_llama7b_v1_r4.json: decision=composition_requires_follow_on_ppa; latency_us=3222.903773; topology=mesh2d; scheduler_policy=locality_aware; reduction_strategy=cluster_tree; cluster_count=16; bank_count=64; link_width_bits=2048; packet_payload_bytes=128; dominant_tile_resource=shared_path; endpoint_width_ratio_vs_measured_ppa=1; router_lanes_for_link=8; fifo_lanes_for_link=8; tile_sram_capacity_fraction_of_selected_local_capacity=0.032113; tile_sram_budget_area_fraction=0.142156; ready_valid_endpoint_passed=True; endpoint_ppa_width_matches_ready_valid_width=True; router_ppa_width_matches_link_width=False; fifo_ppa_width_matches_link_width=False; tile_sram_capacity_covers_selected_local_capacity=False; endpoint_diagnosis=measured_at_ready_valid_width; router_diagnosis=lane_composed_segmented_evidence_available_while_flat_2048_failed; fifo_diagnosis=lane_composed_segmented_evidence_available_while_flat_2048_failed; local_sram_capacity_diagnosis=local_capacity_budget_failed; required_follow_on_ppa=capacity_rebalance_or_smaller_local_sram_required.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Submission Recovery
- submission_failure_count: `2`
- retry_request_count: `0`
- last_submission_failure: `branch already exists: eval/l2_decoder_attention_kv_endpoint_router_sram_composition_softmax_recip_lut_llama7b_v1_r4/local-r4-composition-rescue`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
