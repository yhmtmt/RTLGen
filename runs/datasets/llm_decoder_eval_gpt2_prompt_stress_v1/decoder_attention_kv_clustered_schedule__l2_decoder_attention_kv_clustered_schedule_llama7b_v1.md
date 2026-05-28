# Decoder Attention/KV Clustered Schedule

- model: `llm_decoder_attention_kv_clustered_schedule_llama7b_v1`
- generated_row_count: `2436804`
- skipped_area_budget_count: `406296`

## Best

| seq | die | SRAM | logic | arch | replicas | clusters | reduction | tile | clock ns | latency us | resource |
|---:|---:|---:|---:|---|---:|---:|---|---:|---:|---:|---|
| 131072 | 1200.0 | 0.4 | 0.2 | nm64_flat | 266 | 2 | centralized_tile | 1024 | 6.6331 | 14921.609501 | tile_attention |

## Best By Die And Cluster

| die | clusters | arch | replicas | reduction | tile waves | tile service | reduction cycles | latency us | resource |
|---:|---:|---|---:|---|---:|---:|---:|---:|---|
| 100.0 | 1 | nm64_flat | 22 | centralized_tile | 128 | 6517 | 24 | 180228.437683 | tile_attention |
| 100.0 | 2 | nm64_flat | 22 | centralized_tile | 128 | 6517 | 48 | 180233.531904 | tile_attention |
| 100.0 | 4 | nm64_flat | 22 | centralized_tile | 64 | 14337 | 95 | 197944.227293 | tile_attention |
| 100.0 | 8 | nm64_flat | 22 | centralized_tile | 64 | 17920 | 190 | 246637.973587 | tile_attention |
| 100.0 | 16 | nm64_flat | 22 | centralized_tile | 32 | 35840 | 379 | 246678.090576 | tile_attention |
| 200.0 | 1 | nm64_flat | 44 | centralized_tile | 128 | 3260 | 12 | 90155.184867 | tile_attention |
| 200.0 | 2 | nm64_flat | 44 | centralized_tile | 64 | 6517 | 24 | 90116.978211 | tile_attention |
| 200.0 | 4 | nm64_flat | 44 | centralized_tile | 64 | 6517 | 48 | 90122.072432 | tile_attention |
| 200.0 | 8 | nm64_flat | 44 | centralized_tile | 32 | 14337 | 95 | 98982.408218 | tile_attention |
| 200.0 | 16 | nm64_flat | 44 | centralized_tile | 32 | 17920 | 190 | 123339.363677 | tile_attention |
| 400.0 | 1 | nm64_flat | 88 | centralized_tile | 128 | 1630 | 10 | 45078.5476 | tile_attention |
| 400.0 | 2 | nm64_flat | 88 | centralized_tile | 64 | 3260 | 12 | 45078.972118 | tile_attention |
| 400.0 | 4 | nm64_flat | 88 | centralized_tile | 32 | 6517 | 24 | 45061.142346 | tile_attention |
| 400.0 | 8 | nm64_flat | 88 | centralized_tile | 32 | 6517 | 48 | 45066.236566 | tile_attention |
| 400.0 | 16 | nm64_flat | 88 | centralized_tile | 16 | 14337 | 95 | 49501.39255 | tile_attention |
| 800.0 | 1 | nm64_flat | 177 | centralized_tile | 128 | 812 | 10 | 22456.811101 | tile_attention |
| 800.0 | 2 | nm64_flat | 177 | centralized_tile | 64 | 1630 | 10 | 22538.318634 | tile_attention |
| 800.0 | 4 | nm64_flat | 177 | centralized_tile | 32 | 3260 | 12 | 22538.743152 | tile_attention |
| 800.0 | 8 | nm64_flat | 177 | centralized_tile | 16 | 6517 | 24 | 22531.101821 | tile_attention |
| 800.0 | 16 | nm64_flat | 177 | centralized_tile | 16 | 6517 | 48 | 22536.196042 | tile_attention |
| 1200.0 | 1 | nm64_flat | 266 | centralized_tile | 128 | 541 | 10 | 14962.363267 | tile_attention |
| 1200.0 | 2 | nm64_flat | 266 | centralized_tile | 64 | 1079 | 10 | 14921.609501 | tile_attention |
| 1200.0 | 4 | nm64_flat | 266 | centralized_tile | 32 | 2173 | 10 | 15023.493917 | tile_attention |
| 1200.0 | 8 | nm64_flat | 266 | centralized_tile | 16 | 4345 | 16 | 15021.371325 | tile_attention |
| 1200.0 | 16 | nm64_flat | 266 | centralized_tile | 16 | 4480 | 32 | 15483.247344 | tile_attention |

## Assumptions

- One decode-token attention pass is split into sequence KV tiles.
- Tiles are statically assigned to active clusters by wave; each active cluster handles at most one tile per wave.
- Each tile produces softmax statistics and a partial value vector for the current token.
- Reduction strategies model cross-tile combination after tile service: centralized_tile sends every tile partial, owner_cluster and cluster_tree first reduce tiles locally per cluster.
- This is an analytic schedule model; it still does not model RTL command queues or cycle-accurate SRAM/NoC arbitration.
