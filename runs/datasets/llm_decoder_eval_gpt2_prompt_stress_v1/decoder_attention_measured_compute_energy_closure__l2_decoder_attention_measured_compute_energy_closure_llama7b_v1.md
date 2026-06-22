# Llama7B Measured Compute Energy Closure

## Decision

- decision: `measured_compute_constraints_replace_abstract_frontier`
- abstract_compute_target_infeasible: `True`
- previous_energy_family: `die400:kv8:gqa8:tt1024`
- measured_energy_family: `die1200:kv8:gqa8:tt512`

## Abstract Compute Feasibility

- target_macs_per_cycle: `524288.0`
- required_compute_area_mm2: `1888.64512`
- selected_die_area_mm2: `400.0`
- required_compute_area_over_die: `4.7216128`

## Best Measured-Compute-Constrained Point

| candidate | latency us | throughput tok/s | energy mJ | area mm2 | MAC/cyc | compute mJ | HBM mJ | dominant |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| die1200_dense_gemm_16x8_k1_p1_mac132736_lat1872.29_hbm0.465654_tt512 | 72544.06213406654 | 13.784725731954872 | 81.66413005453946 | 1200.0 | 132736 | 18.095420734855 | 63.520046663430314 | hbm |

## Pareto Rows

| candidate | latency us | energy mJ | area mm2 | MAC/cyc | dominant |
|---|---:|---:|---:|---:|---|
| die1200_dense_gemm_16x8_k1_p1_mac132480_lat1846.01_hbm0.465654_tt512 | 70539.86899822601 | 81.71957023676445 | 1200.0 | 132480 | hbm |
| die1200_dense_gemm_16x8_k1_p1_mac132736_lat1872.29_hbm0.465654_tt512 | 72544.06213406654 | 81.66413005453946 | 1200.0 | 132736 | hbm |
| die800_dense_gemm_16x8_k1_p1_mac88320_lat2742.31_hbm0.837019_tt1024 | 145188.65035710143 | 132.16821721986042 | 800.0 | 88320 | hbm |
| die800_dense_gemm_8x16_k1_p1_mac88832_lat2817.35_hbm0.837019_tt1024 | 153177.847335298 | 131.53537746156437 | 800.0 | 88832 | hbm |
| die400_dense_gemm_16x8_k1_p1_mac44160_lat5481.56_hbm0.918509_tt512 | 290215.1692923548 | 143.26754982526776 | 400.0 | 44160 | hbm |
| die800_dense_gemm_16x8_k1_p1_mac44160_lat5482.13_hbm0.755528_tt512 | 290245.5689471873 | 121.05191980440398 | 800.0 | 44160 | hbm |
| die400_dense_gemm_8x16_k1_p1_mac44416_lat5606.78_hbm0.918509_tt1024 | 304837.49445590633 | 142.5581189085565 | 400.0 | 44416 | hbm |
| die200_dense_gemm_16x8_k1_p1_mac22016_lat11011.5_hbm0.959255_tt512 | 582994.0410441192 | 148.84907839697854 | 200.0 | 22016 | hbm |
| die400_dense_gemm_16x8_k1_p1_mac22016_lat11011.9_hbm0.877764_tt512 | 583014.3074453783 | 137.74087975827712 | 400.0 | 22016 | hbm |
| die800_dense_gemm_16x8_k1_p1_mac22016_lat11012.5_hbm0.694410_tt512 | 583044.7071002107 | 112.74706595342093 | 800.0 | 22016 | hbm |
| die200_dense_gemm_8x16_k1_p1_mac22144_lat11237.4_hbm0.959255_tt1024 | 610968.6665285277 | 148.09937942875183 | 200.0 | 22144 | hbm |
| die100_dense_gemm_16x8_k1_p1_mac11008_lat21997.8_hbm0.979627_tt1024 | 1164650.4981756553 | 151.60485978779684 | 100.0 | 11008 | hbm |
| die200_dense_gemm_16x8_k1_p1_mac11008_lat21998.2_hbm0.938882_tt1024 | 1164670.7645769143 | 146.05082862826816 | 200.0 | 11008 | hbm |
| die400_dense_gemm_16x8_k1_p1_mac11008_lat21998.6_hbm0.877764_tt1024 | 1164691.0310311173 | 137.71955736025512 | 400.0 | 11008 | hbm |
| die400_dense_gemm_16x8_k1_p1_mac11008_lat21998.8_hbm0.847205_tt1024 | 1164701.164231747 | 133.55392172584007 | 400.0 | 11008 | hbm |
| die800_dense_gemm_16x8_k1_p1_mac11008_lat21999.9_hbm0.694410_tt1024 | 1164761.963488468 | 112.72589992429693 | 800.0 | 11008 | hbm |
| die100_dense_gemm_8x16_k1_p1_mac11008_lat22601.4_hbm0.979627_tt1024 | 1228822.6917496296 | 150.873411588181 | 100.0 | 11008 | hbm |
| die100_dense_gemm_16x8_k1_p1_mac5504_lat43945.9_hbm0.954161_tt1024 | 2326666.36143455 | 148.11301564688912 | 100.0 | 5504 | hbm |
| die200_dense_gemm_16x8_k1_p1_mac5504_lat43946.1_hbm0.923602_tt1024 | 2326676.4946351796 | 143.9473018276166 | 200.0 | 5504 | hbm |
| die400_dense_gemm_16x8_k1_p1_mac5504_lat43946.6_hbm0.847205_tt1024 | 2326706.8942370685 | 133.53312453168607 | 400.0 | 5504 | hbm |
| die100_dense_gemm_16x8_k1_p1_mac2688_lat89909.6_hbm0.954161_tt1024 | 4760167.16871196 | 148.0980968694136 | 100.0 | 2688 | hbm |
| die200_dense_gemm_16x8_k1_p1_mac2688_lat89909.8_hbm0.923602_tt1024 | 4760177.30191259 | 143.93234304858612 | 200.0 | 2688 | hbm |
| die100_dense_gemm_16x8_k1_p1_mac1280_lat188787_hbm0.954161_tt512 | 9995115.815804193 | 148.09656199162214 | 100.0 | 1280 | hbm |

## Remaining Abstractions
- Compute power is measured per dense tile and replicated to measured-compute capacity rows, not measured as one full integrated 400-1200 mm2 macro.
- Compute energy ranking assumes compute lanes can be clock gated during added HBM command-service stalls; wall-time compute-power energy is reported as an upper bound.
- HBM energy uses source-backed aggregate pJ/byte and the existing command-service latency model, not vendor stack-current signoff.
- NoC/SRAM energy remains profile-scaled rather than routed switching or SRAM compiler signoff.
- Quality remains native-GQA KV8 backed; KV4/MQA remain excluded until recovery evidence is sufficient.
