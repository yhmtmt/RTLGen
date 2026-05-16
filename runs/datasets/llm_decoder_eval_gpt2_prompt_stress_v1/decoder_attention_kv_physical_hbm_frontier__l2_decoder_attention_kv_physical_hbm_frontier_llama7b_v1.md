# Decoder Attention/KV Physical HBM Frontier

- model: `llm_decoder_attention_kv_physical_hbm_frontier_llama7b_v1`
- generated_row_count: `31104`
- selected_point: `llama7b_proxy seq=32768 die=100.0mm2`

## Best

| seq | die | kv | bits | stacks | pch/stack | width | MT/s | eff | hbm_B/cyc | hbm_share | latency_us | resource |
|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 32768 | 100.0 | mqa | 4 | 1 | 8 | 64 | 3200 | 0.35 | 71.68 | 0.0 | 20.96 | tile_attention |

## Best By Sequence And Die

| seq | die | kv | bits | stacks | MT/s | hbm_share | latency_us | resource |
|---:|---:|---|---:|---:|---:|---:|---:|---|
| 32768 | 100.0 | mqa | 4 | 1 | 3200 | 0.0 | 20.96 | tile_attention |
| 32768 | 200.0 | mqa | 4 | 1 | 3200 | 0.0 | 20.96 | tile_attention |
| 32768 | 400.0 | mqa | 4 | 1 | 3200 | 0.0 | 20.96 | tile_attention |
| 65536 | 100.0 | mqa | 8 | 8 | 6400 | 0.633292 | 40.32 | hbm |
| 65536 | 200.0 | mqa | 4 | 1 | 3200 | 0.0 | 40.416 | tile_attention |
| 65536 | 400.0 | mqa | 4 | 1 | 3200 | 0.0 | 40.416 | tile_attention |
| 131072 | 100.0 | mqa | 8 | 8 | 9000 | 0.816646 | 79.136 | hbm |
| 131072 | 200.0 | mqa | 8 | 8 | 6400 | 0.633292 | 79.232 | hbm |
| 131072 | 400.0 | mqa | 4 | 1 | 3200 | 0.0 | 79.328 | tile_attention |

## Top 10

| rank | seq | die | kv | bits | stacks | pch/stack | MT/s | hbm_B/cyc | hbm_share | latency_us | resource |
|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | 32768 | 100.0 | mqa | 4 | 1 | 8 | 3200 | 71.68 | 0.0 | 20.96 | tile_attention |
| 2 | 32768 | 100.0 | mqa | 4 | 1 | 8 | 3200 | 71.68 | 0.0 | 20.96 | tile_attention |
| 3 | 32768 | 100.0 | mqa | 4 | 1 | 8 | 3200 | 112.64 | 0.0 | 20.96 | tile_attention |
| 4 | 32768 | 100.0 | mqa | 4 | 1 | 8 | 3200 | 112.64 | 0.0 | 20.96 | tile_attention |
| 5 | 32768 | 100.0 | mqa | 4 | 1 | 8 | 3200 | 153.6 | 0.0 | 20.96 | tile_attention |
| 6 | 32768 | 100.0 | mqa | 4 | 1 | 8 | 3200 | 153.6 | 0.0 | 20.96 | tile_attention |
| 7 | 32768 | 100.0 | mqa | 4 | 1 | 8 | 6400 | 143.36 | 0.0 | 20.96 | tile_attention |
| 8 | 32768 | 100.0 | mqa | 4 | 1 | 8 | 6400 | 143.36 | 0.0 | 20.96 | tile_attention |
| 9 | 32768 | 100.0 | mqa | 4 | 1 | 8 | 6400 | 225.28 | 0.0 | 20.96 | tile_attention |
| 10 | 32768 | 100.0 | mqa | 4 | 1 | 8 | 6400 | 225.28 | 0.0 | 20.96 | tile_attention |

## Assumptions

- This is a planning model for single-token decode attention/KV, not a JEDEC HBM timing model.
- HBM bandwidth is derived from stack count, pseudo-channel count, interface width, MT/s, and the core clock period.
- HBM efficiency represents controller scheduling, protocol overhead, row locality, and clock-crossing loss in aggregate.
- KV bits are treated as packed storage bits, so kv4 has half the byte traffic of kv8.
- Shared SRAM residency is capacity-based; the remaining KV-cache traffic spills to HBM.
- The tile scheduler is a compact service model intended to rank architecture directions before RTL.
