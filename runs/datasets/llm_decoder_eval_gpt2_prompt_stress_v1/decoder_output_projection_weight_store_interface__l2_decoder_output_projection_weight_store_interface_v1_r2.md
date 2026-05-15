# Decoder Output-Projection Weight-Store Interface Contract

- model: `decoder_output_projection_weight_store_interface_contract_v1`
- source_feasibility_decision: `weight_store_area_budget_feasible`
- decision: `weight_store_interface_contract_passed`
- scenario_count: `8`
- passed_count: `8`

## Scenarios

| label | full banks | probe banks | read bits | latency | passed | checksum |
|---|---:|---:|---:|---:|---|---:|
| gpt2_medium_proxy | 50 | 50 | 2048 | 1 | `True` | 4335200 |
| gpt2_medium_proxy | 50 | 50 | 2048 | 2 | `True` | 4335200 |
| gpt2_medium_proxy | 50 | 50 | 2048 | 4 | `True` | 4335200 |
| gpt2_medium_proxy | 50 | 50 | 2048 | 8 | `True` | 4335200 |
| gpt2_small | 37 | 37 | 2048 | 1 | `True` | 3142632 |
| gpt2_small | 37 | 37 | 2048 | 2 | `True` | 3142632 |
| gpt2_small | 37 | 37 | 2048 | 4 | `True` | 3142632 |
| gpt2_small | 37 | 37 | 2048 | 8 | `True` | 3142632 |

## Assumptions

- The RTL probe scales the number of banks down to a bounded representative count; full resident capacity and area remain from the feasibility artifact.
- The probe models independent sharded bank reads and deterministic response ordering, not SRAM bitcell layout.
- Python perf reference and RTL simulation must agree on accepted requests, response count, and data checksum.
