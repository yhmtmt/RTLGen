# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_decoder_attention_kv_endpoint_full_onchip_service_softmax_recip_lut_v1`
- `candidate_id`: `l2_decoder_attention_kv_endpoint_full_onchip_service_schedule_softmax_recip_lut_llama7b_v1`

## Evaluations Consumed
- `l2_decoder_attention_kv_endpoint_full_onchip_service_schedule_softmax_recip_lut_llama7b_v1`
- `l2_decoder_attention_kv_endpoint_full_onchip_service_schedule_softmax_recip_lut_llama7b_v1_run_ef7d6da71a712d83`
- source commit: `0ca861d782d0cd50bd0fc74b314337cdc0881fb3`
- review: PR #880

## Baseline Comparison
- baseline_ref: `None`
- baseline_item_id: `None`
- outcome: `onchip_service_schedule_recorded`
- summary: Decoder on-chip SRAM/NoC service evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_endpoint_full_onchip_service_schedule__l2_decoder_attention_kv_endpoint_full_onchip_service_schedule_softmax_recip_lut_llama7b_v1.json: decision=onchip_service_schedule_recorded; measured_l1_profile=hd64_kv8_full_value_p8_ppc2_noc128_softmax_int8_q8; latency_us=3222.903773; latency_slowdown_vs_sram_noc_cap=0.993451; total_cycles=538848; topology=mesh2d; scheduler_policy=locality_aware; schedule_policy=prefetch_overlap; bank_arbiter_policy=locality_first; cluster_count=16; bank_count=64; endpoint_queue_depth_bytes=2048; bank_queue_depth_bytes=2048; router_latency_cycles_per_hop=1; packet_payload_bytes=128; onchip_shared_service_cycles=2503; dominant_tile_resource=shared_path.

## Result
- result: `iterate`
- confidence level: merged accepted evidence
- estimated optimization room: pending follow-on comparison
- architecture conclusion robustness: staged evidence
- summary: Decoder on-chip SRAM/NoC service evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_endpoint_full_onchip_service_schedule__l2_decoder_attention_kv_endpoint_full_onchip_service_schedule_softmax_recip_lut_llama7b_v1.json: decision=onchip_service_schedule_recorded; measured_l1_profile=hd64_kv8_full_value_p8_ppc2_noc128_softmax_int8_q8; latency_us=3222.903773; latency_slowdown_vs_sram_noc_cap=0.993451; total_cycles=538848; topology=mesh2d; scheduler_policy=locality_aware; schedule_policy=prefetch_overlap; bank_arbiter_policy=locality_first; cluster_count=16; bank_count=64; endpoint_queue_depth_bytes=2048; bank_queue_depth_bytes=2048; router_latency_cycles_per_hop=1; packet_payload_bytes=128; onchip_shared_service_cycles=2503; dominant_tile_resource=shared_path.

## Failures and Caveats
- no additional caveats recorded during automatic finalization

## Recommendation
- `iterate`
- reason: Decoder on-chip SRAM/NoC service evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_endpoint_full_onchip_service_schedule__l2_decoder_attention_kv_endpoint_full_onchip_service_schedule_softmax_recip_lut_llama7b_v1.json: decision=onchip_service_schedule_recorded; measured_l1_profile=hd64_kv8_full_value_p8_ppc2_noc128_softmax_int8_q8; latency_us=3222.903773; latency_slowdown_vs_sram_noc_cap=0.993451; total_cycles=538848; topology=mesh2d; scheduler_policy=locality_aware; schedule_policy=prefetch_overlap; bank_arbiter_policy=locality_first; cluster_count=16; bank_count=64; endpoint_queue_depth_bytes=2048; bank_queue_depth_bytes=2048; router_latency_cycles_per_hop=1; packet_payload_bytes=128; onchip_shared_service_cycles=2503; dominant_tile_resource=shared_path.
- next_action: inspect follow-on work after l2_decoder_attention_kv_endpoint_full_onchip_service_schedule_softmax_recip_lut_llama7b_v1
