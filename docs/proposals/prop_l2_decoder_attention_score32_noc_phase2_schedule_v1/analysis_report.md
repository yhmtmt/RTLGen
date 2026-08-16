# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_decoder_attention_score32_noc_phase2_schedule_v1`
- `candidate_id`: `l2_decoder_attention_score32_noc_phase2_schedule_llama7b_v1_r1`

## Evaluations Consumed
- `l2_decoder_attention_score32_noc_phase2_schedule_llama7b_v1_r1`
- `l2_decoder_attention_score32_noc_phase2_schedule_llama7b_v1_r1_run_d97459a58e228077`
- source commit: `b6cff4447a0f71a7e5c6e45a452f4475517c9e47`
- review: PR #1670

## Baseline Comparison
- baseline_ref: `None`
- baseline_item_id: `None`
- outcome: `score32_noc_phase2_schedule_recorded`
- summary: Decoder score32 NoC Phase 2 schedule evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_score32_noc_phase2_schedule__l2_decoder_attention_score32_noc_phase2_schedule_llama7b_v1_r1.json: decision=score32_noc_phase2_schedule_recorded; simulated_wave_count=8; compute_layer_time_ns=421511.3976; noc_clock_ns=1.0; cycles_to_drain=397004; drain_time_ns=397004.0; drain_within_source_compute_layer_envelope=True; scheduled_packet_count=11576; scheduled_flit_count=92128; router_contention_cycles=36762; endpoint_input_stall_cycles_total=320240; collision_free_reuse_proven=True.

## Result
- result: `iterate`
- confidence level: merged accepted evidence
- estimated optimization room: pending follow-on comparison
- architecture conclusion robustness: staged evidence
- summary: Decoder score32 NoC Phase 2 schedule evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_score32_noc_phase2_schedule__l2_decoder_attention_score32_noc_phase2_schedule_llama7b_v1_r1.json: decision=score32_noc_phase2_schedule_recorded; simulated_wave_count=8; compute_layer_time_ns=421511.3976; noc_clock_ns=1.0; cycles_to_drain=397004; drain_time_ns=397004.0; drain_within_source_compute_layer_envelope=True; scheduled_packet_count=11576; scheduled_flit_count=92128; router_contention_cycles=36762; endpoint_input_stall_cycles_total=320240; collision_free_reuse_proven=True.

## Failures and Caveats
- no additional caveats recorded during automatic finalization

## Recommendation
- `iterate`
- reason: Decoder score32 NoC Phase 2 schedule evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_score32_noc_phase2_schedule__l2_decoder_attention_score32_noc_phase2_schedule_llama7b_v1_r1.json: decision=score32_noc_phase2_schedule_recorded; simulated_wave_count=8; compute_layer_time_ns=421511.3976; noc_clock_ns=1.0; cycles_to_drain=397004; drain_time_ns=397004.0; drain_within_source_compute_layer_envelope=True; scheduled_packet_count=11576; scheduled_flit_count=92128; router_contention_cycles=36762; endpoint_input_stall_cycles_total=320240; collision_free_reuse_proven=True.
- next_action: inspect follow-on work after l2_decoder_attention_score32_noc_phase2_schedule_llama7b_v1_r1
