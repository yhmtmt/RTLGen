# Decoder Output-Projection Weight-Fetch Wrapper Contract

- model: `decoder_output_projection_weight_fetch_wrapper_contract_v1`
- decision: `weight_fetch_wrapper_contract_passed`
- scenario_count: `30`
- passed_count: `30`
- stall_scenario_count: `10`

## Scenarios

| label | banks | latency | issue interval | depth | stalls | final cycle | passed |
|---|---:|---:|---:|---:|---:|---:|---|
| gpt2_medium_proxy | 50 | 1 | 1 | 1 | 11 | 25 | `True` |
| gpt2_medium_proxy | 50 | 1 | 21 | 1 | 0 | 234 | `True` |
| gpt2_medium_proxy | 50 | 1 | 29 | 1 | 0 | 322 | `True` |
| gpt2_medium_proxy | 50 | 1 | 1 | 4 | 0 | 14 | `True` |
| gpt2_medium_proxy | 50 | 1 | 21 | 4 | 0 | 234 | `True` |
| gpt2_medium_proxy | 50 | 1 | 29 | 4 | 0 | 322 | `True` |
| gpt2_medium_proxy | 50 | 4 | 1 | 1 | 44 | 61 | `True` |
| gpt2_medium_proxy | 50 | 4 | 21 | 1 | 0 | 237 | `True` |
| gpt2_medium_proxy | 50 | 4 | 29 | 1 | 0 | 325 | `True` |
| gpt2_medium_proxy | 50 | 4 | 1 | 4 | 2 | 19 | `True` |
| gpt2_medium_proxy | 50 | 4 | 21 | 4 | 0 | 237 | `True` |
| gpt2_medium_proxy | 50 | 4 | 29 | 4 | 0 | 325 | `True` |
| gpt2_medium_proxy | 50 | 8 | 1 | 1 | 88 | 109 | `True` |
| gpt2_medium_proxy | 50 | 8 | 21 | 1 | 0 | 241 | `True` |
| gpt2_medium_proxy | 50 | 8 | 29 | 1 | 0 | 329 | `True` |
| gpt2_medium_proxy | 50 | 8 | 1 | 4 | 10 | 31 | `True` |
| gpt2_medium_proxy | 50 | 8 | 21 | 4 | 0 | 241 | `True` |
| gpt2_medium_proxy | 50 | 8 | 29 | 4 | 0 | 329 | `True` |
| gpt2_small | 37 | 1 | 1 | 1 | 11 | 25 | `True` |
| gpt2_small | 37 | 1 | 11 | 1 | 0 | 124 | `True` |
| gpt2_small | 37 | 1 | 1 | 4 | 0 | 14 | `True` |
| gpt2_small | 37 | 1 | 11 | 4 | 0 | 124 | `True` |
| gpt2_small | 37 | 4 | 1 | 1 | 44 | 61 | `True` |
| gpt2_small | 37 | 4 | 11 | 1 | 0 | 127 | `True` |
| gpt2_small | 37 | 4 | 1 | 4 | 2 | 19 | `True` |
| gpt2_small | 37 | 4 | 11 | 4 | 0 | 127 | `True` |
| gpt2_small | 37 | 8 | 1 | 1 | 88 | 109 | `True` |
| gpt2_small | 37 | 8 | 11 | 1 | 0 | 131 | `True` |
| gpt2_small | 37 | 8 | 1 | 4 | 10 | 31 | `True` |
| gpt2_small | 37 | 8 | 11 | 4 | 0 | 131 | `True` |

## Assumptions

- This is a control-contract RTL simulation, not an SRAM macro or full output-projection datapath.
- The model uses full selected bank counts from the feasibility artifact but deterministic generated data instead of resident weight arrays.
- Scenarios include both throughput stress and selected producer cadence from the feasibility rows.
