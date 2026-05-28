# Decoder Attention/KV Clustered Schedule

- model: `llm_decoder_attention_kv_clustered_schedule_llama7b_v1`
- generated_row_count: `2436804`
- skipped_area_budget_count: `406296`

## Best

| seq | die | SRAM | logic | arch | replicas | clusters | reduction | tile | clock ns | latency us | resource |
|---:|---:|---:|---:|---|---:|---:|---|---:|---:|---:|---|
| 131072 | 1200.0 | 0.4 | 0.2 | nm64_flat | 266 | 2 | owner_cluster | 1024 | 6.6331 | 14973.613005 | tile_attention |

## Best By Die And Cluster

| die | clusters | arch | replicas | reduction | tile waves | tile service | reduction cycles | latency us | resource |
|---:|---:|---|---:|---|---:|---:|---:|---:|---|
| 100.0 | 1 | nm64_flat | 22 | centralized_tile | 128 | 6517 | 3026 | 180865.639802 | tile_attention |
| 100.0 | 2 | nm64_flat | 22 | owner_cluster | 64 | 13034 | 3074 | 180875.828243 | tile_attention |
| 100.0 | 4 | nm64_flat | 22 | owner_cluster | 32 | 28674 | 3423 | 198650.62591 | tile_attention |
| 100.0 | 8 | nm64_flat | 22 | owner_cluster | 16 | 71680 | 4350 | 247520.971859 | tile_attention |
| 100.0 | 16 | nm64_flat | 22 | owner_cluster | 8 | 143360 | 4539 | 247561.088848 | tile_attention |
| 200.0 | 1 | nm64_flat | 44 | centralized_tile | 128 | 3260 | 1513 | 90473.785926 | tile_attention |
| 200.0 | 2 | nm64_flat | 44 | owner_cluster | 64 | 6517 | 1537 | 90438.126381 | tile_attention |
| 200.0 | 4 | nm64_flat | 44 | owner_cluster | 32 | 13034 | 1561 | 90443.220602 | tile_attention |
| 200.0 | 8 | nm64_flat | 44 | owner_cluster | 16 | 28674 | 1759 | 99335.607526 | tile_attention |
| 200.0 | 16 | nm64_flat | 44 | owner_cluster | 8 | 71680 | 2270 | 123780.862813 | tile_attention |
| 400.0 | 1 | nm64_flat | 88 | centralized_tile | 128 | 1630 | 757 | 45237.105222 | tile_attention |
| 400.0 | 2 | nm64_flat | 88 | owner_cluster | 64 | 3260 | 769 | 45239.652333 | tile_attention |
| 400.0 | 4 | nm64_flat | 88 | owner_cluster | 32 | 6517 | 781 | 45221.82256 | tile_attention |
| 400.0 | 8 | nm64_flat | 88 | owner_cluster | 16 | 13034 | 805 | 45226.916781 | tile_attention |
| 400.0 | 16 | nm64_flat | 88 | owner_cluster | 8 | 28674 | 927 | 49677.992205 | tile_attention |
| 800.0 | 1 | nm64_flat | 177 | centralized_tile | 128 | 812 | 377 | 22534.710227 | tile_attention |
| 800.0 | 2 | nm64_flat | 177 | owner_cluster | 64 | 1630 | 385 | 22617.915834 | tile_attention |
| 800.0 | 4 | nm64_flat | 177 | owner_cluster | 32 | 3260 | 391 | 22619.189389 | tile_attention |
| 800.0 | 8 | nm64_flat | 177 | owner_cluster | 16 | 6517 | 403 | 22611.548058 | tile_attention |
| 800.0 | 16 | nm64_flat | 177 | cluster_tree | 8 | 13034 | 427 | 22616.642278 | tile_attention |
| 1200.0 | 1 | nm64_flat | 266 | centralized_tile | 128 | 541 | 251 | 15013.517734 | tile_attention |
| 1200.0 | 2 | nm64_flat | 266 | owner_cluster | 64 | 1079 | 255 | 14973.613005 | tile_attention |
| 1200.0 | 4 | nm64_flat | 266 | owner_cluster | 32 | 2173 | 261 | 15076.770976 | tile_attention |
| 1200.0 | 8 | nm64_flat | 266 | cluster_tree | 16 | 4345 | 269 | 15075.072902 | tile_attention |
| 1200.0 | 16 | nm64_flat | 266 | cluster_tree | 8 | 8960 | 292 | 15538.434736 | tile_attention |

## Assumptions

- One decode-token attention pass is split into sequence KV tiles.
- Tiles are statically assigned to active clusters by wave; each active cluster handles at most one tile per wave.
- Each tile produces softmax statistics and a partial value vector for the current token.
- Reduction strategies model cross-tile combination after tile service: centralized_tile sends every tile partial, owner_cluster and cluster_tree first reduce tiles locally per cluster.
- This is an analytic schedule model; it still does not model RTL command queues or cycle-accurate SRAM/NoC arbitration.
