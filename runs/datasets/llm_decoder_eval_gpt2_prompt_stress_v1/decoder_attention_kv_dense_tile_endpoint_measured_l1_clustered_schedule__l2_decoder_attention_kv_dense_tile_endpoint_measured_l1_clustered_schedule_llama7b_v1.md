# Decoder Attention/KV Clustered Schedule

- model: `llm_decoder_attention_kv_clustered_schedule_llama7b_v1`
- generated_row_count: `4128768`
- skipped_area_budget_count: `847872`

## Best

| seq | die | SRAM | logic | L1 profile | arch | replicas | clusters | reduction | tile | clock ns | latency us | resource |
|---:|---:|---:|---:|---|---|---:|---:|---|---:|---:|---:|---|
| 131072 | 1200.0 | 0.4 | 0.4 | hd64_kv8_full_value_p8_ppc2_noc128_softmax_int8_q10 | dense_gemm_16x8_k1_p1 | 1035 | 1 | owner_cluster | 512 | 5.9811 | 1758.156307 | cross_tile_reduction |

## Best By Overhead

| die | cmd/tile | cmd/wave | reducer setup | reduction x | clusters | reduction | latency us | resource |
|---:|---:|---:|---:|---:|---:|---|---:|---|
| 200.0 | 0 | 0 | 0 | 1.0 | 1 | owner_cluster | 10546.449706 | cross_tile_reduction |
| 200.0 | 0 | 0 | 0 | 2.0 | 1 | owner_cluster | 10620.902438 | cross_tile_reduction |
| 200.0 | 0 | 0 | 64 | 1.0 | 1 | owner_cluster | 10558.698998 | cross_tile_reduction |
| 200.0 | 0 | 0 | 64 | 2.0 | 1 | owner_cluster | 10633.151731 | cross_tile_reduction |
| 200.0 | 0 | 16 | 0 | 1.0 | 8 | cluster_tree | 10829.331811 | tile_attention |
| 200.0 | 0 | 16 | 0 | 2.0 | 8 | cluster_tree | 10907.803843 | tile_attention |
| 200.0 | 0 | 16 | 64 | 1.0 | 8 | cluster_tree | 10841.581104 | tile_attention |
| 200.0 | 0 | 16 | 64 | 2.0 | 8 | cluster_tree | 10920.053136 | tile_attention |
| 200.0 | 4 | 0 | 0 | 1.0 | 1 | owner_cluster | 10742.43839 | command_dispatch |
| 200.0 | 4 | 0 | 0 | 2.0 | 1 | owner_cluster | 10816.891123 | command_dispatch |
| 200.0 | 4 | 0 | 64 | 1.0 | 1 | owner_cluster | 10754.687683 | command_dispatch |
| 200.0 | 4 | 0 | 64 | 2.0 | 1 | owner_cluster | 10829.140416 | command_dispatch |
| 200.0 | 4 | 16 | 0 | 1.0 | 8 | cluster_tree | 11025.320496 | tile_attention |
| 200.0 | 4 | 16 | 0 | 2.0 | 8 | cluster_tree | 11103.792528 | tile_attention |
| 200.0 | 4 | 16 | 64 | 1.0 | 8 | cluster_tree | 11037.569789 | tile_attention |
| 200.0 | 4 | 16 | 64 | 2.0 | 8 | cluster_tree | 11116.041821 | tile_attention |
| 400.0 | 0 | 0 | 0 | 1.0 | 1 | owner_cluster | 5273.511946 | cross_tile_reduction |
| 400.0 | 0 | 0 | 0 | 2.0 | 1 | owner_cluster | 5310.83401 | cross_tile_reduction |
| 400.0 | 0 | 0 | 64 | 1.0 | 1 | owner_cluster | 5285.761238 | cross_tile_reduction |
| 400.0 | 0 | 0 | 64 | 2.0 | 1 | owner_cluster | 5323.083302 | cross_tile_reduction |
| 400.0 | 0 | 16 | 0 | 1.0 | 16 | cluster_tree | 5416.10137 | tile_attention |
| 400.0 | 0 | 16 | 0 | 2.0 | 16 | cluster_tree | 5456.677152 | tile_attention |
| 400.0 | 0 | 16 | 64 | 1.0 | 16 | cluster_tree | 5428.350662 | tile_attention |
| 400.0 | 0 | 16 | 64 | 2.0 | 16 | cluster_tree | 5468.926445 | tile_attention |
| 400.0 | 4 | 0 | 0 | 1.0 | 1 | owner_cluster | 5469.50063 | command_dispatch |
| 400.0 | 4 | 0 | 0 | 2.0 | 1 | owner_cluster | 5506.822694 | command_dispatch |
| 400.0 | 4 | 0 | 64 | 1.0 | 1 | owner_cluster | 5481.749923 | command_dispatch |
| 400.0 | 4 | 0 | 64 | 2.0 | 1 | owner_cluster | 5519.071987 | command_dispatch |
| 400.0 | 4 | 16 | 0 | 1.0 | 16 | cluster_tree | 5612.090054 | tile_attention |
| 400.0 | 4 | 16 | 0 | 2.0 | 16 | cluster_tree | 5652.665837 | tile_attention |
| 400.0 | 4 | 16 | 64 | 1.0 | 16 | cluster_tree | 5624.339347 | tile_attention |
| 400.0 | 4 | 16 | 64 | 2.0 | 16 | cluster_tree | 5664.91513 | tile_attention |
| 800.0 | 0 | 0 | 0 | 1.0 | 2 | owner_cluster | 2637.234461 | tile_attention |
| 800.0 | 0 | 0 | 0 | 2.0 | 2 | owner_cluster | 2656.373981 | cross_tile_reduction |
| 800.0 | 0 | 0 | 64 | 1.0 | 2 | owner_cluster | 2649.483754 | cross_tile_reduction |
| 800.0 | 0 | 0 | 64 | 2.0 | 2 | owner_cluster | 2668.623274 | cross_tile_reduction |
| 800.0 | 0 | 16 | 0 | 1.0 | 16 | cluster_tree | 2738.099731 | tile_attention |
| 800.0 | 0 | 16 | 0 | 2.0 | 16 | cluster_tree | 2759.727389 | tile_attention |
| 800.0 | 0 | 16 | 64 | 1.0 | 16 | cluster_tree | 2750.349024 | tile_attention |
| 800.0 | 0 | 16 | 64 | 2.0 | 16 | cluster_tree | 2771.976682 | tile_attention |
| 800.0 | 4 | 0 | 0 | 1.0 | 2 | owner_cluster | 2833.223146 | command_dispatch |
| 800.0 | 4 | 0 | 0 | 2.0 | 2 | owner_cluster | 2852.362666 | command_dispatch |
| 800.0 | 4 | 0 | 64 | 1.0 | 2 | owner_cluster | 2845.472438 | command_dispatch |
| 800.0 | 4 | 0 | 64 | 2.0 | 2 | owner_cluster | 2864.611958 | command_dispatch |
| 800.0 | 4 | 16 | 0 | 1.0 | 16 | cluster_tree | 2934.088416 | command_dispatch |
| 800.0 | 4 | 16 | 0 | 2.0 | 16 | cluster_tree | 2955.716074 | command_dispatch |
| 800.0 | 4 | 16 | 64 | 1.0 | 16 | cluster_tree | 2946.337709 | command_dispatch |
| 800.0 | 4 | 16 | 64 | 2.0 | 16 | cluster_tree | 2967.965366 | command_dispatch |
| 1200.0 | 0 | 0 | 0 | 1.0 | 1 | owner_cluster | 1758.156307 | cross_tile_reduction |
| 1200.0 | 0 | 0 | 0 | 2.0 | 1 | owner_cluster | 1770.78839 | cross_tile_reduction |
| 1200.0 | 0 | 0 | 64 | 1.0 | 1 | owner_cluster | 1770.4056 | cross_tile_reduction |
| 1200.0 | 0 | 0 | 64 | 2.0 | 1 | owner_cluster | 1783.037683 | cross_tile_reduction |
| 1200.0 | 0 | 16 | 0 | 1.0 | 16 | cluster_tree | 1809.641616 | tile_attention |
| 1200.0 | 0 | 16 | 0 | 2.0 | 16 | cluster_tree | 1824.570442 | tile_attention |
| 1200.0 | 0 | 16 | 64 | 1.0 | 16 | cluster_tree | 1821.890909 | tile_attention |
| 1200.0 | 0 | 16 | 64 | 2.0 | 16 | cluster_tree | 1836.819734 | tile_attention |
| 1200.0 | 4 | 0 | 0 | 1.0 | 1 | owner_cluster | 1954.144992 | command_dispatch |
| 1200.0 | 4 | 0 | 0 | 2.0 | 1 | owner_cluster | 1966.777075 | command_dispatch |
| 1200.0 | 4 | 0 | 64 | 1.0 | 1 | owner_cluster | 1966.394285 | command_dispatch |
| 1200.0 | 4 | 0 | 64 | 2.0 | 1 | owner_cluster | 1979.026368 | command_dispatch |
| 1200.0 | 4 | 16 | 0 | 1.0 | 16 | cluster_tree | 2005.630301 | command_dispatch |
| 1200.0 | 4 | 16 | 0 | 2.0 | 16 | cluster_tree | 2020.559126 | command_dispatch |
| 1200.0 | 4 | 16 | 64 | 1.0 | 16 | cluster_tree | 2017.879594 | command_dispatch |
| 1200.0 | 4 | 16 | 64 | 2.0 | 16 | cluster_tree | 2032.808419 | command_dispatch |

## Best By Measured L1 Profile

| die | L1 profile | logic used um2 | replicas | clusters | reduction | latency us | resource |
|---:|---|---:|---:|---:|---|---:|---|
| 200.0 | hd128_kv8_full_value_p16_ppc4_noc256_softmax_int8_q10 | 79545344.15565 | 171 | 1 | owner_cluster | 10548.172262 | cross_tile_reduction |
| 200.0 | hd128_kv8_full_value_p16_ppc4_noc256_softmax_int8_q12 | 79549073.45845 | 171 | 1 | owner_cluster | 10548.172262 | cross_tile_reduction |
| 200.0 | hd128_kv8_full_value_p16_ppc4_noc256_softmax_int8_q16 | 79550883.607675 | 171 | 1 | owner_cluster | 10548.172262 | cross_tile_reduction |
| 200.0 | hd64_kv8_full_value_p8_ppc2_noc128_softmax_int8_q10 | 79909543.6675 | 172 | 1 | owner_cluster | 10546.449706 | cross_tile_reduction |
| 200.0 | hd64_kv8_full_value_p8_ppc2_noc128_softmax_int8_q12 | 79913272.9703 | 172 | 1 | owner_cluster | 10546.449706 | cross_tile_reduction |
| 200.0 | hd64_kv8_full_value_p8_ppc2_noc128_softmax_int8_q16 | 79915083.119525 | 172 | 1 | owner_cluster | 10546.449706 | cross_tile_reduction |
| 200.0 | hd64_kv8_full_value_p8_ppc4_noc128_softmax_int8_q10 | 79992939.630175 | 172 | 1 | owner_cluster | 10546.449706 | cross_tile_reduction |
| 200.0 | hd64_kv8_full_value_p8_ppc4_noc128_softmax_int8_q12 | 79996668.932975 | 172 | 1 | owner_cluster | 10546.449706 | cross_tile_reduction |
| 200.0 | hd64_kv8_full_value_p8_ppc4_noc128_softmax_int8_q16 | 79998479.0822 | 172 | 1 | owner_cluster | 10546.449706 | cross_tile_reduction |
| 400.0 | hd128_kv8_full_value_p16_ppc4_noc256_softmax_int8_q10 | 159709046.15565 | 344 | 1 | owner_cluster | 5273.511946 | cross_tile_reduction |
| 400.0 | hd128_kv8_full_value_p16_ppc4_noc256_softmax_int8_q12 | 159712775.45845 | 344 | 1 | owner_cluster | 5273.511946 | cross_tile_reduction |
| 400.0 | hd128_kv8_full_value_p16_ppc4_noc256_softmax_int8_q16 | 159714585.607675 | 344 | 1 | owner_cluster | 5273.511946 | cross_tile_reduction |
| 400.0 | hd64_kv8_full_value_p8_ppc2_noc128_softmax_int8_q10 | 159609871.6675 | 344 | 1 | owner_cluster | 5273.511946 | cross_tile_reduction |
| 400.0 | hd64_kv8_full_value_p8_ppc2_noc128_softmax_int8_q12 | 159613600.9703 | 344 | 1 | owner_cluster | 5273.511946 | cross_tile_reduction |
| 400.0 | hd64_kv8_full_value_p8_ppc2_noc128_softmax_int8_q16 | 159615411.119525 | 344 | 1 | owner_cluster | 5273.511946 | cross_tile_reduction |
| 400.0 | hd64_kv8_full_value_p8_ppc4_noc128_softmax_int8_q10 | 159693267.630175 | 344 | 1 | owner_cluster | 5273.511946 | cross_tile_reduction |
| 400.0 | hd64_kv8_full_value_p8_ppc4_noc128_softmax_int8_q12 | 159696996.932975 | 344 | 1 | owner_cluster | 5273.511946 | cross_tile_reduction |
| 400.0 | hd64_kv8_full_value_p8_ppc4_noc128_softmax_int8_q16 | 159698807.0822 | 344 | 1 | owner_cluster | 5273.511946 | cross_tile_reduction |
| 800.0 | hd128_kv8_full_value_p16_ppc4_noc256_softmax_int8_q10 | 319881466.3113 | 689 | 2 | owner_cluster | 2637.234461 | tile_attention |
| 800.0 | hd128_kv8_full_value_p16_ppc4_noc256_softmax_int8_q12 | 319888924.9169 | 689 | 2 | owner_cluster | 2637.234461 | tile_attention |
| 800.0 | hd128_kv8_full_value_p16_ppc4_noc256_softmax_int8_q16 | 319892545.21535 | 689 | 2 | owner_cluster | 2637.234461 | tile_attention |
| 800.0 | hd64_kv8_full_value_p8_ppc2_noc128_softmax_int8_q10 | 319683117.335 | 689 | 2 | owner_cluster | 2637.234461 | tile_attention |
| 800.0 | hd64_kv8_full_value_p8_ppc2_noc128_softmax_int8_q12 | 319690575.9406 | 689 | 2 | owner_cluster | 2637.234461 | tile_attention |
| 800.0 | hd64_kv8_full_value_p8_ppc2_noc128_softmax_int8_q16 | 319694196.23905 | 689 | 2 | owner_cluster | 2637.234461 | tile_attention |
| 800.0 | hd64_kv8_full_value_p8_ppc4_noc128_softmax_int8_q10 | 319849909.26035 | 689 | 2 | owner_cluster | 2637.234461 | tile_attention |
| 800.0 | hd64_kv8_full_value_p8_ppc4_noc128_softmax_int8_q12 | 319857367.86595 | 689 | 2 | owner_cluster | 2637.234461 | tile_attention |
| 800.0 | hd64_kv8_full_value_p8_ppc4_noc128_softmax_int8_q16 | 319860988.1644 | 689 | 2 | owner_cluster | 2637.234461 | tile_attention |
| 1200.0 | hd128_kv8_full_value_p16_ppc4_noc256_softmax_int8_q10 | 479900480.15565 | 1035 | 1 | owner_cluster | 1758.156307 | cross_tile_reduction |
| 1200.0 | hd128_kv8_full_value_p16_ppc4_noc256_softmax_int8_q12 | 479904209.45845 | 1035 | 1 | owner_cluster | 1758.156307 | cross_tile_reduction |
| 1200.0 | hd128_kv8_full_value_p16_ppc4_noc256_softmax_int8_q16 | 479906019.607675 | 1035 | 1 | owner_cluster | 1758.156307 | cross_tile_reduction |
| 1200.0 | hd64_kv8_full_value_p8_ppc2_noc128_softmax_int8_q10 | 479801305.6675 | 1035 | 1 | owner_cluster | 1758.156307 | cross_tile_reduction |
| 1200.0 | hd64_kv8_full_value_p8_ppc2_noc128_softmax_int8_q12 | 479805034.9703 | 1035 | 1 | owner_cluster | 1758.156307 | cross_tile_reduction |
| 1200.0 | hd64_kv8_full_value_p8_ppc2_noc128_softmax_int8_q16 | 479806845.119525 | 1035 | 1 | owner_cluster | 1758.156307 | cross_tile_reduction |
| 1200.0 | hd64_kv8_full_value_p8_ppc4_noc128_softmax_int8_q10 | 479884701.630175 | 1035 | 1 | owner_cluster | 1758.156307 | cross_tile_reduction |
| 1200.0 | hd64_kv8_full_value_p8_ppc4_noc128_softmax_int8_q12 | 479888430.932975 | 1035 | 1 | owner_cluster | 1758.156307 | cross_tile_reduction |
| 1200.0 | hd64_kv8_full_value_p8_ppc4_noc128_softmax_int8_q16 | 479890241.0822 | 1035 | 1 | owner_cluster | 1758.156307 | cross_tile_reduction |

## Best By Die And Cluster

| die | clusters | arch | replicas | reduction | tile waves | tile service | reduction cycles | latency us | resource |
|---:|---:|---|---:|---|---:|---:|---:|---:|---|
| 200.0 | 1 | dense_gemm_16x8_k1_p1 | 172 | owner_cluster | 256 | 210 | 389 | 10546.449706 | cross_tile_reduction |
| 200.0 | 2 | dense_gemm_16x8_k1_p1 | 171 | owner_cluster | 128 | 423 | 396 | 10622.4336 | tile_attention |
| 200.0 | 4 | dense_gemm_16x8_k1_p1 | 170 | cluster_tree | 64 | 856 | 404 | 10747.414666 | tile_attention |
| 200.0 | 8 | dense_gemm_16x8_k1_p1 | 169 | cluster_tree | 32 | 1709 | 410 | 10731.337469 | tile_attention |
| 200.0 | 16 | dense_gemm_16x8_k1_p1 | 165 | cluster_tree | 16 | 3586 | 442 | 11256.334502 | tile_attention |
| 400.0 | 1 | dense_gemm_16x8_k1_p1 | 344 | owner_cluster | 256 | 105 | 195 | 5273.511946 | cross_tile_reduction |
| 400.0 | 2 | dense_gemm_16x8_k1_p1 | 344 | owner_cluster | 128 | 210 | 197 | 5273.894736 | tile_attention |
| 400.0 | 4 | dense_gemm_16x8_k1_p1 | 343 | cluster_tree | 64 | 423 | 202 | 5311.790986 | tile_attention |
| 400.0 | 8 | dense_gemm_16x8_k1_p1 | 341 | cluster_tree | 32 | 856 | 208 | 5374.760006 | tile_attention |
| 400.0 | 16 | dense_gemm_16x8_k1_p1 | 338 | cluster_tree | 16 | 1709 | 212 | 5367.104198 | tile_attention |
| 800.0 | 1 | dense_gemm_16x8_k1_p1 | 690 | owner_cluster | 256 | 53 | 98 | 2661.350256 | cross_tile_reduction |
| 800.0 | 2 | dense_gemm_16x8_k1_p1 | 689 | owner_cluster | 128 | 105 | 100 | 2637.234461 | tile_attention |
| 800.0 | 4 | dense_gemm_16x8_k1_p1 | 688 | cluster_tree | 64 | 210 | 103 | 2638.000042 | tile_attention |
| 800.0 | 8 | dense_gemm_16x8_k1_p1 | 686 | cluster_tree | 32 | 423 | 107 | 2657.139562 | tile_attention |
| 800.0 | 16 | dense_gemm_16x8_k1_p1 | 683 | cluster_tree | 16 | 856 | 113 | 2689.10256 | tile_attention |
| 1200.0 | 1 | dense_gemm_16x8_k1_p1 | 1035 | owner_cluster | 256 | 35 | 66 | 1758.156307 | cross_tile_reduction |
| 1200.0 | 2 | dense_gemm_16x8_k1_p1 | 1034 | owner_cluster | 128 | 70 | 68 | 1758.539098 | tile_attention |
| 1200.0 | 4 | dense_gemm_16x8_k1_p1 | 1034 | cluster_tree | 64 | 140 | 71 | 1759.113283 | tile_attention |
| 1200.0 | 8 | dense_gemm_16x8_k1_p1 | 1032 | cluster_tree | 32 | 280 | 74 | 1759.687469 | tile_attention |
| 1200.0 | 16 | dense_gemm_16x8_k1_p1 | 1028 | cluster_tree | 16 | 560 | 78 | 1760.644445 | tile_attention |

## Assumptions

- One decode-token attention pass is split into sequence KV tiles.
- Tiles are statically assigned to active clusters by wave; each active cluster handles at most one tile per wave.
- Each tile produces softmax statistics and a partial value vector for the current token.
- Reduction strategies model cross-tile combination after tile service: centralized_tile sends every tile partial, owner_cluster and cluster_tree first reduce tiles locally per cluster.
- This is an analytic schedule model; it still does not model RTL command queues or cycle-accurate SRAM/NoC arbitration.
- Optional command and reducer overhead parameters are sensitivity knobs, not measured RTL/PPA.
- When measured L1 cost profiles are provided, their per-cluster tile/reducer, FIFO, router, and endpoint area is subtracted from the logic budget before compute replicas are allocated.
- Measured L1 profile clock is combined by max() with measured compute-array clock; this is a conservative local macro proxy, not a full routed SoC timing closure.
- Measured L1 profiles charge the local tile/value datapath, optional softmax-weight generator, and memory/NoC/endpoint primitives listed in the selected cost file; cycle-accurate SRAM/NoC arbitration remains an analytic service model.
