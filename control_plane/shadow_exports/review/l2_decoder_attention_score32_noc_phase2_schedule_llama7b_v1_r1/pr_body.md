## Summary
- item_id: `l2_decoder_attention_score32_noc_phase2_schedule_llama7b_v1_r1`
- run_key: `l2_decoder_attention_score32_noc_phase2_schedule_llama7b_v1_r1_run_d97459a58e228077`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `2/2 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_score32_noc_phase2_schedule_llama7b_v1_r1/evaluated.json`
- metrics_rows_count: `0`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_score32_noc_phase2_schedule_llama7b_v1_r1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_score32_noc_phase2_schedule_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_score32_noc_phase2_schedule_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_score32_noc_phase2_schedule_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `b6cff4447a0f71a7e5c6e45a452f4475517c9e47`
- review_metadata_source_commit: `b6cff4447a0f71a7e5c6e45a452f4475517c9e47`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_score32_noc_phase2_schedule`
- comparison_role: `closure_detail`
- expected_direction: `iterate`
- expected_reason: `Use clock-corrected routed service evidence to replace the old NoC scalar or identify the next measured-clock/SRAM-placement adapter.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder score32 NoC Phase 2 schedule evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_score32_noc_phase2_schedule__l2_decoder_attention_score32_noc_phase2_schedule_llama7b_v1_r1.json: decision=score32_noc_phase2_schedule_recorded; simulated_wave_count=8; compute_layer_time_ns=421511.3976; noc_clock_ns=1.0; cycles_to_drain=397004; drain_time_ns=397004.0; drain_within_source_compute_layer_envelope=True; scheduled_packet_count=11576; scheduled_flit_count=92128; router_contention_cycles=36762; endpoint_input_stall_cycles_total=320240; collision_free_reuse_proven=True.`

## Focused Comparison
- primary_question: `When the full checked-in score32 recost traffic quantities are mapped onto an explicit static 4x4 segmented mesh with 4 VCs and deterministic XY routing, what routed drain time, contention, and link pressure appear across all declared waves?`
- comparison_role: `closure_detail`
- proposal_outcome: `score32_noc_phase2_schedule_recorded`
- comparison_summary: `Decoder score32 NoC Phase 2 schedule evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_score32_noc_phase2_schedule__l2_decoder_attention_score32_noc_phase2_schedule_llama7b_v1_r1.json: decision=score32_noc_phase2_schedule_recorded; simulated_wave_count=8; compute_layer_time_ns=421511.3976; noc_clock_ns=1.0; cycles_to_drain=397004; drain_time_ns=397004.0; drain_within_source_compute_layer_envelope=True; scheduled_packet_count=11576; scheduled_flit_count=92128; router_contention_cycles=36762; endpoint_input_stall_cycles_total=320240; collision_free_reuse_proven=True.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
