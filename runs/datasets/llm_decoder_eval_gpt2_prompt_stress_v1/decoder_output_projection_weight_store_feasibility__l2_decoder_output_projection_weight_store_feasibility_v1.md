# Decoder Output-Projection Weight-Store Feasibility

- model: `decoder_output_projection_weight_store_feasibility_v1`
- decision: `weight_store_area_budget_feasible`
- row_count: `240`
- area_budget_feasible_rows: `18`

## Shape Summary

| shape | cache_mb | target_bw_Bpc | best banks | read bits/cyc | proxy_area_mm2 | budget_ok | dominant |
|---|---:|---:|---:|---:|---:|---|---|
| gpt2_medium_proxy | 98.5 | 16384.0 | 50 | 204800 | 226.492416 | `True` | capacity |
| gpt2_small | 73.6875 | 16384.0 | 37 | 151552 | 167.604388 | `True` | capacity |

## Assumptions

- This is a banking and storage proxy, not a generated SRAM macro or routed memory subsystem.
- The proxy area is bitcell_area_um2_per_bit times stored bits plus peripheral overhead.
- Aggregate read bandwidth assumes banks can be read independently and combined by a distributed producer fabric.
- The aggregate_read_bits_per_cycle field is an interface-width pressure indicator, not necessarily one physical bus.
- Targets come from the best parallel producer memory-hierarchy rows after ranker calibration.
