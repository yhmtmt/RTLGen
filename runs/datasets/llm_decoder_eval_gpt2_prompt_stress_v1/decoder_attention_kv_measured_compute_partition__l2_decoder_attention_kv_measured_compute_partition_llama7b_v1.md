# Decoder Attention/KV Measured Compute Partition

- model: `llm_decoder_attention_kv_measured_compute_partition_llama7b_v1`
- generated_row_count: `672408`
- skipped_area_budget_count: `212112`

## Best

| seq | die | SRAM | logic | arch | replicas | clusters | MAC/cyc | clock ns | latency us | resource |
|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|---|
| 131072 | 1200.0 | 0.4 | 0.2 | nm64_flat | 266 | 2 | 17024 | 6.6331 | 15748.146826 | tile_attention |

## Best By Die

| seq | die | SRAM | logic | arch | replicas | clusters | local share | shared share | hbm share | latency us | resource |
|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---|
| 131072 | 100.0 | 0.4 | 0.2 | nm64_flat | 22 | 2 | 0.004075 | 0.036671 | 0.959255 | 190330.27753 | tile_attention |
| 131072 | 200.0 | 0.4 | 0.2 | nm64_flat | 44 | 4 | 0.008149 | 0.073342 | 0.918509 | 95165.351024 | tile_attention |
| 131072 | 400.0 | 0.4 | 0.2 | nm64_flat | 88 | 8 | 0.016298 | 0.146683 | 0.837019 | 47582.781642 | tile_attention |
| 131072 | 800.0 | 0.4 | 0.2 | nm64_flat | 177 | 1 | 0.032596 | 0.293367 | 0.674037 | 23677.301501 | tile_attention |
| 131072 | 1200.0 | 0.4 | 0.2 | nm64_flat | 266 | 2 | 0.048894 | 0.44005 | 0.511056 | 15748.146826 | tile_attention |

## Best By Die And Cluster

| die | clusters | arch | replicas | per-cluster MAC/cyc | latency us | efficiency | resource |
|---:|---:|---|---:|---:|---:|---:|---|
| 100.0 | 1 | nm64_flat | 22 | 1408 | 190330.27753 | 1.0 | tile_attention |
| 100.0 | 2 | nm64_flat | 22 | 704 | 190330.27753 | 1.0 | tile_attention |
| 100.0 | 4 | nm64_flat | 22 | 320 | 209043.048602 | 1.0 | tile_attention |
| 100.0 | 8 | nm64_flat | 22 | 128 | 260508.26327 | 1.0 | tile_attention |
| 100.0 | 16 | nm64_flat | 22 | 64 | 260508.26327 | 1.0 | tile_attention |
| 100.0 | 32 | nm8_flat | 33 | 8 | 937759.874109 | 1.0 | tile_attention |
| 200.0 | 1 | nm64_flat | 44 | 2816 | 95178.935613 | 1.0 | tile_attention |
| 200.0 | 2 | nm64_flat | 44 | 1408 | 95165.351024 | 1.0 | tile_attention |
| 200.0 | 4 | nm64_flat | 44 | 704 | 95165.351024 | 1.0 | tile_attention |
| 200.0 | 8 | nm64_flat | 44 | 320 | 104521.73656 | 1.0 | tile_attention |
| 200.0 | 16 | nm64_flat | 44 | 128 | 130254.343894 | 1.0 | tile_attention |
| 200.0 | 32 | nm64_flat | 44 | 64 | 130254.343894 | 1.0 | tile_attention |
| 200.0 | 64 | nm8_flat | 66 | 8 | 468880.032179 | 1.0 | tile_attention |
| 400.0 | 1 | nm64_flat | 88 | 5632 | 47603.158525 | 1.0 | tile_attention |
| 400.0 | 2 | nm64_flat | 88 | 2816 | 47589.573936 | 1.0 | tile_attention |
| 400.0 | 4 | nm64_flat | 88 | 1408 | 47582.781642 | 1.0 | tile_attention |
| 400.0 | 8 | nm64_flat | 88 | 704 | 47582.781642 | 1.0 | tile_attention |
| 400.0 | 16 | nm64_flat | 88 | 320 | 52260.97441 | 1.0 | tile_attention |
| 400.0 | 32 | nm64_flat | 88 | 128 | 65127.278077 | 1.0 | tile_attention |
| 400.0 | 64 | nm64_flat | 88 | 64 | 65127.278077 | 1.0 | tile_attention |
| 800.0 | 1 | nm64_flat | 177 | 11328 | 23677.301501 | 1.0 | tile_attention |
| 800.0 | 2 | nm64_flat | 177 | 5632 | 23799.5628 | 1.0 | tile_attention |
| 800.0 | 4 | nm64_flat | 177 | 2816 | 23792.770506 | 1.0 | tile_attention |
| 800.0 | 8 | nm64_flat | 177 | 1408 | 23789.374358 | 1.0 | tile_attention |
| 800.0 | 16 | nm64_flat | 177 | 704 | 23789.374358 | 1.0 | tile_attention |
| 800.0 | 32 | nm64_flat | 177 | 320 | 26128.470742 | 1.0 | tile_attention |
| 800.0 | 64 | nm64_flat | 177 | 128 | 32561.622576 | 1.0 | tile_attention |
| 1200.0 | 1 | nm64_flat | 266 | 17024 | 15748.146826 | 1.0 | tile_attention |
| 1200.0 | 2 | nm64_flat | 266 | 8512 | 15748.146826 | 1.0 | tile_attention |
| 1200.0 | 4 | nm64_flat | 266 | 4224 | 15863.61583 | 1.0 | tile_attention |
| 1200.0 | 8 | nm64_flat | 266 | 2112 | 15860.219683 | 1.0 | tile_attention |
| 1200.0 | 16 | nm64_flat | 266 | 1024 | 16345.868733 | 1.0 | tile_attention |
| 1200.0 | 32 | nm64_flat | 266 | 512 | 16345.868733 | 1.0 | tile_attention |
| 1200.0 | 64 | nm64_flat | 266 | 256 | 16345.868733 | 1.0 | tile_attention |

## Assumptions

- Compute blocks use merged corrected NPU PPA rows and are replicated within the logic area budget.
- cluster_count is a planning partition count; replicas are statically assigned to clusters by floor/ceil division.
- Attention tiles are sequence-sharded across active clusters; qkv projection uses aggregate compute throughput.
- Local SRAM is modeled as sequence-sharded resident KV storage; shared SRAM and HBM bandwidth are contended across active clusters.
- NoC bandwidth is divided across active clusters and penalized by hop count plus router latency.
- This is a scheduling/service model, not cycle-accurate NoC arbitration or SRAM macro floorplanning.
