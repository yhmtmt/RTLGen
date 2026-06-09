# Quality Gate

## Proposal
- `proposal_id`: `prop_l2_decoder_attention_kv_endpoint_ready_valid_service_v1`
- `title`: `Endpoint ready-valid service probe for Llama7B frontier`

## Why This Gate Is Required
- The current Llama7B frontier now includes explicit endpoint queue and bank queue service policy, but it is still selected by an analytic scheduler.
- The next least-abstract on-chip check should confirm that the selected endpoint packet and queue sizing maps to finite ready/valid RTL behavior.

## Reference
- endpoint_onchip_ref: `l2_decoder_attention_kv_endpoint_full_onchip_service_schedule_llama7b_v1`

## Checks
- metric: source artifact
  - threshold: command consumes `decoder_attention_kv_endpoint_full_onchip_service_schedule__...llama7b_v1.json`
- metric: derived RTL parameters
  - threshold: report includes `DATA_W`, `BANKS`, `ENDPOINT_QUEUE_DEPTH`, and `BANK_QUEUE_DEPTH`
- metric: ready/valid behavior
  - threshold: accepted beats equal emitted beats, producer stalls are nonzero, consumer stalls are nonzero, and the probe passes
- metric: scope control
  - threshold: report states HBM/DRAM service is inherited unchanged

## Result
- status: pending
- note: Final quality decision waits for evaluator output.
