# Quality Gate

## Proposal
- `proposal_id`: `prop_l2_decoder_attention_kv_endpoint_full_onchip_service_softmax_recip_lut_v1`
- `title`: `Endpoint full on-chip service for reciprocal-LUT softmax Llama7B frontier`

## Checks
- metric: source artifact
  - threshold: command consumes `decoder_attention_kv_endpoint_sram_noc_full_search_schedule__...softmax_recip_lut...v1_r2.json`
- metric: old source artifact
  - threshold: command does not consume `l2_decoder_attention_kv_endpoint_sram_noc_full_search_schedule_llama7b_v1.json`
- metric: policy sweep
  - threshold: report includes schedule policy, bank arbiter policy, endpoint queue depth, bank queue depth, packet payload, and router hop latency
- metric: HBM/DRAM
  - threshold: report states HBM/DRAM service is inherited unchanged

## Result
- status: pending
- note: Final quality decision waits for evaluator output.

