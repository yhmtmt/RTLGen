# Decoder Attention/KV Clustered Schedule

- model: `llm_decoder_attention_kv_clustered_schedule_llama7b_v1`
- generated_row_count: `25194240`
- skipped_area_budget_count: `8398080`

## Best

| seq | die | SRAM | logic | L1 profile | arch | replicas | clusters | reduction | tile | clock ns | latency us | resource |
|---:|---:|---:|---:|---|---|---:|---:|---|---:|---:|---:|---|
| 131072 | 1200.0 | 0.35 | 0.5 | hd64_kv8_full_value_p8_ppc2_noc128_softmax_int8_q10 | dense_gemm_16x8_k1_p1 | 1291 | 8 | cluster_tree | 1024 | 5.9811 | 1399.864493 | tile_attention |

## Best By Overhead

| die | cmd/tile | cmd/wave | reducer setup | reduction x | clusters | reduction | latency us | resource |
|---:|---:|---:|---:|---:|---:|---|---:|---|
| 800.0 | 0 | 0 | 0 | 1.0 | 4 | cluster_tree | 2096.925811 | tile_attention |
| 800.0 | 0 | 0 | 0 | 2.0 | 4 | cluster_tree | 2105.3472 | tile_attention |
| 800.0 | 0 | 0 | 0 | 4.0 | 4 | cluster_tree | 2122.189978 | tile_attention |
| 800.0 | 0 | 0 | 64 | 1.0 | 4 | cluster_tree | 2109.175104 | tile_attention |
| 800.0 | 0 | 0 | 64 | 2.0 | 4 | cluster_tree | 2117.596493 | tile_attention |
| 800.0 | 0 | 0 | 64 | 4.0 | 4 | cluster_tree | 2134.43927 | tile_attention |
| 800.0 | 0 | 0 | 256 | 1.0 | 4 | cluster_tree | 2145.922982 | tile_attention |
| 800.0 | 0 | 0 | 256 | 2.0 | 4 | cluster_tree | 2154.344371 | cross_tile_reduction |
| 800.0 | 0 | 0 | 256 | 4.0 | 4 | cluster_tree | 2171.187149 | cross_tile_reduction |
| 800.0 | 0 | 16 | 0 | 1.0 | 16 | cluster_tree | 2144.391821 | tile_attention |
| 800.0 | 0 | 16 | 0 | 2.0 | 16 | cluster_tree | 2154.152976 | tile_attention |
| 800.0 | 0 | 16 | 0 | 4.0 | 16 | cluster_tree | 2173.675286 | tile_attention |
| 800.0 | 0 | 16 | 64 | 1.0 | 16 | cluster_tree | 2156.641114 | tile_attention |
| 800.0 | 0 | 16 | 64 | 2.0 | 16 | cluster_tree | 2166.402269 | tile_attention |
| 800.0 | 0 | 16 | 64 | 4.0 | 16 | cluster_tree | 2185.924579 | tile_attention |
| 800.0 | 0 | 16 | 256 | 1.0 | 16 | cluster_tree | 2193.388992 | tile_attention |
| 800.0 | 0 | 16 | 256 | 2.0 | 16 | cluster_tree | 2203.150147 | tile_attention |
| 800.0 | 0 | 16 | 256 | 4.0 | 16 | cluster_tree | 2222.672458 | tile_attention |
| 800.0 | 0 | 64 | 0 | 1.0 | 32 | cluster_tree | 2208.892003 | tile_attention |
| 800.0 | 0 | 64 | 0 | 2.0 | 32 | cluster_tree | 2219.418739 | tile_attention |
| 800.0 | 0 | 64 | 0 | 4.0 | 32 | cluster_tree | 2240.472211 | tile_attention |
| 800.0 | 0 | 64 | 64 | 1.0 | 32 | cluster_tree | 2221.141296 | tile_attention |
| 800.0 | 0 | 64 | 64 | 2.0 | 32 | cluster_tree | 2231.668032 | tile_attention |
| 800.0 | 0 | 64 | 64 | 4.0 | 32 | cluster_tree | 2252.721504 | tile_attention |
| 800.0 | 0 | 64 | 256 | 1.0 | 32 | cluster_tree | 2257.889174 | tile_attention |
| 800.0 | 0 | 64 | 256 | 2.0 | 32 | cluster_tree | 2268.41591 | tile_attention |
| 800.0 | 0 | 64 | 256 | 4.0 | 32 | cluster_tree | 2289.469382 | tile_attention |
| 800.0 | 4 | 0 | 0 | 1.0 | 4 | cluster_tree | 2194.920154 | command_dispatch |
| 800.0 | 4 | 0 | 0 | 2.0 | 4 | cluster_tree | 2203.341542 | command_dispatch |
| 800.0 | 4 | 0 | 0 | 4.0 | 4 | cluster_tree | 2220.18432 | command_dispatch |
| 800.0 | 4 | 0 | 64 | 1.0 | 4 | cluster_tree | 2207.169446 | command_dispatch |
| 800.0 | 4 | 0 | 64 | 2.0 | 4 | cluster_tree | 2215.590835 | command_dispatch |
| 800.0 | 4 | 0 | 64 | 4.0 | 4 | cluster_tree | 2232.433613 | command_dispatch |
| 800.0 | 4 | 0 | 256 | 1.0 | 4 | cluster_tree | 2243.917325 | command_dispatch |
| 800.0 | 4 | 0 | 256 | 2.0 | 4 | cluster_tree | 2252.338714 | command_dispatch |
| 800.0 | 4 | 0 | 256 | 4.0 | 4 | cluster_tree | 2269.181491 | command_dispatch |
| 800.0 | 4 | 16 | 0 | 1.0 | 16 | cluster_tree | 2242.386163 | tile_attention |
| 800.0 | 4 | 16 | 0 | 2.0 | 16 | cluster_tree | 2252.147318 | tile_attention |
| 800.0 | 4 | 16 | 0 | 4.0 | 16 | cluster_tree | 2271.669629 | tile_attention |
| 800.0 | 4 | 16 | 64 | 1.0 | 16 | cluster_tree | 2254.635456 | tile_attention |
| 800.0 | 4 | 16 | 64 | 2.0 | 16 | cluster_tree | 2264.396611 | tile_attention |
| 800.0 | 4 | 16 | 64 | 4.0 | 16 | cluster_tree | 2283.918922 | tile_attention |
| 800.0 | 4 | 16 | 256 | 1.0 | 16 | cluster_tree | 2291.383334 | tile_attention |
| 800.0 | 4 | 16 | 256 | 2.0 | 16 | cluster_tree | 2301.14449 | tile_attention |
| 800.0 | 4 | 16 | 256 | 4.0 | 16 | cluster_tree | 2320.6668 | tile_attention |
| 800.0 | 4 | 64 | 0 | 1.0 | 32 | cluster_tree | 2306.886346 | tile_attention |
| 800.0 | 4 | 64 | 0 | 2.0 | 32 | cluster_tree | 2317.413082 | tile_attention |
| 800.0 | 4 | 64 | 0 | 4.0 | 32 | cluster_tree | 2338.466554 | tile_attention |
| 800.0 | 4 | 64 | 64 | 1.0 | 32 | cluster_tree | 2319.135638 | tile_attention |
| 800.0 | 4 | 64 | 64 | 2.0 | 32 | cluster_tree | 2329.662374 | tile_attention |
| 800.0 | 4 | 64 | 64 | 4.0 | 32 | cluster_tree | 2350.715846 | tile_attention |
| 800.0 | 4 | 64 | 256 | 1.0 | 32 | cluster_tree | 2355.883517 | tile_attention |
| 800.0 | 4 | 64 | 256 | 2.0 | 32 | cluster_tree | 2366.410253 | tile_attention |
| 800.0 | 4 | 64 | 256 | 4.0 | 32 | cluster_tree | 2387.463725 | tile_attention |
| 800.0 | 16 | 0 | 0 | 1.0 | 4 | cluster_tree | 2488.903181 | command_dispatch |
| 800.0 | 16 | 0 | 0 | 2.0 | 4 | cluster_tree | 2497.32457 | command_dispatch |
| 800.0 | 16 | 0 | 0 | 4.0 | 4 | cluster_tree | 2514.167347 | command_dispatch |
| 800.0 | 16 | 0 | 64 | 1.0 | 4 | cluster_tree | 2501.152474 | command_dispatch |
| 800.0 | 16 | 0 | 64 | 2.0 | 4 | cluster_tree | 2509.573862 | command_dispatch |
| 800.0 | 16 | 0 | 64 | 4.0 | 4 | cluster_tree | 2526.41664 | command_dispatch |
| 800.0 | 16 | 0 | 256 | 1.0 | 4 | cluster_tree | 2537.900352 | command_dispatch |
| 800.0 | 16 | 0 | 256 | 2.0 | 4 | cluster_tree | 2546.321741 | command_dispatch |
| 800.0 | 16 | 0 | 256 | 4.0 | 4 | cluster_tree | 2563.164518 | command_dispatch |
| 800.0 | 16 | 16 | 0 | 1.0 | 16 | cluster_tree | 2536.36919 | command_dispatch |
| 800.0 | 16 | 16 | 0 | 2.0 | 16 | cluster_tree | 2546.130346 | command_dispatch |
| 800.0 | 16 | 16 | 0 | 4.0 | 16 | cluster_tree | 2565.652656 | command_dispatch |
| 800.0 | 16 | 16 | 64 | 1.0 | 16 | cluster_tree | 2548.618483 | command_dispatch |
| 800.0 | 16 | 16 | 64 | 2.0 | 16 | cluster_tree | 2558.379638 | command_dispatch |
| 800.0 | 16 | 16 | 64 | 4.0 | 16 | cluster_tree | 2577.901949 | command_dispatch |
| 800.0 | 16 | 16 | 256 | 1.0 | 16 | cluster_tree | 2585.366362 | command_dispatch |
| 800.0 | 16 | 16 | 256 | 2.0 | 16 | cluster_tree | 2595.127517 | command_dispatch |
| 800.0 | 16 | 16 | 256 | 4.0 | 16 | cluster_tree | 2614.649827 | command_dispatch |
| 800.0 | 16 | 64 | 0 | 1.0 | 32 | cluster_tree | 2600.869373 | tile_attention |
| 800.0 | 16 | 64 | 0 | 2.0 | 32 | cluster_tree | 2611.396109 | tile_attention |
| 800.0 | 16 | 64 | 0 | 4.0 | 32 | cluster_tree | 2632.449581 | tile_attention |
| 800.0 | 16 | 64 | 64 | 1.0 | 32 | cluster_tree | 2613.118666 | tile_attention |
| 800.0 | 16 | 64 | 64 | 2.0 | 32 | cluster_tree | 2623.645402 | tile_attention |
| 800.0 | 16 | 64 | 64 | 4.0 | 32 | cluster_tree | 2644.698874 | tile_attention |
| 800.0 | 16 | 64 | 256 | 1.0 | 32 | cluster_tree | 2649.866544 | tile_attention |
| 800.0 | 16 | 64 | 256 | 2.0 | 32 | cluster_tree | 2660.39328 | tile_attention |
| 800.0 | 16 | 64 | 256 | 4.0 | 32 | cluster_tree | 2681.446752 | tile_attention |
| 1200.0 | 0 | 0 | 0 | 1.0 | 8 | cluster_tree | 1399.864493 | tile_attention |
| 1200.0 | 0 | 0 | 0 | 2.0 | 8 | cluster_tree | 1406.37193 | tile_attention |
| 1200.0 | 0 | 0 | 0 | 4.0 | 2 | owner_cluster | 1418.621222 | cross_tile_reduction |
| 1200.0 | 0 | 0 | 64 | 1.0 | 8 | cluster_tree | 1412.113786 | tile_attention |
| 1200.0 | 0 | 0 | 64 | 2.0 | 8 | cluster_tree | 1418.621222 | tile_attention |
| 1200.0 | 0 | 0 | 64 | 4.0 | 2 | owner_cluster | 1430.870515 | cross_tile_reduction |
| 1200.0 | 0 | 0 | 256 | 1.0 | 8 | cluster_tree | 1448.861664 | tile_attention |
| 1200.0 | 0 | 0 | 256 | 2.0 | 8 | cluster_tree | 1455.369101 | tile_attention |
| 1200.0 | 0 | 0 | 256 | 4.0 | 2 | owner_cluster | 1467.618394 | cross_tile_reduction |
| 1200.0 | 0 | 16 | 0 | 1.0 | 32 | cluster_tree | 1418.238432 | tile_attention |
| 1200.0 | 0 | 16 | 0 | 2.0 | 32 | cluster_tree | 1426.085635 | tile_attention |
| 1200.0 | 0 | 16 | 0 | 4.0 | 32 | cluster_tree | 1441.780042 | tile_attention |
| 1200.0 | 0 | 16 | 64 | 1.0 | 32 | cluster_tree | 1430.487725 | tile_attention |
| 1200.0 | 0 | 16 | 64 | 2.0 | 32 | cluster_tree | 1438.334928 | tile_attention |
| 1200.0 | 0 | 16 | 64 | 4.0 | 32 | cluster_tree | 1454.029334 | tile_attention |
| 1200.0 | 0 | 16 | 256 | 1.0 | 32 | cluster_tree | 1467.235603 | tile_attention |
| 1200.0 | 0 | 16 | 256 | 2.0 | 32 | cluster_tree | 1475.082806 | tile_attention |
| 1200.0 | 0 | 16 | 256 | 4.0 | 32 | cluster_tree | 1490.777213 | tile_attention |
| 1200.0 | 0 | 64 | 0 | 1.0 | 32 | cluster_tree | 1454.98631 | tile_attention |
| 1200.0 | 0 | 64 | 0 | 2.0 | 32 | cluster_tree | 1462.833514 | tile_attention |
| 1200.0 | 0 | 64 | 0 | 4.0 | 32 | cluster_tree | 1478.52792 | tile_attention |
| 1200.0 | 0 | 64 | 64 | 1.0 | 32 | cluster_tree | 1467.235603 | tile_attention |
| 1200.0 | 0 | 64 | 64 | 2.0 | 32 | cluster_tree | 1475.082806 | tile_attention |
| 1200.0 | 0 | 64 | 64 | 4.0 | 32 | cluster_tree | 1490.777213 | tile_attention |
| 1200.0 | 0 | 64 | 256 | 1.0 | 32 | cluster_tree | 1503.983482 | tile_attention |
| 1200.0 | 0 | 64 | 256 | 2.0 | 32 | cluster_tree | 1511.830685 | tile_attention |
| 1200.0 | 0 | 64 | 256 | 4.0 | 32 | cluster_tree | 1527.525091 | tile_attention |
| 1200.0 | 4 | 0 | 0 | 1.0 | 8 | cluster_tree | 1497.858835 | command_dispatch |
| 1200.0 | 4 | 0 | 0 | 2.0 | 8 | cluster_tree | 1504.366272 | command_dispatch |
| 1200.0 | 4 | 0 | 0 | 4.0 | 2 | owner_cluster | 1516.615565 | command_dispatch |
| 1200.0 | 4 | 0 | 64 | 1.0 | 8 | cluster_tree | 1510.108128 | command_dispatch |
| 1200.0 | 4 | 0 | 64 | 2.0 | 8 | cluster_tree | 1516.615565 | command_dispatch |
| 1200.0 | 4 | 0 | 64 | 4.0 | 2 | owner_cluster | 1528.864858 | command_dispatch |
| 1200.0 | 4 | 0 | 256 | 1.0 | 8 | cluster_tree | 1546.856006 | command_dispatch |
| 1200.0 | 4 | 0 | 256 | 2.0 | 8 | cluster_tree | 1553.363443 | command_dispatch |
| 1200.0 | 4 | 0 | 256 | 4.0 | 2 | owner_cluster | 1565.612736 | command_dispatch |
| 1200.0 | 4 | 16 | 0 | 1.0 | 32 | cluster_tree | 1516.232774 | tile_attention |
| 1200.0 | 4 | 16 | 0 | 2.0 | 32 | cluster_tree | 1524.079978 | tile_attention |
| 1200.0 | 4 | 16 | 0 | 4.0 | 32 | cluster_tree | 1539.774384 | tile_attention |
| 1200.0 | 4 | 16 | 64 | 1.0 | 32 | cluster_tree | 1528.482067 | tile_attention |
| 1200.0 | 4 | 16 | 64 | 2.0 | 32 | cluster_tree | 1536.32927 | tile_attention |
| 1200.0 | 4 | 16 | 64 | 4.0 | 32 | cluster_tree | 1552.023677 | tile_attention |
| 1200.0 | 4 | 16 | 256 | 1.0 | 32 | cluster_tree | 1565.229946 | tile_attention |
| 1200.0 | 4 | 16 | 256 | 2.0 | 32 | cluster_tree | 1573.077149 | tile_attention |
| 1200.0 | 4 | 16 | 256 | 4.0 | 32 | cluster_tree | 1588.771555 | tile_attention |
| 1200.0 | 4 | 64 | 0 | 1.0 | 32 | cluster_tree | 1552.980653 | tile_attention |
| 1200.0 | 4 | 64 | 0 | 2.0 | 32 | cluster_tree | 1560.827856 | tile_attention |
| 1200.0 | 4 | 64 | 0 | 4.0 | 32 | cluster_tree | 1576.522262 | tile_attention |
| 1200.0 | 4 | 64 | 64 | 1.0 | 32 | cluster_tree | 1565.229946 | tile_attention |
| 1200.0 | 4 | 64 | 64 | 2.0 | 32 | cluster_tree | 1573.077149 | tile_attention |
| 1200.0 | 4 | 64 | 64 | 4.0 | 32 | cluster_tree | 1588.771555 | tile_attention |
| 1200.0 | 4 | 64 | 256 | 1.0 | 32 | cluster_tree | 1601.977824 | tile_attention |
| 1200.0 | 4 | 64 | 256 | 2.0 | 32 | cluster_tree | 1609.825027 | tile_attention |
| 1200.0 | 4 | 64 | 256 | 4.0 | 32 | cluster_tree | 1625.519434 | tile_attention |
| 1200.0 | 16 | 0 | 0 | 1.0 | 8 | cluster_tree | 1791.841862 | command_dispatch |
| 1200.0 | 16 | 0 | 0 | 2.0 | 8 | cluster_tree | 1798.349299 | command_dispatch |
| 1200.0 | 16 | 0 | 0 | 4.0 | 2 | owner_cluster | 1810.598592 | command_dispatch |
| 1200.0 | 16 | 0 | 64 | 1.0 | 8 | cluster_tree | 1804.091155 | command_dispatch |
| 1200.0 | 16 | 0 | 64 | 2.0 | 8 | cluster_tree | 1810.598592 | command_dispatch |
| 1200.0 | 16 | 0 | 64 | 4.0 | 2 | owner_cluster | 1822.847885 | command_dispatch |
| 1200.0 | 16 | 0 | 256 | 1.0 | 8 | cluster_tree | 1840.839034 | command_dispatch |
| 1200.0 | 16 | 0 | 256 | 2.0 | 8 | cluster_tree | 1847.34647 | command_dispatch |
| 1200.0 | 16 | 0 | 256 | 4.0 | 2 | owner_cluster | 1859.595763 | command_dispatch |
| 1200.0 | 16 | 16 | 0 | 1.0 | 32 | cluster_tree | 1810.215802 | command_dispatch |
| 1200.0 | 16 | 16 | 0 | 2.0 | 32 | cluster_tree | 1818.063005 | command_dispatch |
| 1200.0 | 16 | 16 | 0 | 4.0 | 32 | cluster_tree | 1833.757411 | command_dispatch |
| 1200.0 | 16 | 16 | 64 | 1.0 | 32 | cluster_tree | 1822.465094 | command_dispatch |
| 1200.0 | 16 | 16 | 64 | 2.0 | 32 | cluster_tree | 1830.312298 | command_dispatch |
| 1200.0 | 16 | 16 | 64 | 4.0 | 32 | cluster_tree | 1846.006704 | command_dispatch |
| 1200.0 | 16 | 16 | 256 | 1.0 | 32 | cluster_tree | 1859.212973 | command_dispatch |
| 1200.0 | 16 | 16 | 256 | 2.0 | 32 | cluster_tree | 1867.060176 | command_dispatch |
| 1200.0 | 16 | 16 | 256 | 4.0 | 32 | cluster_tree | 1882.754582 | command_dispatch |
| 1200.0 | 16 | 64 | 0 | 1.0 | 32 | cluster_tree | 1846.96368 | command_dispatch |
| 1200.0 | 16 | 64 | 0 | 2.0 | 32 | cluster_tree | 1854.810883 | command_dispatch |
| 1200.0 | 16 | 64 | 0 | 4.0 | 32 | cluster_tree | 1870.50529 | command_dispatch |
| 1200.0 | 16 | 64 | 64 | 1.0 | 32 | cluster_tree | 1859.212973 | command_dispatch |
| 1200.0 | 16 | 64 | 64 | 2.0 | 32 | cluster_tree | 1867.060176 | command_dispatch |
| 1200.0 | 16 | 64 | 64 | 4.0 | 32 | cluster_tree | 1882.754582 | command_dispatch |
| 1200.0 | 16 | 64 | 256 | 1.0 | 32 | cluster_tree | 1895.960851 | command_dispatch |
| 1200.0 | 16 | 64 | 256 | 2.0 | 32 | cluster_tree | 1903.808054 | command_dispatch |
| 1200.0 | 16 | 64 | 256 | 4.0 | 32 | cluster_tree | 1919.502461 | command_dispatch |

## Best By Measured L1 Profile

| die | L1 profile | logic used um2 | replicas | clusters | reduction | latency us | resource |
|---:|---|---:|---:|---:|---|---:|---|
| 800.0 | hd64_kv8_full_value_p8_ppc2_noc128_softmax_int8_q10 | 399740704.5411 | 861 | 4 | cluster_tree | 2096.925811 | tile_attention |
| 1200.0 | hd64_kv8_full_value_p8_ppc2_noc128_softmax_int8_q10 | 599767215.0822 | 1291 | 8 | cluster_tree | 1399.864493 | tile_attention |

## Best By Die And Cluster

| die | clusters | arch | replicas | reduction | tile waves | tile service | reduction cycles | latency us | resource |
|---:|---:|---|---:|---|---:|---:|---:|---:|---|
| 800.0 | 1 | dense_gemm_16x8_k1_p1 | 864 | centralized_tile | 128 | 84 | 39 | 2132.054266 | tile_attention |
| 800.0 | 2 | dense_gemm_16x8_k1_p1 | 862 | owner_cluster | 64 | 169 | 42 | 2114.91696 | tile_attention |
| 800.0 | 4 | dense_gemm_16x8_k1_p1 | 861 | cluster_tree | 32 | 335 | 44 | 2096.925811 | tile_attention |
| 800.0 | 8 | dense_gemm_16x8_k1_p1 | 859 | cluster_tree | 16 | 672 | 47 | 2103.624643 | tile_attention |
| 800.0 | 16 | dense_gemm_16x8_k1_p1 | 856 | cluster_tree | 8 | 1354 | 51 | 2119.893235 | tile_attention |
| 800.0 | 32 | dense_gemm_16x8_k1_p1 | 849 | cluster_tree | 4 | 2759 | 55 | 2159.894832 | tile_attention |
| 1200.0 | 1 | dense_gemm_16x8_k1_p1 | 1294 | centralized_tile | 128 | 57 | 26 | 1425.89424 | tile_attention |
| 1200.0 | 2 | dense_gemm_16x8_k1_p1 | 1294 | owner_cluster | 64 | 112 | 29 | 1401.96984 | tile_attention |
| 1200.0 | 4 | dense_gemm_16x8_k1_p1 | 1293 | cluster_tree | 32 | 224 | 31 | 1402.35263 | tile_attention |
| 1200.0 | 8 | dense_gemm_16x8_k1_p1 | 1291 | cluster_tree | 16 | 447 | 34 | 1399.864493 | tile_attention |
| 1200.0 | 16 | dense_gemm_16x8_k1_p1 | 1288 | cluster_tree | 8 | 897 | 37 | 1405.223558 | tile_attention |
| 1200.0 | 32 | dense_gemm_16x8_k1_p1 | 1281 | cluster_tree | 4 | 1794 | 41 | 1405.989139 | tile_attention |

## Assumptions

- One decode-token attention pass is split into sequence KV tiles.
- Tiles are statically assigned to active clusters by wave; each active cluster handles at most one tile per wave.
- Each tile produces softmax statistics and a partial value vector for the current token.
- Reduction strategies model cross-tile combination after tile service: centralized_tile sends every tile partial, owner_cluster and cluster_tree first reduce tiles locally per cluster.
- This is an analytic schedule model; it still does not model RTL command queues or cycle-accurate SRAM/NoC arbitration.
- Optional command and reducer overhead parameters are sensitivity knobs, not measured RTL/PPA.
- When measured L1 cost profiles are provided, their per-cluster tile/reducer, FIFO, and router area is subtracted from the logic budget before compute replicas are allocated.
- Measured L1 profile clock is combined by max() with measured compute-array clock; this is a conservative local macro proxy, not a full routed SoC timing closure.
- Measured L1 profiles charge the local tile/value datapath, optional softmax-weight generator, and memory/NoC primitives listed in the selected cost file; cycle-accurate SRAM/NoC arbitration remains an analytic service model.
