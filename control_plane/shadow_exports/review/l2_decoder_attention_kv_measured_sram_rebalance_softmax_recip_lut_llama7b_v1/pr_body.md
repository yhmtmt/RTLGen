## Summary
- item_id: `l2_decoder_attention_kv_measured_sram_rebalance_softmax_recip_lut_llama7b_v1`
- run_key: `l2_decoder_attention_kv_measured_sram_rebalance_softmax_recip_lut_llama7b_v1_run_e557c6e917a916c7`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_kv_measured_sram_rebalance_softmax_recip_lut_llama7b_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_kv_measured_sram_rebalance_softmax_recip_lut_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_kv_measured_sram_rebalance_softmax_recip_lut_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_kv_measured_sram_rebalance_softmax_recip_lut_v1`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_kv_measured_sram_rebalance_softmax_recip_lut_v1` plus `docs/developer_agent_review.md`
- execution_source_commit: `c569ea33f5194a80660fe36e50cdac8878a3da59`
- review_metadata_source_commit: `c569ea33f5194a80660fe36e50cdac8878a3da59`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_kv_measured_sram_rebalance`
- comparison_role: `frontier_closure`
- expected_direction: `record_measured_sram_rebalanced_frontier`
- expected_reason: `Use current softmax-recip r2 endpoint schedule plus r4 endpoint/router/SRAM composition evidence to close the remaining local SRAM capacity abstraction.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder measured-SRAM rebalance evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_measured_sram_rebalance__l2_decoder_attention_kv_measured_sram_rebalance_softmax_recip_lut_llama7b_v1.json: decision=measured_sram_rebalance_recorded; latency_us=2138.84136; hbm_byte_share=0.983398438; measured_shared_sram_capacity_mib=68.0; local_capacity_bytes_per_cluster=614656; abstract_local_capacity_bytes_per_cluster_replaced=19140624; dominant_tile_resource=tile_attention.`

## Focused Comparison
- primary_question: `What is the best endpoint service schedule after replacing abstract local/shared SRAM capacity with measured SRAM capacity under the same SRAM area budget?`
- comparison_role: `frontier_closure`
- proposal_outcome: `measured_sram_rebalance_recorded`
- comparison_summary: `Decoder measured-SRAM rebalance evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_measured_sram_rebalance__l2_decoder_attention_kv_measured_sram_rebalance_softmax_recip_lut_llama7b_v1.json: decision=measured_sram_rebalance_recorded; latency_us=2138.84136; hbm_byte_share=0.983398438; measured_shared_sram_capacity_mib=68.0; local_capacity_bytes_per_cluster=614656; abstract_local_capacity_bytes_per_cluster_replaced=19140624; dominant_tile_resource=tile_attention.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
