# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_decoder_attention_kv_hbm_closed_onchip_schedule_v1`
- `candidate_id`: `l2_decoder_attention_kv_hbm_closed_onchip_schedule_llama7b_v1`

## Evaluations Consumed
- `l2_decoder_attention_kv_hbm_closed_onchip_schedule_llama7b_v1`
- `l2_decoder_attention_kv_hbm_closed_onchip_schedule_llama7b_v1_run_dd10fc86a91d072b`
- source commit: `a9c25db65e0909e90931ed524fd0dca6c16a30f0`
- review: PR #826

## Baseline Comparison
- baseline_ref: `None`
- baseline_item_id: `None`
- outcome: `hbm_closed_onchip_schedule_recorded`
- summary: Decoder HBM-closed on-chip schedule evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_hbm_closed_onchip_schedule__l2_decoder_attention_kv_hbm_closed_onchip_schedule_llama7b_v1.json: decision=hbm_closed_onchip_schedule_recorded; latency_us=2138.84136; latency_slowdown_vs_hbm_closed_source=1.0; dominant_tile_resource=tile_attention; schedule_policy=static_wave; bank_arbiter_policy=locality_first; endpoint_queue_depth_bytes=1024; bank_queue_depth_bytes=1024; router_latency_cycles_per_hop=1; packet_payload_bytes=64; tile_hbm_cycles=1301; tile_attention_cycles=1354; onchip_shared_service_cycles=225.

## Result
- result: `iterate`
- confidence level: merged accepted evidence
- estimated optimization room: pending follow-on comparison
- architecture conclusion robustness: staged evidence
- summary: Decoder HBM-closed on-chip schedule evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_hbm_closed_onchip_schedule__l2_decoder_attention_kv_hbm_closed_onchip_schedule_llama7b_v1.json: decision=hbm_closed_onchip_schedule_recorded; latency_us=2138.84136; latency_slowdown_vs_hbm_closed_source=1.0; dominant_tile_resource=tile_attention; schedule_policy=static_wave; bank_arbiter_policy=locality_first; endpoint_queue_depth_bytes=1024; bank_queue_depth_bytes=1024; router_latency_cycles_per_hop=1; packet_payload_bytes=64; tile_hbm_cycles=1301; tile_attention_cycles=1354; onchip_shared_service_cycles=225.

## Failures and Caveats
- no additional caveats recorded during automatic finalization

## Recommendation
- `iterate`
- reason: Decoder HBM-closed on-chip schedule evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_hbm_closed_onchip_schedule__l2_decoder_attention_kv_hbm_closed_onchip_schedule_llama7b_v1.json: decision=hbm_closed_onchip_schedule_recorded; latency_us=2138.84136; latency_slowdown_vs_hbm_closed_source=1.0; dominant_tile_resource=tile_attention; schedule_policy=static_wave; bank_arbiter_policy=locality_first; endpoint_queue_depth_bytes=1024; bank_queue_depth_bytes=1024; router_latency_cycles_per_hop=1; packet_payload_bytes=64; tile_hbm_cycles=1301; tile_attention_cycles=1354; onchip_shared_service_cycles=225.
- next_action: inspect follow-on work after l2_decoder_attention_kv_hbm_closed_onchip_schedule_llama7b_v1
