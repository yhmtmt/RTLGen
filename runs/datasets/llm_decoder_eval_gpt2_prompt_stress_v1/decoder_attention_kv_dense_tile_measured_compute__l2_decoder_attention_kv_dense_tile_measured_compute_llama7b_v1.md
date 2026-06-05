# Decoder Attention/KV Measured Compute Substitution

- model: `llm_decoder_attention_kv_measured_compute_llama7b_v1`
- generated_row_count: `6480`
- skipped_area_budget_count: `4320`

## Best

| seq | die | SRAM frac | logic frac | arch | replicas | MAC/cyc | clock ns | compute area um2 | compute mW | latency us | resource |
|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---|
| 131072 | 1200.0 | 0.4 | 0.4 | dense_gemm_16x8_k1_p1 | 1035 | 132480 | 5.9811 | 479592090.0 | 9832.5 | 1844.858333 | tile_attention |

## Best By Die

| seq | die | SRAM frac | logic frac | arch | replicas | MAC/cyc | hbm share | latency us | resource |
|---:|---:|---:|---:|---|---:|---:|---:|---:|---|
| 131072 | 100.0 | 0.4 | 0.4 | dense_gemm_16x8_k1_p1 | 86 | 11008 | 0.979627 | 21997.815917 | tile_attention |
| 131072 | 200.0 | 0.4 | 0.4 | dense_gemm_16x8_k1_p1 | 172 | 22016 | 0.959255 | 11011.540042 | tile_attention |
| 131072 | 400.0 | 0.4 | 0.4 | dense_gemm_16x8_k1_p1 | 345 | 44160 | 0.918509 | 5481.558528 | tile_attention |
| 131072 | 800.0 | 0.4 | 0.4 | dense_gemm_16x8_k1_p1 | 690 | 88320 | 0.837019 | 2742.310426 | tile_attention |
| 131072 | 1200.0 | 0.4 | 0.4 | dense_gemm_16x8_k1_p1 | 1035 | 132480 | 0.755528 | 1844.858333 | tile_attention |

## Top 10

| rank | die | SRAM frac | logic frac | arch | replicas | MAC/cyc | vec/cyc | clock ns | latency us | resource |
|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|---|
| 1 | 1200.0 | 0.4 | 0.4 | dense_gemm_16x8_k1_p1 | 1035 | 132480 | 16560 | 5.9811 | 1844.858333 | tile_attention |
| 2 | 1200.0 | 0.4 | 0.4 | dense_gemm_16x8_k1_p1 | 1035 | 132480 | 16560 | 5.9811 | 1844.858333 | tile_attention |
| 3 | 1200.0 | 0.4 | 0.4 | dense_gemm_16x8_k1_p1 | 1035 | 132480 | 16560 | 5.9811 | 1845.049728 | tile_attention |
| 4 | 1200.0 | 0.4 | 0.4 | dense_gemm_16x8_k1_p1 | 1035 | 132480 | 16560 | 5.9811 | 1845.049728 | tile_attention |
| 5 | 1200.0 | 0.4 | 0.4 | dense_gemm_16x8_k1_p1 | 1035 | 132480 | 16560 | 5.9811 | 1845.241123 | tile_attention |
| 6 | 1200.0 | 0.4 | 0.4 | dense_gemm_16x8_k1_p1 | 1035 | 132480 | 16560 | 5.9811 | 1845.241123 | tile_attention |
| 7 | 1200.0 | 0.4 | 0.4 | dense_gemm_16x8_k1_p1 | 1035 | 132480 | 16560 | 5.9811 | 1845.623914 | tile_attention |
| 8 | 1200.0 | 0.4 | 0.4 | dense_gemm_16x8_k1_p1 | 1035 | 132480 | 16560 | 5.9811 | 1845.623914 | tile_attention |
| 9 | 1200.0 | 0.4 | 0.4 | dense_gemm_16x8_k1_p1 | 1035 | 132480 | 16560 | 5.9811 | 1845.623914 | tile_attention |
| 10 | 1200.0 | 0.4 | 0.4 | dense_gemm_16x8_k1_p1 | 1035 | 132480 | 16560 | 5.9811 | 1845.623914 | tile_attention |

## Assumptions

- Compute throughput is derived from merged compute PPA: replica_count * measured block MACs/cycle.
- Block clock period is the measured critical path for the selected PPA row; HBM service remains derived from physical MT/s.
- Only quality-backed native-GQA KV8 is ranked here; KV4/MQA remain excluded from deployable candidates.
- Compute area is constrained by an explicit die-area fraction after SRAM and reserved non-SRAM/non-compute area.
- Vector throughput is not separately measured for the attention softmax path; it is tied to MAC throughput by vector_ops_per_mac.
- This remains a planning model, not a detailed NoC arbitration or SRAM macro floorplan.
