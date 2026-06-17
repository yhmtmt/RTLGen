## Summary
- item_id: `l2_decoder_attention_kv_endpoint_router_sram_composition_softmax_recip_lut_llama7b_v1_r2`
- run_key: `l2_decoder_attention_kv_endpoint_router_sram_composition_softmax_recip_lut_llama7b_v1_r2_run_5810710abb241836`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_kv_endpoint_router_sram_composition_softmax_recip_lut_llama7b_v1_r2/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_kv_endpoint_router_sram_composition_softmax_recip_lut_llama7b_v1_r2.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_kv_endpoint_router_sram_composition_softmax_recip_lut_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_kv_endpoint_router_sram_composition_softmax_recip_lut_v1`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_kv_endpoint_router_sram_composition_softmax_recip_lut_v1` plus `docs/developer_agent_review.md`
- execution_source_commit: `9ca357bf7a6b593e4b0e7b6fe25ac10ee3e7f01a`
- review_metadata_source_commit: `9ca357bf7a6b593e4b0e7b6fe25ac10ee3e7f01a`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_kv_endpoint_router_sram_composition`
- comparison_role: `frontier_closure`
- expected_direction: `close_recip_lut_endpoint_router_sram_composition_for_selected_frontier`
- expected_reason: `Use reciprocal-LUT ready/valid output and q12 endpoint service frontier to audit concrete endpoint/router/SRAM composition, with the composition audit promoted into the decision record.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder endpoint/router/SRAM composition evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_endpoint_router_sram_composition__l2_decoder_attention_kv_endpoint_router_sram_composition_softmax_recip_lut_llama7b_v1_r2.json: decision=composition_requires_follow_on_ppa; latency_us=3222.903773; topology=mesh2d; scheduler_policy=locality_aware; reduction_strategy=cluster_tree; cluster_count=16; bank_count=64; link_width_bits=2048; packet_payload_bytes=128; dominant_tile_resource=shared_path; endpoint_width_ratio_vs_measured_ppa=8; router_lanes_for_link=16; fifo_lanes_for_link=16; tile_sram_capacity_fraction_of_selected_local_capacity=0.032113; tile_sram_budget_area_fraction=0.142156; ready_valid_endpoint_passed=True; endpoint_ppa_width_matches_ready_valid_width=False; router_ppa_width_matches_link_width=False; fifo_ppa_width_matches_link_width=False; tile_sram_capacity_covers_selected_local_capacity=False; required_follow_on_ppa=endpoint_ppa_width_matches_ready_valid_width,router_ppa_width_matches_link_width,fifo_ppa_width_matches_link_width,full_local_capacity_sram_macro_profile_missing.`

## Focused Comparison
- primary_question: `Does concrete endpoint/router/SRAM composition expose a width, replication, queue, or SRAM area gap that changes the selected Llama7B reciprocal-LUT frontier?`
- comparison_role: `frontier_closure`
- proposal_outcome: `composition_requires_follow_on_ppa`
- comparison_summary: `Decoder endpoint/router/SRAM composition evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_endpoint_router_sram_composition__l2_decoder_attention_kv_endpoint_router_sram_composition_softmax_recip_lut_llama7b_v1_r2.json: decision=composition_requires_follow_on_ppa; latency_us=3222.903773; topology=mesh2d; scheduler_policy=locality_aware; reduction_strategy=cluster_tree; cluster_count=16; bank_count=64; link_width_bits=2048; packet_payload_bytes=128; dominant_tile_resource=shared_path; endpoint_width_ratio_vs_measured_ppa=8; router_lanes_for_link=16; fifo_lanes_for_link=16; tile_sram_capacity_fraction_of_selected_local_capacity=0.032113; tile_sram_budget_area_fraction=0.142156; ready_valid_endpoint_passed=True; endpoint_ppa_width_matches_ready_valid_width=False; router_ppa_width_matches_link_width=False; fifo_ppa_width_matches_link_width=False; tile_sram_capacity_covers_selected_local_capacity=False; required_follow_on_ppa=endpoint_ppa_width_matches_ready_valid_width,router_ppa_width_matches_link_width,fifo_ppa_width_matches_link_width,full_local_capacity_sram_macro_profile_missing.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
