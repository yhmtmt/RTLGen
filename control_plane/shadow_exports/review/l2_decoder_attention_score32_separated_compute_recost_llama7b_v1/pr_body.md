## Summary
- item_id: `l2_decoder_attention_score32_separated_compute_recost_llama7b_v1`
- run_key: `l2_decoder_attention_score32_separated_compute_recost_llama7b_v1_run_142d1ae462e5b7ad`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `2/2 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_score32_separated_compute_recost_llama7b_v1/evaluated.json`
- metrics_rows_count: `0`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_score32_separated_compute_recost_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_score32_separated_compute_recost_llama7b_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_score32_separated_compute_recost_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_score32_separated_compute_recost_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `d50b265d58b2390374577422d11ed84502663414`
- review_metadata_source_commit: `d50b265d58b2390374577422d11ed84502663414`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_score32_separated_compute_recost`
- comparison_role: `score32_separated_compute_recost`
- expected_direction: `record_score32_separated_compute_recost`
- expected_reason: `Use the measured-component recost to decide whether the next score32 priority should be composed RTL implementation rather than another analytical subtotal adjustment.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder score32 separated-compute recost evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_score32_separated_compute_recost__l2_decoder_attention_score32_separated_compute_recost_llama7b_v1.json: decision=score32_separated_compute_recost_requires_precision_aligned_rtl; candidate_id=score32_separated_dense_int8_shared_vector_softmax_c16_hbm_c4; latency_us=1575.373891; token_throughput_per_s=634.769946177812; energy_mj_per_token=135.755919226219; compute_control_energy_mj_per_token=1.537270795311; logic_area_mm2=179.6236140317; schedule_clock_ns=5.9811; timing_ok=True; energy_source_precision_profile=q8_k8_v6_a24_s8_w8_recip_lut_q10_int8_compute; precision_aligned=False; quality_target_backed=True; quality_backed=False; promotable=False; abstraction_status=measured_components_unmeasured_composition; full_wrapper_replication_removed=True; old_full_wrapper_replica_count=815; old_full_wrapper_area_um2=490074.0; old_full_wrapper_power_mw=35.3; recommended_next_step=Build and measure the precision-aligned separated producer/consumer RTL composition, then run full-path tensor-hash equivalence.; remaining_abstractions=['the inherited q8/k8/v6 reciprocal-LUT energy row is not precision-aligned with the q8/k8/v8 score32 exp-LUT/div target', 'producer-to-score32 ready/valid queues and backpressure are not yet embodied in one composed RTL block', 'the inherited dense-int8 schedule has not yet been replayed against the separated score32 consumer', 'full QK-to-softmax-to-V RTL/perf-sim tensor-hash equivalence is pending for the separated composition', 'NoC and SRAM energy remain profile-scaled rather than gate-level toggle power', 'HBM energy is source-backed aggregate energy, not vendor current signoff'].`

## Focused Comparison
- primary_question: `Does measured-component separated compute recost make the current quality-aware score32 frontier compelling enough to prioritize composed RTL work?`
- comparison_role: `score32_separated_compute_recost`
- proposal_outcome: `score32_separated_compute_recost_requires_precision_aligned_rtl`
- comparison_summary: `Decoder score32 separated-compute recost evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_score32_separated_compute_recost__l2_decoder_attention_score32_separated_compute_recost_llama7b_v1.json: decision=score32_separated_compute_recost_requires_precision_aligned_rtl; candidate_id=score32_separated_dense_int8_shared_vector_softmax_c16_hbm_c4; latency_us=1575.373891; token_throughput_per_s=634.769946177812; energy_mj_per_token=135.755919226219; compute_control_energy_mj_per_token=1.537270795311; logic_area_mm2=179.6236140317; schedule_clock_ns=5.9811; timing_ok=True; energy_source_precision_profile=q8_k8_v6_a24_s8_w8_recip_lut_q10_int8_compute; precision_aligned=False; quality_target_backed=True; quality_backed=False; promotable=False; abstraction_status=measured_components_unmeasured_composition; full_wrapper_replication_removed=True; old_full_wrapper_replica_count=815; old_full_wrapper_area_um2=490074.0; old_full_wrapper_power_mw=35.3; recommended_next_step=Build and measure the precision-aligned separated producer/consumer RTL composition, then run full-path tensor-hash equivalence.; remaining_abstractions=['the inherited q8/k8/v6 reciprocal-LUT energy row is not precision-aligned with the q8/k8/v8 score32 exp-LUT/div target', 'producer-to-score32 ready/valid queues and backpressure are not yet embodied in one composed RTL block', 'the inherited dense-int8 schedule has not yet been replayed against the separated score32 consumer', 'full QK-to-softmax-to-V RTL/perf-sim tensor-hash equivalence is pending for the separated composition', 'NoC and SRAM energy remain profile-scaled rather than gate-level toggle power', 'HBM energy is source-backed aggregate energy, not vendor current signoff'].`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
