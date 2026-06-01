# Decoder Attention/KV Clustered Schedule

- model: `llm_decoder_attention_kv_clustered_schedule_llama7b_v1`
- generated_row_count: `2396160`
- skipped_area_budget_count: `0`

## Best

| seq | die | SRAM | logic | L1 profile | arch | replicas | clusters | reduction | tile | clock ns | latency us | resource |
|---:|---:|---:|---:|---|---|---:|---:|---|---:|---:|---:|---|
| 131072 | 1200.0 | 0.4 | 0.2 | hd64_kv8_full_value_p8_ppc2_noc128 | nm64_flat | 264 | 8 | cluster_tree | 512 | 6.6331 | 15134.08096 | tile_attention |

## Best By Overhead

| die | cmd/tile | cmd/wave | reducer setup | reduction x | clusters | reduction | latency us | resource |
|---:|---:|---:|---:|---:|---:|---|---:|---|
| 200.0 | 0 | 0 | 0 | 1.0 | 1 | owner_cluster | 90797.481206 | cross_tile_reduction |
| 200.0 | 0 | 0 | 0 | 2.0 | 1 | owner_cluster | 91442.324656 | cross_tile_reduction |
| 200.0 | 0 | 0 | 64 | 1.0 | 1 | owner_cluster | 90811.065795 | cross_tile_reduction |
| 200.0 | 0 | 0 | 64 | 2.0 | 1 | owner_cluster | 91455.909245 | cross_tile_reduction |
| 200.0 | 0 | 16 | 0 | 1.0 | 1 | owner_cluster | 91666.89489 | command_dispatch |
| 200.0 | 0 | 16 | 0 | 2.0 | 1 | owner_cluster | 92311.738339 | cross_tile_reduction |
| 200.0 | 0 | 16 | 64 | 1.0 | 1 | owner_cluster | 91680.479478 | command_dispatch |
| 200.0 | 0 | 16 | 64 | 2.0 | 1 | owner_cluster | 92325.322928 | cross_tile_reduction |
| 200.0 | 4 | 0 | 0 | 1.0 | 1 | owner_cluster | 91014.834627 | cross_tile_reduction |
| 200.0 | 4 | 0 | 0 | 2.0 | 1 | owner_cluster | 91659.678077 | cross_tile_reduction |
| 200.0 | 4 | 0 | 64 | 1.0 | 1 | owner_cluster | 91028.419216 | cross_tile_reduction |
| 200.0 | 4 | 0 | 64 | 2.0 | 1 | owner_cluster | 91673.262666 | cross_tile_reduction |
| 200.0 | 4 | 16 | 0 | 1.0 | 1 | owner_cluster | 91884.24831 | command_dispatch |
| 200.0 | 4 | 16 | 0 | 2.0 | 1 | owner_cluster | 92529.09176 | cross_tile_reduction |
| 200.0 | 4 | 16 | 64 | 1.0 | 1 | owner_cluster | 91897.832899 | command_dispatch |
| 200.0 | 4 | 16 | 64 | 2.0 | 1 | owner_cluster | 92542.676349 | cross_tile_reduction |
| 400.0 | 0 | 0 | 0 | 1.0 | 2 | owner_cluster | 45400.120288 | tile_attention |
| 400.0 | 0 | 0 | 0 | 2.0 | 2 | owner_cluster | 45723.815568 | cross_tile_reduction |
| 400.0 | 0 | 0 | 64 | 1.0 | 2 | owner_cluster | 45413.704877 | tile_attention |
| 400.0 | 0 | 0 | 64 | 2.0 | 2 | owner_cluster | 45737.400157 | cross_tile_reduction |
| 400.0 | 0 | 16 | 0 | 1.0 | 2 | owner_cluster | 45834.82713 | command_dispatch |
| 400.0 | 0 | 16 | 0 | 2.0 | 2 | owner_cluster | 46158.52241 | cross_tile_reduction |
| 400.0 | 0 | 16 | 64 | 1.0 | 2 | owner_cluster | 45848.411718 | command_dispatch |
| 400.0 | 0 | 16 | 64 | 2.0 | 2 | owner_cluster | 46172.106998 | cross_tile_reduction |
| 400.0 | 4 | 0 | 0 | 1.0 | 2 | owner_cluster | 45617.473709 | tile_attention |
| 400.0 | 4 | 0 | 0 | 2.0 | 2 | owner_cluster | 45941.168989 | cross_tile_reduction |
| 400.0 | 4 | 0 | 64 | 1.0 | 2 | owner_cluster | 45631.058298 | tile_attention |
| 400.0 | 4 | 0 | 64 | 2.0 | 2 | owner_cluster | 45954.753578 | cross_tile_reduction |
| 400.0 | 4 | 16 | 0 | 1.0 | 2 | owner_cluster | 46052.18055 | command_dispatch |
| 400.0 | 4 | 16 | 0 | 2.0 | 2 | owner_cluster | 46375.87583 | command_dispatch |
| 400.0 | 4 | 16 | 64 | 1.0 | 2 | owner_cluster | 46065.765139 | command_dispatch |
| 400.0 | 4 | 16 | 64 | 2.0 | 2 | owner_cluster | 46389.460419 | cross_tile_reduction |
| 800.0 | 0 | 0 | 0 | 1.0 | 1 | owner_cluster | 22669.494819 | cross_tile_reduction |
| 800.0 | 0 | 0 | 0 | 2.0 | 1 | owner_cluster | 22829.962774 | cross_tile_reduction |
| 800.0 | 0 | 0 | 64 | 1.0 | 1 | owner_cluster | 22683.079408 | cross_tile_reduction |
| 800.0 | 0 | 0 | 64 | 2.0 | 1 | owner_cluster | 22843.547363 | cross_tile_reduction |
| 800.0 | 0 | 16 | 0 | 1.0 | 4 | owner_cluster | 22918.899379 | tile_attention |
| 800.0 | 0 | 16 | 0 | 2.0 | 4 | owner_cluster | 23082.126704 | tile_attention |
| 800.0 | 0 | 16 | 64 | 1.0 | 4 | owner_cluster | 22932.483968 | tile_attention |
| 800.0 | 0 | 16 | 64 | 2.0 | 4 | owner_cluster | 23095.711293 | tile_attention |
| 800.0 | 4 | 0 | 0 | 1.0 | 1 | owner_cluster | 22886.84824 | command_dispatch |
| 800.0 | 4 | 0 | 0 | 2.0 | 1 | owner_cluster | 23047.316195 | cross_tile_reduction |
| 800.0 | 4 | 0 | 64 | 1.0 | 1 | owner_cluster | 22900.432829 | command_dispatch |
| 800.0 | 4 | 0 | 64 | 2.0 | 1 | owner_cluster | 23060.900784 | cross_tile_reduction |
| 800.0 | 4 | 16 | 0 | 1.0 | 4 | owner_cluster | 23136.2528 | command_dispatch |
| 800.0 | 4 | 16 | 0 | 2.0 | 4 | owner_cluster | 23299.480125 | command_dispatch |
| 800.0 | 4 | 16 | 64 | 1.0 | 4 | owner_cluster | 23149.837389 | command_dispatch |
| 800.0 | 4 | 16 | 64 | 2.0 | 4 | owner_cluster | 23313.064714 | command_dispatch |
| 1200.0 | 0 | 0 | 0 | 1.0 | 8 | cluster_tree | 15134.08096 | tile_attention |
| 1200.0 | 0 | 0 | 0 | 2.0 | 8 | cluster_tree | 15244.668003 | tile_attention |
| 1200.0 | 0 | 0 | 64 | 1.0 | 8 | cluster_tree | 15147.665549 | tile_attention |
| 1200.0 | 0 | 0 | 64 | 2.0 | 8 | cluster_tree | 15258.252592 | tile_attention |
| 1200.0 | 0 | 16 | 0 | 1.0 | 8 | cluster_tree | 15242.75767 | tile_attention |
| 1200.0 | 0 | 16 | 0 | 2.0 | 8 | cluster_tree | 15353.344714 | tile_attention |
| 1200.0 | 0 | 16 | 64 | 1.0 | 8 | cluster_tree | 15256.342259 | tile_attention |
| 1200.0 | 0 | 16 | 64 | 2.0 | 8 | cluster_tree | 15366.929302 | tile_attention |
| 1200.0 | 4 | 0 | 0 | 1.0 | 8 | cluster_tree | 15351.434381 | tile_attention |
| 1200.0 | 4 | 0 | 0 | 2.0 | 8 | cluster_tree | 15462.021424 | tile_attention |
| 1200.0 | 4 | 0 | 64 | 1.0 | 8 | cluster_tree | 15365.01897 | tile_attention |
| 1200.0 | 4 | 0 | 64 | 2.0 | 8 | cluster_tree | 15475.606013 | tile_attention |
| 1200.0 | 4 | 16 | 0 | 1.0 | 8 | cluster_tree | 15460.111091 | tile_attention |
| 1200.0 | 4 | 16 | 0 | 2.0 | 8 | cluster_tree | 15570.698134 | tile_attention |
| 1200.0 | 4 | 16 | 64 | 1.0 | 8 | cluster_tree | 15473.69568 | tile_attention |
| 1200.0 | 4 | 16 | 64 | 2.0 | 8 | cluster_tree | 15584.282723 | tile_attention |

## Best By Measured L1 Profile

| die | L1 profile | logic used um2 | replicas | clusters | reduction | latency us | resource |
|---:|---|---:|---:|---:|---|---:|---|
| 200.0 | hd128_kv8_full_value_p16_ppc4_noc256 | 39946820.809825 | 44 | 1 | owner_cluster | 90797.481206 | cross_tile_reduction |
| 200.0 | hd64_kv8_full_value_p8_ppc2_noc128 | 39847646.321675 | 44 | 1 | owner_cluster | 90797.481206 | cross_tile_reduction |
| 200.0 | hd64_kv8_full_value_p8_ppc4_noc128 | 39931042.28435 | 44 | 1 | owner_cluster | 90797.481206 | cross_tile_reduction |
| 400.0 | hd128_kv8_full_value_p16_ppc4_noc256 | 79893641.61965 | 88 | 2 | owner_cluster | 45400.120288 | tile_attention |
| 400.0 | hd64_kv8_full_value_p8_ppc2_noc128 | 79695292.64335 | 88 | 2 | owner_cluster | 45400.120288 | tile_attention |
| 400.0 | hd64_kv8_full_value_p8_ppc4_noc128 | 79862084.5687 | 88 | 2 | owner_cluster | 45400.120288 | tile_attention |
| 800.0 | hd128_kv8_full_value_p16_ppc4_noc256 | 159929445.809825 | 177 | 1 | owner_cluster | 22669.494819 | cross_tile_reduction |
| 800.0 | hd64_kv8_full_value_p8_ppc2_noc128 | 159830271.321675 | 177 | 1 | owner_cluster | 22669.494819 | cross_tile_reduction |
| 800.0 | hd64_kv8_full_value_p8_ppc4_noc128 | 159913667.28435 | 177 | 1 | owner_cluster | 22669.494819 | cross_tile_reduction |
| 1200.0 | hd128_kv8_full_value_p16_ppc4_noc256 | 239316445.809825 | 265 | 1 | owner_cluster | 15150.0004 | cross_tile_reduction |
| 1200.0 | hd64_kv8_full_value_p8_ppc2_noc128 | 239394170.5734 | 264 | 8 | cluster_tree | 15134.08096 | tile_attention |
| 1200.0 | hd64_kv8_full_value_p8_ppc4_noc128 | 239300667.28435 | 265 | 1 | owner_cluster | 15150.0004 | cross_tile_reduction |

## Best By Die And Cluster

| die | clusters | arch | replicas | reduction | tile waves | tile service | reduction cycles | latency us | resource |
|---:|---:|---|---:|---|---:|---:|---:|---:|---|
| 200.0 | 1 | nm64_flat | 44 | owner_cluster | 256 | 1630 | 3038 | 90797.481206 | cross_tile_reduction |
| 200.0 | 2 | nm64_flat | 43 | owner_cluster | 128 | 3415 | 3195 | 95078.74927 | tile_attention |
| 200.0 | 4 | nm64_flat | 43 | owner_cluster | 64 | 7169 | 3377 | 99722.556048 | tile_attention |
| 200.0 | 8 | nm64_flat | 42 | owner_cluster | 32 | 14337 | 3428 | 99765.007888 | tile_attention |
| 200.0 | 16 | nm64_flat | 41 | owner_cluster | 16 | 35840 | 4363 | 124340.802582 | tile_attention |
| 400.0 | 1 | nm64_flat | 88 | owner_cluster | 256 | 816 | 1519 | 45453.185088 | cross_tile_reduction |
| 400.0 | 2 | nm64_flat | 88 | owner_cluster | 128 | 1630 | 1525 | 45400.120288 | tile_attention |
| 400.0 | 4 | nm64_flat | 87 | owner_cluster | 64 | 3415 | 1609 | 47532.68847 | tile_attention |
| 400.0 | 8 | nm64_flat | 87 | owner_cluster | 32 | 7169 | 1712 | 49857.13897 | tile_attention |
| 400.0 | 16 | nm64_flat | 85 | owner_cluster | 16 | 14337 | 1762 | 49883.246851 | tile_attention |
| 800.0 | 1 | nm64_flat | 177 | owner_cluster | 256 | 407 | 756 | 22669.494819 | cross_tile_reduction |
| 800.0 | 2 | nm64_flat | 177 | owner_cluster | 128 | 816 | 763 | 22725.318989 | tile_attention |
| 800.0 | 4 | nm64_flat | 176 | owner_cluster | 64 | 1630 | 769 | 22701.545958 | tile_attention |
| 800.0 | 8 | nm64_flat | 175 | owner_cluster | 32 | 3415 | 817 | 23766.874883 | tile_attention |
| 800.0 | 16 | nm64_flat | 174 | cluster_tree | 16 | 7169 | 880 | 24933.875965 | tile_attention |
| 1200.0 | 1 | nm64_flat | 265 | owner_cluster | 256 | 272 | 505 | 15150.0004 | cross_tile_reduction |
| 1200.0 | 2 | nm64_flat | 265 | owner_cluster | 128 | 545 | 509 | 15178.018614 | tile_attention |
| 1200.0 | 4 | nm64_flat | 265 | owner_cluster | 64 | 1088 | 513 | 15151.698474 | tile_attention |
| 1200.0 | 8 | nm64_flat | 264 | cluster_tree | 32 | 2173 | 521 | 15134.08096 | tile_attention |
| 1200.0 | 16 | nm64_flat | 263 | cluster_tree | 16 | 4480 | 552 | 15596.593757 | tile_attention |

## Assumptions

- One decode-token attention pass is split into sequence KV tiles.
- Tiles are statically assigned to active clusters by wave; each active cluster handles at most one tile per wave.
- Each tile produces softmax statistics and a partial value vector for the current token.
- Reduction strategies model cross-tile combination after tile service: centralized_tile sends every tile partial, owner_cluster and cluster_tree first reduce tiles locally per cluster.
- This is an analytic schedule model; it still does not model RTL command queues or cycle-accurate SRAM/NoC arbitration.
- Optional command and reducer overhead parameters are sensitivity knobs, not measured RTL/PPA.
- When measured L1 cost profiles are provided, their per-cluster tile/reducer, FIFO, and router area is subtracted from the logic budget before compute replicas are allocated.
- Measured L1 profile clock is combined by max() with measured compute-array clock; this is a conservative local macro proxy, not a full routed SoC timing closure.
- Measured L1 profiles in this run use full-value tile datapath PPA anchors plus memory/NoC primitives; softmax-weight generation, SRAM timing, and cycle-accurate NoC arbitration remain abstracted.
