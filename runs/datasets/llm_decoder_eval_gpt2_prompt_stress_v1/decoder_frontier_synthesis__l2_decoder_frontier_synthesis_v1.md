# Decoder Frontier Synthesis

- model: `llm_decoder_frontier_synthesis_v1`

## Focus Summary

| shape | seq | dominant | share | attention_us | mlp_us | producer_ranker_us | attention choice | producer choice |
|---|---:|---|---:|---:|---:|---:|---|---|
| gpt2_medium_proxy | 128 | output_projection_producer_ranker | 0.998767 | 1.392 | 6.144 | 6728.322951 | local_sram/mqa/kv8/hops0 | w64/k1/share1.0/ii512 |
| gpt2_small | 128 | output_projection_producer_ranker | 0.999491 | 0.552 | 1.728 | 5046.275694 | local_sram/mqa/kv8/hops0 | w64/k1/share1.0/ii384 |

## Measured Attention/KV Tile Summary

- area_growth_largest_vs_smallest: `23.809901`
- fastest_critical_path_ns: `4.4824`
- fastest_design: `attention_kv_tile_hd64_kv4_l16_b128_wrapper`
- largest_design: `attention_kv_tile_hd128_kv16_l64_b512_wrapper`
- largest_die_area_um2: `269044.503025`
- smallest_design: `attention_kv_tile_hd64_kv4_l16_b128_wrapper`
- smallest_die_area_um2: `11299.69`

## Assumptions

- This is a synthesis of existing analytical reports, not a new RTL measurement.
- Attention/KV uses the best latency row per shape and sequence from the calibrated attention/KV report.
- Producer/ranker uses the best FIFO-valid coupled row per hidden/vocab shape.
- MLP and norm are resident-weight estimates from the whole-decoder stage breakdown.
- Use this report to choose the next measured RTL frontier, not as final PPA accounting.
