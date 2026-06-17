# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_decoder_attention_kv_subtile_pipeline_schedule_softmax_recip_lut_v1`
- `candidate_id`: `l2_decoder_attention_kv_subtile_pipeline_schedule_softmax_recip_lut_llama7b_v1`

## Evaluations Consumed
- `l2_decoder_attention_kv_subtile_pipeline_schedule_softmax_recip_lut_llama7b_v1`
- `l2_decoder_attention_kv_subtile_pipeline_schedule_softmax_recip_lut_llama7b_v1_run_6364ceb1a3b8a12f`
- source commit: `f81774cba0b9e26dd9a6d15e8959ea6854bd0fa2`
- review: PR #909

## Baseline Comparison
- baseline_ref: `None`
- baseline_item_id: `None`
- outcome: `subtile_pipeline_schedule_recorded`
- summary: Decoder sub-tile pipeline schedule evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_subtile_pipeline_schedule__l2_decoder_attention_kv_subtile_pipeline_schedule_softmax_recip_lut_llama7b_v1.json: decision=subtile_pipeline_schedule_recorded; latency_us=1575.373891; latency_speedup_vs_hbm_closed_source=1.357672; tile_service_cycles=986; pipeline_attention_cycles=986; dominant_tile_resource=pipeline_attention; compute_mode=dual_mac; compute_area_multiplier=2.0; normalize_strategy=online_correction; subtile_count=8; subtile_buffer_count=4; prefetch_distance=3; required_stream_buffer_bytes=532608; available_local_capacity_bytes=614656; hbm_exposed_cycles=815; hbm_floor_gap_cycles=-315.

## Result
- result: `iterate`
- confidence level: merged accepted evidence
- estimated optimization room: pending follow-on comparison
- architecture conclusion robustness: staged evidence
- summary: Decoder sub-tile pipeline schedule evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_subtile_pipeline_schedule__l2_decoder_attention_kv_subtile_pipeline_schedule_softmax_recip_lut_llama7b_v1.json: decision=subtile_pipeline_schedule_recorded; latency_us=1575.373891; latency_speedup_vs_hbm_closed_source=1.357672; tile_service_cycles=986; pipeline_attention_cycles=986; dominant_tile_resource=pipeline_attention; compute_mode=dual_mac; compute_area_multiplier=2.0; normalize_strategy=online_correction; subtile_count=8; subtile_buffer_count=4; prefetch_distance=3; required_stream_buffer_bytes=532608; available_local_capacity_bytes=614656; hbm_exposed_cycles=815; hbm_floor_gap_cycles=-315.

## Failures and Caveats
- no additional caveats recorded during automatic finalization

## Recommendation
- `iterate`
- reason: Decoder sub-tile pipeline schedule evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_subtile_pipeline_schedule__l2_decoder_attention_kv_subtile_pipeline_schedule_softmax_recip_lut_llama7b_v1.json: decision=subtile_pipeline_schedule_recorded; latency_us=1575.373891; latency_speedup_vs_hbm_closed_source=1.357672; tile_service_cycles=986; pipeline_attention_cycles=986; dominant_tile_resource=pipeline_attention; compute_mode=dual_mac; compute_area_multiplier=2.0; normalize_strategy=online_correction; subtile_count=8; subtile_buffer_count=4; prefetch_distance=3; required_stream_buffer_bytes=532608; available_local_capacity_bytes=614656; hbm_exposed_cycles=815; hbm_floor_gap_cycles=-315.
- next_action: inspect follow-on work after l2_decoder_attention_kv_subtile_pipeline_schedule_softmax_recip_lut_llama7b_v1
