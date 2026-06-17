# Endpoint Ready/Valid Service Probe

## Source Frontier
- source_json: `runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_endpoint_full_onchip_service_schedule__l2_decoder_attention_kv_endpoint_full_onchip_service_schedule_softmax_recip_lut_llama7b_v1_r2.json`
- latency_us: `3222.903773`
- topology: `mesh2d`
- schedule_policy: `prefetch_overlap`
- bank_arbiter_policy: `locality_first`

## Derived RTL Parameters
- DATA_W: `1024`
- BANKS: `4`
- BANK_SEL_W: `2`
- ENDPOINT_QUEUE_DEPTH: `16`
- BANK_QUEUE_DEPTH: `16`

## Result
- decision: `ready_valid_endpoint_policy_passed`
- accepted: `17`
- emitted: `17`
- producer_stalls: `2`
- consumer_stalls: `16`
- endpoint_max: `16`
- bank_max: `4`
- final_cycle: `22`

## Scope
- This probe validates finite ready/valid endpoint buffering, producer/consumer backpressure, and locality-first bank drain for the selected packet and queue sizing.
- It does not replace the full NoC router or SRAM macro timing model, and it does not change HBM/DRAM assumptions.
