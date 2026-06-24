# Llama7B Measured Compute Energy Closure

## Decision

- decision: `measured_compute_constraints_replace_abstract_frontier`
- abstract_compute_target_infeasible: `True`
- previous_energy_family: `die400:kv8:gqa8:tt1024`
- measured_energy_family: `die1200:kv8:gqa8:tt1024`

## Abstract Compute Feasibility

- target_macs_per_cycle: `524288.0`
- required_compute_area_mm2: `2036.641792`
- selected_die_area_mm2: `400.0`
- required_compute_area_over_die: `5.09160448`

## Best Measured-Compute-Constrained Point

| candidate | latency us | throughput tok/s | energy mJ | area mm2 | MAC/cyc | compute mJ | HBM mJ | dominant |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| die1200_dense_gemm_16x16_k1_p2_mac119808_lat2260.26_hbm0.465654_tt1024 | 95126.8919364575 | 10.512274496132768 | 82.92581224371085 | 1200.0 | 119808 | 19.357784498426398 | 63.520046663430314 | hbm |

## Pareto Rows

| candidate | latency us | energy mJ | area mm2 | MAC/cyc | dominant |
|---|---:|---:|---:|---:|---|
| die1200_dense_gemm_16x16_k1_p1_mac123392_lat2142.63_hbm0.465654_tt1024 | 88751.92761149416 | 85.56550819224147 | 1200.0 | 123392 | hbm |
| die1200_dense_gemm_16x16_k1_p2_mac119808_lat2260.26_hbm0.465654_tt1024 | 95126.8919364575 | 82.92581224371085 | 1200.0 | 119808 | hbm |
| die800_dense_gemm_16x16_k1_p1_mac82176_lat3222.05_hbm0.837019_tt1024 | 185024.64055690364 | 136.22247158193582 | 800.0 | 82176 | hbm |
| die800_dense_gemm_16x16_k1_p2_mac79872_lat3384.69_hbm0.837019_tt1024 | 197504.33143906217 | 133.5175802049352 | 800.0 | 79872 | hbm |
| die400_dense_gemm_16x16_k1_p1_mac40960_lat6414.78_hbm0.918509_tt1024 | 368365.936578397 | 147.16262763441978 | 400.0 | 40960 | hbm |
| die800_dense_gemm_16x16_k1_p1_mac40960_lat6416.03_hbm0.755528_tt1024 | 368437.56827419467 | 124.94936687518097 | 800.0 | 40960 | hbm |
| die400_dense_gemm_16x16_k1_p2_mac39936_lat6712.53_hbm0.918509_tt1024 | 391691.64561347925 | 144.46398789603256 | 400.0 | 39936 | hbm |
| die200_dense_gemm_16x16_k1_p1_mac20480_lat12827.5_hbm0.959255_tt512 | 736612.4870162726 | 152.71424679779057 | 200.0 | 20480 | hbm |
| die400_dense_gemm_16x16_k1_p1_mac20480_lat12827.9_hbm0.877764_tt512 | 736636.3642673468 | 141.60613120683712 | 400.0 | 20480 | hbm |
| die800_dense_gemm_16x16_k1_p1_mac20480_lat12828.3_hbm0.755528_tt512 | 736660.2414609963 | 124.94367171522097 | 800.0 | 20480 | hbm |
| die800_dense_gemm_16x16_k1_p1_mac20480_lat12828.5_hbm0.694410_tt512 | 736672.1800865333 | 116.61244197026492 | 800.0 | 20480 | hbm |
| die200_dense_gemm_16x16_k1_p2_mac19968_lat13395.9_hbm0.959255_tt1024 | 781681.6244010826 | 149.97684236290675 | 200.0 | 19968 | hbm |
| die100_dense_gemm_16x16_k1_p1_mac10240_lat25654.1_hbm0.963329_tt512 | 1473177.2195878217 | 153.26890450210837 | 100.0 | 10240 | hbm |
| die200_dense_gemm_16x16_k1_p1_mac10240_lat25654.3_hbm0.908323_tt512 | 1473189.1582133588 | 145.77068329025514 | 200.0 | 10240 | hbm |
| die400_dense_gemm_16x16_k1_p1_mac10240_lat25654.5_hbm0.847205_tt512 | 1473201.0967814713 | 137.43927641279507 | 400.0 | 10240 | hbm |
| die800_dense_gemm_16x16_k1_p1_mac10240_lat25655.2_hbm0.694410_tt512 | 1473236.9126580823 | 116.61084778710092 | 800.0 | 10240 | hbm |
| die100_dense_gemm_16x16_k1_p2_mac9984_lat26763.3_hbm0.979627_tt1024 | 1561698.5747219569 | 152.73358573038325 | 100.0 | 9984 | hbm |
| die100_dense_gemm_16x16_k1_p1_mac5120_lat51281_hbm0.954161_tt1024 | 2944790.48072333 | 152.00684231844613 | 100.0 | 5120 | hbm |
| die400_dense_gemm_16x16_k1_p1_mac5120_lat51281.9_hbm0.847205_tt1024 | 2944838.2351680533 | 137.42699272669105 | 400.0 | 5120 | hbm |
| die100_dense_gemm_16x16_k1_p1_mac2560_lat102534_hbm0.954161_tt1024 | 5887993.125743272 | 152.00095269655512 | 100.0 | 2560 | hbm |

## Remaining Abstractions
- Compute power is measured per dense tile and replicated to measured-compute capacity rows, not measured as one full integrated 400-1200 mm2 macro.
- Compute energy ranking assumes compute lanes can be clock gated during added HBM command-service stalls; wall-time compute-power energy is reported as an upper bound.
- HBM energy uses source-backed aggregate pJ/byte and the existing command-service latency model, not vendor stack-current signoff.
- NoC/SRAM energy remains profile-scaled rather than routed switching or SRAM compiler signoff.
- Quality remains native-GQA KV8 backed; KV4/MQA remain excluded until recovery evidence is sufficient.
