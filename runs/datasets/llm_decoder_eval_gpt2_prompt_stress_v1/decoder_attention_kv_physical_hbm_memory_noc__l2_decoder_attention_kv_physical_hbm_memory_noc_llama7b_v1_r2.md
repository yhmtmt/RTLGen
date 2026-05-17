# Decoder Attention/KV Physical HBM Frontier

- model: `llm_decoder_attention_kv_physical_hbm_frontier_llama7b_v1`
- generated_row_count: `92160`
- selected_point: `llama7b_proxy seq=131072 die=800.0mm2`

## Best

| seq | die | kv | bits | stacks | pch/stack | width | MT/s | eff | hbm_B/cyc | hbm_share | latency_us | resource |
|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 131072 | 800.0 | gqa8 | 8 | 8 | 16 | 64 | 9000 | 0.75 | 6912.0 | 0.541615 | 86.112 | hbm |

## Best By Sequence And Die

| seq | die | kv | bits | stacks | MT/s | SRAM MiB | local_frac | NoC B/cyc | hops | hbm_share | latency_us | resource |
|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 131072 | 100.0 | gqa8 | 8 | 8 | 9000 | 379.97961 | 0.1 | 8192.0 | 1 | 0.916508 | 133.152 | hbm |
| 131072 | 200.0 | gqa8 | 8 | 8 | 9000 | 759.959221 | 0.1 | 8192.0 | 1 | 0.833017 | 122.72 | hbm |
| 131072 | 400.0 | gqa8 | 8 | 8 | 9000 | 1519.918442 | 0.1 | 32768.0 | 1 | 0.666034 | 101.536 | hbm |
| 131072 | 800.0 | gqa8 | 8 | 8 | 9000 | 2503.395081 | 0.25 | 32768.0 | 1 | 0.541615 | 86.112 | hbm |
| 131072 | 1200.0 | gqa8 | 8 | 8 | 9000 | 3755.092621 | 0.5 | 32768.0 | 1 | 0.541615 | 86.112 | hbm |

## Top 10

| rank | seq | die | kv | bits | stacks | pch/stack | MT/s | hbm_B/cyc | hbm_share | latency_us | resource |
|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | 131072 | 800.0 | gqa8 | 8 | 8 | 16 | 9000 | 6912.0 | 0.541615 | 86.112 | hbm |
| 2 | 131072 | 800.0 | gqa8 | 8 | 8 | 16 | 9000 | 6912.0 | 0.541615 | 86.112 | hbm |
| 3 | 131072 | 800.0 | gqa8 | 8 | 8 | 16 | 9000 | 6912.0 | 0.541615 | 86.112 | hbm |
| 4 | 131072 | 800.0 | gqa8 | 8 | 8 | 16 | 9000 | 6912.0 | 0.541615 | 86.112 | hbm |
| 5 | 131072 | 800.0 | gqa8 | 8 | 8 | 16 | 9000 | 6912.0 | 0.541615 | 86.112 | hbm |
| 6 | 131072 | 800.0 | gqa8 | 8 | 8 | 16 | 9000 | 6912.0 | 0.541615 | 86.112 | hbm |
| 7 | 131072 | 1200.0 | gqa8 | 8 | 8 | 16 | 9000 | 6912.0 | 0.541615 | 86.112 | hbm |
| 8 | 131072 | 1200.0 | gqa8 | 8 | 8 | 16 | 9000 | 6912.0 | 0.541615 | 86.112 | hbm |
| 9 | 131072 | 1200.0 | gqa8 | 8 | 8 | 16 | 9000 | 6912.0 | 0.541615 | 86.112 | hbm |
| 10 | 131072 | 1200.0 | gqa8 | 8 | 8 | 16 | 9000 | 6912.0 | 0.541615 | 86.112 | hbm |

## Assumptions

- This is a planning model for single-token decode attention/KV, not a JEDEC HBM timing model.
- HBM bandwidth is derived from stack count, pseudo-channel count, interface width, MT/s, and the core clock period.
- HBM efficiency represents controller scheduling, protocol overhead, row locality, and clock-crossing loss in aggregate.
- KV bits are treated as packed storage bits, so kv4 has half the byte traffic of kv8.
- Shared SRAM residency is capacity-based; the remaining KV-cache traffic spills to HBM.
- The tile scheduler is a compact service model intended to rank architecture directions before RTL.
