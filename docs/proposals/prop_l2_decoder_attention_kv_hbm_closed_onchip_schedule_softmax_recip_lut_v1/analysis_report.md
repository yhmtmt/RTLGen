# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_decoder_attention_kv_hbm_closed_onchip_schedule_softmax_recip_lut_v1`
- `candidate_id`: `l2_decoder_attention_kv_hbm_closed_onchip_schedule_softmax_recip_lut_llama7b_v1`

## Evaluations Consumed
- `l2_decoder_attention_kv_hbm_closed_onchip_schedule_softmax_recip_lut_llama7b_v1`
- `l2_decoder_attention_kv_hbm_closed_onchip_schedule_softmax_recip_lut_llama7b_v1_run_23c73d0286366557`
- source commit: `7540125e5410eadb3b3ac1327aa0859e59087cd8`
- review: PR #908

## Baseline Comparison
- baseline_ref: `None`
- baseline_item_id: `None`
- outcome: `hbm_closed_onchip_schedule_recorded`
- summary: Decoder HBM-closed on-chip schedule evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_hbm_closed_onchip_schedule__l2_decoder_attention_kv_hbm_closed_onchip_schedule_softmax_recip_lut_llama7b_v1.json: decision=hbm_closed_onchip_schedule_recorded; latency_us=2138.84136; latency_slowdown_vs_hbm_closed_source=1.0; dominant_tile_resource=tile_attention; schedule_policy=static_wave; bank_arbiter_policy=locality_first; endpoint_queue_depth_bytes=1024; bank_queue_depth_bytes=1024; router_latency_cycles_per_hop=1; packet_payload_bytes=64; tile_hbm_cycles=1301; tile_attention_cycles=1354; onchip_shared_service_cycles=225.

## Result
- result: `iterate`
- confidence level: merged accepted evidence
- estimated optimization room: pending follow-on comparison
- architecture conclusion robustness: staged evidence
- summary: Decoder HBM-closed on-chip schedule evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_hbm_closed_onchip_schedule__l2_decoder_attention_kv_hbm_closed_onchip_schedule_softmax_recip_lut_llama7b_v1.json: decision=hbm_closed_onchip_schedule_recorded; latency_us=2138.84136; latency_slowdown_vs_hbm_closed_source=1.0; dominant_tile_resource=tile_attention; schedule_policy=static_wave; bank_arbiter_policy=locality_first; endpoint_queue_depth_bytes=1024; bank_queue_depth_bytes=1024; router_latency_cycles_per_hop=1; packet_payload_bytes=64; tile_hbm_cycles=1301; tile_attention_cycles=1354; onchip_shared_service_cycles=225.

## Failures and Caveats
- no additional caveats recorded during automatic finalization

## Recommendation
- `iterate`
- reason: Decoder HBM-closed on-chip schedule evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_hbm_closed_onchip_schedule__l2_decoder_attention_kv_hbm_closed_onchip_schedule_softmax_recip_lut_llama7b_v1.json: decision=hbm_closed_onchip_schedule_recorded; latency_us=2138.84136; latency_slowdown_vs_hbm_closed_source=1.0; dominant_tile_resource=tile_attention; schedule_policy=static_wave; bank_arbiter_policy=locality_first; endpoint_queue_depth_bytes=1024; bank_queue_depth_bytes=1024; router_latency_cycles_per_hop=1; packet_payload_bytes=64; tile_hbm_cycles=1301; tile_attention_cycles=1354; onchip_shared_service_cycles=225.
- next_action: inspect follow-on work after l2_decoder_attention_kv_hbm_closed_onchip_schedule_softmax_recip_lut_llama7b_v1
