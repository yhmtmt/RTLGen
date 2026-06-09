# Quality Gate

## Proposal
- `proposal_id`: `prop_l2_decoder_attention_kv_endpoint_sram_noc_constrained_schedule_v1`
- `title`: `Endpoint SRAM/NoC constrained Llama7B attention schedule`

## Why This Gate Is Required
- The endpoint topology-derived schedule still has optimistic SRAM-bank service.
- The Llama7B frontier should be interpreted with practical endpoint and SRAM-bank caps before selecting a detailed on-chip service model.

## Reference
- endpoint_topology_derived_ref: `l2_decoder_attention_kv_dense_tile_endpoint_topology_derived_schedule_llama7b_v1_r3`
- sram_profile_ref: `l2_decoder_attention_sram_profile_v1`

## Checks
- metric: generated rows
  - threshold: nonzero successful output
- metric: cap-source accounting
  - threshold: report includes practical NoC cap-source counts
- metric: endpoint topology input
  - threshold: command consumes `decoder_attention_kv_dense_tile_endpoint_topology_derived_schedule__...r3.json`
- metric: abstract NoC knobs
  - threshold: generated task command must not include independent `--noc-bandwidth-bytes-per-cycle` or `--noc-hops`
- metric: frontier comparison
  - threshold: report includes slowdown versus the endpoint topology-derived schedule

## Result
- status: pending
- note: Final quality decision waits for evaluator output.
