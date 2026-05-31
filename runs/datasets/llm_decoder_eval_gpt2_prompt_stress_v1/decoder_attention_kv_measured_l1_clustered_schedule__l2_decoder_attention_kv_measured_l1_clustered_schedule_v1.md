# Decoder Attention/KV Clustered Schedule

- model: `llm_decoder_attention_kv_clustered_schedule_llama7b_v1`
- generated_row_count: `3194880`
- skipped_area_budget_count: `0`

## Best

| seq | die | SRAM | logic | L1 profile | arch | replicas | clusters | reduction | tile | clock ns | latency us | resource |
|---:|---:|---:|---:|---|---|---:|---:|---|---:|---:|---:|---|
| 131072 | 1200.0 | 0.4 | 0.2 | hd64_kv4_p8_ppc2_noc128 | nm64_flat | 265 | 8 | cluster_tree | 512 | 6.6331 | 15133.019664 | tile_attention |

## Best By Overhead

| die | cmd/tile | cmd/wave | reducer setup | reduction x | clusters | reduction | latency us | resource |
|---:|---:|---:|---:|---:|---:|---|---:|---|
| 200.0 | 0 | 0 | 0 | 1.0 | 4 | owner_cluster | 90764.368771 | tile_attention |
| 200.0 | 0 | 0 | 0 | 2.0 | 4 | owner_cluster | 91416.853552 | tile_attention |
| 200.0 | 0 | 0 | 64 | 1.0 | 4 | owner_cluster | 90777.95336 | tile_attention |
| 200.0 | 0 | 0 | 64 | 2.0 | 4 | owner_cluster | 91430.438141 | tile_attention |
| 200.0 | 0 | 16 | 0 | 1.0 | 4 | owner_cluster | 90981.722192 | tile_attention |
| 200.0 | 0 | 16 | 0 | 2.0 | 4 | owner_cluster | 91634.206973 | tile_attention |
| 200.0 | 0 | 16 | 64 | 1.0 | 4 | owner_cluster | 90995.306781 | tile_attention |
| 200.0 | 0 | 16 | 64 | 2.0 | 4 | owner_cluster | 91647.791562 | tile_attention |
| 200.0 | 4 | 0 | 0 | 1.0 | 4 | owner_cluster | 90981.722192 | tile_attention |
| 200.0 | 4 | 0 | 0 | 2.0 | 4 | owner_cluster | 91634.206973 | tile_attention |
| 200.0 | 4 | 0 | 64 | 1.0 | 4 | owner_cluster | 90995.306781 | tile_attention |
| 200.0 | 4 | 0 | 64 | 2.0 | 4 | owner_cluster | 91647.791562 | tile_attention |
| 200.0 | 4 | 16 | 0 | 1.0 | 4 | owner_cluster | 91199.075613 | tile_attention |
| 200.0 | 4 | 16 | 0 | 2.0 | 4 | owner_cluster | 91851.560394 | tile_attention |
| 200.0 | 4 | 16 | 64 | 1.0 | 4 | owner_cluster | 91212.660202 | tile_attention |
| 200.0 | 4 | 16 | 64 | 2.0 | 4 | owner_cluster | 91865.144982 | tile_attention |
| 400.0 | 0 | 0 | 0 | 1.0 | 8 | owner_cluster | 45387.384736 | tile_attention |
| 400.0 | 0 | 0 | 0 | 2.0 | 8 | owner_cluster | 45718.721347 | tile_attention |
| 400.0 | 0 | 0 | 64 | 1.0 | 8 | owner_cluster | 45400.969325 | tile_attention |
| 400.0 | 0 | 0 | 64 | 2.0 | 8 | owner_cluster | 45732.305936 | tile_attention |
| 400.0 | 0 | 16 | 0 | 1.0 | 8 | owner_cluster | 45496.061446 | tile_attention |
| 400.0 | 0 | 16 | 0 | 2.0 | 8 | owner_cluster | 45827.398058 | tile_attention |
| 400.0 | 0 | 16 | 64 | 1.0 | 8 | owner_cluster | 45509.646035 | tile_attention |
| 400.0 | 0 | 16 | 64 | 2.0 | 8 | owner_cluster | 45840.982646 | tile_attention |
| 400.0 | 4 | 0 | 0 | 1.0 | 8 | owner_cluster | 45604.738157 | tile_attention |
| 400.0 | 4 | 0 | 0 | 2.0 | 8 | owner_cluster | 45936.074768 | tile_attention |
| 400.0 | 4 | 0 | 64 | 1.0 | 8 | owner_cluster | 45618.322746 | tile_attention |
| 400.0 | 4 | 0 | 64 | 2.0 | 8 | owner_cluster | 45949.659357 | tile_attention |
| 400.0 | 4 | 16 | 0 | 1.0 | 8 | owner_cluster | 45713.414867 | tile_attention |
| 400.0 | 4 | 16 | 0 | 2.0 | 8 | owner_cluster | 46044.751478 | tile_attention |
| 400.0 | 4 | 16 | 64 | 1.0 | 8 | owner_cluster | 45726.999456 | tile_attention |
| 400.0 | 4 | 16 | 64 | 2.0 | 8 | owner_cluster | 46058.336067 | tile_attention |
| 800.0 | 0 | 0 | 0 | 1.0 | 1 | owner_cluster | 22669.494819 | cross_tile_reduction |
| 800.0 | 0 | 0 | 0 | 2.0 | 1 | owner_cluster | 22829.962774 | cross_tile_reduction |
| 800.0 | 0 | 0 | 64 | 1.0 | 1 | owner_cluster | 22683.079408 | cross_tile_reduction |
| 800.0 | 0 | 0 | 64 | 2.0 | 1 | owner_cluster | 22843.547363 | cross_tile_reduction |
| 800.0 | 0 | 16 | 0 | 1.0 | 16 | cluster_tree | 22753.337203 | tile_attention |
| 800.0 | 0 | 16 | 0 | 2.0 | 16 | cluster_tree | 22924.205859 | tile_attention |
| 800.0 | 0 | 16 | 64 | 1.0 | 16 | cluster_tree | 22766.921792 | tile_attention |
| 800.0 | 0 | 16 | 64 | 2.0 | 16 | cluster_tree | 22937.790448 | tile_attention |
| 800.0 | 4 | 0 | 0 | 1.0 | 1 | owner_cluster | 22886.84824 | command_dispatch |
| 800.0 | 4 | 0 | 0 | 2.0 | 1 | owner_cluster | 23047.316195 | cross_tile_reduction |
| 800.0 | 4 | 0 | 64 | 1.0 | 1 | owner_cluster | 22900.432829 | command_dispatch |
| 800.0 | 4 | 0 | 64 | 2.0 | 1 | owner_cluster | 23060.900784 | cross_tile_reduction |
| 800.0 | 4 | 16 | 0 | 1.0 | 16 | cluster_tree | 22970.690624 | tile_attention |
| 800.0 | 4 | 16 | 0 | 2.0 | 16 | cluster_tree | 23141.55928 | tile_attention |
| 800.0 | 4 | 16 | 64 | 1.0 | 16 | cluster_tree | 22984.275213 | tile_attention |
| 800.0 | 4 | 16 | 64 | 2.0 | 16 | cluster_tree | 23155.143869 | tile_attention |
| 1200.0 | 0 | 0 | 0 | 1.0 | 8 | cluster_tree | 15133.019664 | tile_attention |
| 1200.0 | 0 | 0 | 0 | 2.0 | 8 | cluster_tree | 15243.606707 | tile_attention |
| 1200.0 | 0 | 0 | 64 | 1.0 | 8 | cluster_tree | 15146.604253 | tile_attention |
| 1200.0 | 0 | 0 | 64 | 2.0 | 8 | cluster_tree | 15257.191296 | tile_attention |
| 1200.0 | 0 | 16 | 0 | 1.0 | 8 | cluster_tree | 15241.696374 | tile_attention |
| 1200.0 | 0 | 16 | 0 | 2.0 | 8 | cluster_tree | 15352.283418 | tile_attention |
| 1200.0 | 0 | 16 | 64 | 1.0 | 8 | cluster_tree | 15255.280963 | tile_attention |
| 1200.0 | 0 | 16 | 64 | 2.0 | 8 | cluster_tree | 15365.868006 | tile_attention |
| 1200.0 | 4 | 0 | 0 | 1.0 | 8 | cluster_tree | 15350.373085 | tile_attention |
| 1200.0 | 4 | 0 | 0 | 2.0 | 8 | cluster_tree | 15460.960128 | tile_attention |
| 1200.0 | 4 | 0 | 64 | 1.0 | 8 | cluster_tree | 15363.957674 | tile_attention |
| 1200.0 | 4 | 0 | 64 | 2.0 | 8 | cluster_tree | 15474.544717 | tile_attention |
| 1200.0 | 4 | 16 | 0 | 1.0 | 8 | cluster_tree | 15459.049795 | tile_attention |
| 1200.0 | 4 | 16 | 0 | 2.0 | 8 | cluster_tree | 15569.636838 | tile_attention |
| 1200.0 | 4 | 16 | 64 | 1.0 | 8 | cluster_tree | 15472.634384 | tile_attention |
| 1200.0 | 4 | 16 | 64 | 2.0 | 8 | cluster_tree | 15583.221427 | tile_attention |

## Best By Measured L1 Profile

| die | L1 profile | logic used um2 | replicas | clusters | reduction | latency us | resource |
|---:|---|---:|---:|---:|---|---:|---|
| 200.0 | hd128_kv4_p8_ppc4_noc256 | 39981202.7218 | 44 | 4 | owner_cluster | 90764.368771 | tile_attention |
| 200.0 | hd128_kv8_p16_ppc4_noc256 | 39810819.262325 | 44 | 1 | owner_cluster | 90797.481206 | cross_tile_reduction |
| 200.0 | hd64_kv4_p8_ppc2_noc128 | 39913646.1947 | 44 | 4 | owner_cluster | 90764.368771 | tile_attention |
| 200.0 | hd64_kv4_p8_ppc4_noc128 | 39964093.4602 | 44 | 4 | owner_cluster | 90764.368771 | tile_attention |
| 400.0 | hd128_kv4_p8_ppc4_noc256 | 79962405.4436 | 88 | 8 | owner_cluster | 45387.384736 | tile_attention |
| 400.0 | hd128_kv8_p16_ppc4_noc256 | 79621638.52465 | 88 | 2 | owner_cluster | 45400.120288 | tile_attention |
| 400.0 | hd64_kv4_p8_ppc2_noc128 | 79827292.3894 | 88 | 8 | owner_cluster | 45387.384736 | tile_attention |
| 400.0 | hd64_kv4_p8_ppc4_noc128 | 79928186.9204 | 88 | 8 | owner_cluster | 45387.384736 | tile_attention |
| 800.0 | hd128_kv4_p8_ppc4_noc256 | 159748050.68045 | 177 | 1 | owner_cluster | 22669.494819 | cross_tile_reduction |
| 800.0 | hd128_kv8_p16_ppc4_noc256 | 159793444.262325 | 177 | 1 | owner_cluster | 22669.494819 | cross_tile_reduction |
| 800.0 | hd64_kv4_p8_ppc2_noc128 | 159731161.548675 | 177 | 1 | owner_cluster | 22669.494819 | cross_tile_reduction |
| 800.0 | hd64_kv4_p8_ppc4_noc128 | 159743773.36505 | 177 | 1 | owner_cluster | 22669.494819 | cross_tile_reduction |
| 1200.0 | hd128_kv4_p8_ppc4_noc256 | 239638530.4436 | 265 | 8 | cluster_tree | 15133.019664 | tile_attention |
| 1200.0 | hd128_kv8_p16_ppc4_noc256 | 239099554.0986 | 264 | 8 | cluster_tree | 15134.08096 | tile_attention |
| 1200.0 | hd64_kv4_p8_ppc2_noc128 | 239503417.3894 | 265 | 8 | cluster_tree | 15133.019664 | tile_attention |
| 1200.0 | hd64_kv4_p8_ppc4_noc128 | 239604311.9204 | 265 | 8 | cluster_tree | 15133.019664 | tile_attention |

## Best By Die And Cluster

| die | clusters | arch | replicas | reduction | tile waves | tile service | reduction cycles | latency us | resource |
|---:|---:|---|---:|---|---:|---:|---:|---:|---|
| 200.0 | 1 | nm64_flat | 44 | owner_cluster | 256 | 1630 | 3038 | 90797.481206 | cross_tile_reduction |
| 200.0 | 2 | nm64_flat | 44 | owner_cluster | 128 | 3260 | 3050 | 90800.028317 | tile_attention |
| 200.0 | 4 | nm64_flat | 44 | owner_cluster | 64 | 6517 | 3074 | 90764.368771 | tile_attention |
| 200.0 | 8 | nm64_flat | 43 | owner_cluster | 32 | 14337 | 3425 | 99725.952195 | tile_attention |
| 200.0 | 16 | nm64_flat | 43 | owner_cluster | 16 | 35840 | 4354 | 124259.931827 | tile_attention |
| 400.0 | 1 | nm64_flat | 88 | owner_cluster | 256 | 816 | 1519 | 45453.185088 | cross_tile_reduction |
| 400.0 | 2 | nm64_flat | 88 | owner_cluster | 128 | 1630 | 1525 | 45400.120288 | tile_attention |
| 400.0 | 4 | nm64_flat | 88 | owner_cluster | 64 | 3260 | 1537 | 45402.667398 | tile_attention |
| 400.0 | 8 | nm64_flat | 88 | owner_cluster | 32 | 6517 | 1561 | 45387.384736 | tile_attention |
| 400.0 | 16 | nm64_flat | 87 | owner_cluster | 16 | 14337 | 1760 | 49863.931264 | tile_attention |
| 800.0 | 1 | nm64_flat | 177 | owner_cluster | 256 | 407 | 756 | 22669.494819 | cross_tile_reduction |
| 800.0 | 2 | nm64_flat | 177 | owner_cluster | 128 | 816 | 763 | 22725.318989 | tile_attention |
| 800.0 | 4 | nm64_flat | 177 | owner_cluster | 64 | 1630 | 769 | 22699.423366 | tile_attention |
| 800.0 | 8 | nm64_flat | 176 | owner_cluster | 32 | 3260 | 781 | 22704.093069 | tile_attention |
| 800.0 | 16 | nm64_flat | 176 | cluster_tree | 16 | 6517 | 805 | 22698.998848 | tile_attention |
| 1200.0 | 1 | nm64_flat | 265 | owner_cluster | 256 | 272 | 505 | 15150.0004 | cross_tile_reduction |
| 1200.0 | 2 | nm64_flat | 265 | owner_cluster | 128 | 545 | 509 | 15178.018614 | tile_attention |
| 1200.0 | 4 | nm64_flat | 265 | owner_cluster | 64 | 1088 | 513 | 15151.698474 | tile_attention |
| 1200.0 | 8 | nm64_flat | 265 | cluster_tree | 32 | 2173 | 521 | 15133.019664 | tile_attention |
| 1200.0 | 16 | nm64_flat | 265 | cluster_tree | 16 | 4480 | 552 | 15594.683424 | tile_attention |

## Assumptions

- One decode-token attention pass is split into sequence KV tiles.
- Tiles are statically assigned to active clusters by wave; each active cluster handles at most one tile per wave.
- Each tile produces softmax statistics and a partial value vector for the current token.
- Reduction strategies model cross-tile combination after tile service: centralized_tile sends every tile partial, owner_cluster and cluster_tree first reduce tiles locally per cluster.
- This is an analytic schedule model; it still does not model RTL command queues or cycle-accurate SRAM/NoC arbitration.
- Optional command and reducer overhead parameters are sensitivity knobs, not measured RTL/PPA.
- When measured L1 cost profiles are provided, their per-cluster tile/reducer, FIFO, and router area is subtracted from the logic budget before compute replicas are allocated.
- Measured L1 profile clock is combined by max() with measured compute-array clock; this is a conservative local macro proxy, not a full routed SoC timing closure.
- Measured L1 tile/reducer profiles cover QK/stat/local partial reduction structure and memory/NoC primitives; the full softmax-weighted value datapath still needs a later L1 closure run.
