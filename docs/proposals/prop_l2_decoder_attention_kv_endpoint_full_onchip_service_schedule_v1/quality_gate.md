# Quality Gate

## Proposal
- `proposal_id`: `prop_l2_decoder_attention_kv_endpoint_full_onchip_service_schedule_v1`
- `title`: `Endpoint full-search on-chip service Llama7B schedule`

## Why This Gate Is Required
- The current best Llama7B point is selected by practical SRAM/endpoint caps but still uses a compact service-envelope model.
- The next least-abstract comparison should model endpoint queues, bank queues, packet payload, router hop latency, SRAM bank arbitration, and overlap policy explicitly.

## Reference
- endpoint_full_search_ref: `l2_decoder_attention_kv_endpoint_sram_noc_full_search_schedule_llama7b_v1`

## Checks
- metric: source artifact
  - threshold: command consumes `decoder_attention_kv_endpoint_sram_noc_full_search_schedule__...llama7b_v1.json`
- metric: old source artifact
  - threshold: command does not consume `l2_decoder_attention_kv_sram_noc_constrained_schedule_llama7b_v1_r2.json`
- metric: policy sweep
  - threshold: report includes schedule policy, bank arbiter policy, endpoint queue depth, bank queue depth, packet payload, and router hop latency
- metric: HBM/DRAM
  - threshold: report states HBM/DRAM service is inherited unchanged

## Result
- status: pending
- note: Final quality decision waits for evaluator output.

