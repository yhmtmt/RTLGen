## Summary
- item_id: `l2_decoder_attention_kv_subtile_pipeline_schedule_softmax_recip_lut_llama7b_v1`
- run_key: `l2_decoder_attention_kv_subtile_pipeline_schedule_softmax_recip_lut_llama7b_v1_run_6364ceb1a3b8a12f`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_kv_subtile_pipeline_schedule_softmax_recip_lut_llama7b_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_kv_subtile_pipeline_schedule_softmax_recip_lut_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_kv_subtile_pipeline_schedule_softmax_recip_lut_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_kv_subtile_pipeline_schedule_softmax_recip_lut_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_kv_subtile_pipeline_schedule_softmax_recip_lut_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `f81774cba0b9e26dd9a6d15e8959ea6854bd0fa2`
- review_metadata_source_commit: `f81774cba0b9e26dd9a6d15e8959ea6854bd0fa2`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_kv_subtile_pipeline_schedule`
- comparison_role: `frontier_closure`
- expected_direction: `record_softmax_recip_subtile_pipeline_schedule_frontier`
- expected_reason: `Evaluate whether sub-tile QK/softmax/V pipelining reduces the tile_attention bottleneck after softmax-recip measured-HBM and HBM-closed on-chip service closure.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder sub-tile pipeline schedule evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_subtile_pipeline_schedule__l2_decoder_attention_kv_subtile_pipeline_schedule_softmax_recip_lut_llama7b_v1.json: decision=subtile_pipeline_schedule_recorded; latency_us=1575.373891; latency_speedup_vs_hbm_closed_source=1.357672; tile_service_cycles=986; pipeline_attention_cycles=986; dominant_tile_resource=pipeline_attention; compute_mode=dual_mac; compute_area_multiplier=2.0; normalize_strategy=online_correction; subtile_count=8; subtile_buffer_count=4; prefetch_distance=3; required_stream_buffer_bytes=532608; available_local_capacity_bytes=614656; hbm_exposed_cycles=815; hbm_floor_gap_cycles=-315.`

## Focused Comparison
- primary_question: `Does sub-tile QK/softmax/V pipelining improve the softmax-recip HBM-closed Llama7B attention frontier without exceeding measured local SRAM capacity?`
- comparison_role: `frontier_closure`
- proposal_outcome: `subtile_pipeline_schedule_recorded`
- comparison_summary: `Decoder sub-tile pipeline schedule evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_subtile_pipeline_schedule__l2_decoder_attention_kv_subtile_pipeline_schedule_softmax_recip_lut_llama7b_v1.json: decision=subtile_pipeline_schedule_recorded; latency_us=1575.373891; latency_speedup_vs_hbm_closed_source=1.357672; tile_service_cycles=986; pipeline_attention_cycles=986; dominant_tile_resource=pipeline_attention; compute_mode=dual_mac; compute_area_multiplier=2.0; normalize_strategy=online_correction; subtile_count=8; subtile_buffer_count=4; prefetch_distance=3; required_stream_buffer_bytes=532608; available_local_capacity_bytes=614656; hbm_exposed_cycles=815; hbm_floor_gap_cycles=-315.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Submission Recovery
- submission_failure_count: `1`
- retry_request_count: `0`
- last_submission_failure: `work item l2_decoder_attention_kv_subtile_pipeline_schedule_softmax_recip_lut_llama7b_v1 is not eligible for submission: developer_loop proposal linkage does not resolve to a proposal`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
