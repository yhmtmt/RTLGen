# Quality Gate

## Proposal
- `proposal_id`: `prop_l2_decoder_attention_kv_endpoint_sram_noc_full_search_schedule_v1`
- `title`: `Endpoint SRAM/NoC full-search Llama7B attention schedule`

## Why This Gate Is Required
- Retained-frontier postprocessing can miss architecture points that become better only after practical SRAM/endpoint caps are applied.
- The Llama7B frontier should be selected from a cap-aware search before we decide whether SRAM endpoint service changes the best topology.

## Reference
- endpoint_topology_pairs_ref: `l2_decoder_attention_kv_dense_tile_endpoint_topology_scheduler_pairs_llama7b_v1`
- sram_profile_ref: `l2_decoder_attention_sram_profile_v1`
- retained_cap_ref: `l2_decoder_attention_kv_endpoint_sram_noc_constrained_schedule_llama7b_v1`

## Checks
- metric: source mode
  - threshold: report records `full_topology_regeneration`
- metric: generated rows
  - threshold: nonzero successful output
- metric: cap-source accounting
  - threshold: report includes practical NoC cap-source counts
- metric: endpoint topology input
  - threshold: command consumes the endpoint topology/scheduler pair matrix
- metric: retained topology input
  - threshold: command does not consume `--topology-derived-json`
- metric: abstract NoC knobs
  - threshold: generated task command must not include independent `--noc-bandwidth-bytes-per-cycle` or `--noc-hops`

## Result
- status: pending
- note: Final quality decision waits for evaluator output.

