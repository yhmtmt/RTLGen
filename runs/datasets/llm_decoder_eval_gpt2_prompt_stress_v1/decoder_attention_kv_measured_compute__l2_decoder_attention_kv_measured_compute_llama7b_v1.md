# Decoder Attention/KV Measured Compute Substitution

- model: `llm_decoder_attention_kv_measured_compute_llama7b_v1`
- generated_row_count: `12480`
- skipped_area_budget_count: `1560`

## Best

| seq | die | SRAM frac | logic frac | arch | replicas | MAC/cyc | clock ns | compute area um2 | compute mW | latency us | resource |
|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---|
| 131072 | 1200.0 | 0.4 | 0.2 | nm64_flat | 266 | 17024 | 6.6331 | 239965250.0 | 1002.82 | 15750.693936 | tile_attention |

## Best By Die

| seq | die | SRAM frac | logic frac | arch | replicas | MAC/cyc | hbm share | latency us | resource |
|---:|---:|---:|---:|---|---:|---:|---:|---:|---|
| 131072 | 100.0 | 0.4 | 0.2 | nm64_flat | 22 | 1408 | 0.979627 | 190330.914307 | tile_attention |
| 131072 | 200.0 | 0.4 | 0.2 | nm64_flat | 44 | 2816 | 0.959255 | 95179.78465 | tile_attention |
| 131072 | 400.0 | 0.4 | 0.2 | nm64_flat | 88 | 5632 | 0.918509 | 47604.43208 | tile_attention |
| 131072 | 800.0 | 0.4 | 0.2 | nm64_flat | 177 | 11328 | 0.837019 | 23679.211834 | tile_attention |
| 131072 | 1200.0 | 0.4 | 0.2 | nm64_flat | 266 | 17024 | 0.755528 | 15750.693936 | tile_attention |

## Top 10

| rank | die | SRAM frac | logic frac | arch | replicas | MAC/cyc | vec/cyc | clock ns | latency us | resource |
|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|---|
| 1 | 1200.0 | 0.4 | 0.2 | nm64_flat | 266 | 17024 | 2128 | 6.6331 | 15750.693936 | tile_attention |
| 2 | 1200.0 | 0.4 | 0.2 | nm64_flat | 266 | 17024 | 2128 | 6.6331 | 15750.693936 | tile_attention |
| 3 | 1200.0 | 0.4 | 0.2 | nm64_flat | 266 | 17024 | 2128 | 6.6331 | 15751.118454 | tile_attention |
| 4 | 1200.0 | 0.4 | 0.2 | nm64_flat | 266 | 17024 | 2128 | 6.6331 | 15751.118454 | tile_attention |
| 5 | 1200.0 | 0.4 | 0.2 | nm64_flat | 266 | 17024 | 2128 | 6.6331 | 15751.542973 | tile_attention |
| 6 | 1200.0 | 0.4 | 0.2 | nm64_flat | 266 | 17024 | 2128 | 6.6331 | 15751.542973 | tile_attention |
| 7 | 1200.0 | 0.6 | 0.2 | nm64_flat | 266 | 17024 | 2128 | 6.6331 | 15751.542973 | tile_attention |
| 8 | 1200.0 | 0.6 | 0.2 | nm64_flat | 266 | 17024 | 2128 | 6.6331 | 15751.542973 | tile_attention |
| 9 | 1200.0 | 0.4 | 0.2 | nm64_flat | 266 | 17024 | 2128 | 6.6331 | 15752.17975 | tile_attention |
| 10 | 1200.0 | 0.4 | 0.2 | nm64_flat | 266 | 17024 | 2128 | 6.6331 | 15752.17975 | tile_attention |

## Assumptions

- Compute throughput is derived from merged NPU block PPA: replica_count * measured block num_modules.
- Block clock period is the measured critical path for the selected PPA row; HBM service remains derived from physical MT/s.
- Only quality-backed native-GQA KV8 is ranked here; KV4/MQA remain excluded from deployable candidates.
- Compute area is constrained by an explicit die-area fraction after SRAM and reserved non-SRAM/non-compute area.
- Vector throughput is not separately measured for the attention softmax path; it is tied to MAC throughput by vector_ops_per_mac.
- This remains a planning model, not a detailed NoC arbitration or SRAM macro floorplan.
