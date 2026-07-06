# Score32 Integrated Frontier Ranking

- decision: `score32_integrated_frontier_best_precision_safe_throughput`
- best latency candidate: `physical_hbm_gqa8_kv8_service_frontier`
- best energy candidate: `physical_hbm_gqa8_kv8_service_frontier`
- best precision-safe throughput candidate: `score32_exp_lut_hbm_dram_service_closure_best`
- current recommended candidate: `score32_exp_lut_hbm_dram_service_closure_best`
- score32 latency us: `12532.357427`
- score32 total energy mJ/token: `494.831007886`
- score32 die area mm2: `800.0`
- score32 quality status: `mixed_int8_generation_quality_pass`

## Promotable Latency Rank

| candidate | latency us | token/s | energy mJ/token | area mm2 | precision |
|---|---:|---:|---:|---:|---|
| score32_exp_lut_hbm_dram_service_closure_best | 12532.357427 | 79.793447149 | 494.831007886 | 800.0 | mixed_int8_generation_quality_pass |
| die1200_dense_gemm_16x8_k1_p1_mac132736_lat1872.29_hbm0.465654_tt512 | 72544.06213406654 | 13.784725731954872 | 81.66413005453946 | 1200.0 | conservative_native_gqa8_kv8 |

## All Rows

| candidate | promotable | latency us | energy mJ/token | status |
|---|---:|---:|---:|---|
| physical_hbm_gqa8_kv8_service_frontier | False | 30.944 | 8.14357724928343 | abstract_compute_target_infeasible_after_measured_compute_closure |
| die800_dense_gemm_int8_16x8_k1_p1_rep855_lat1575.37_hbm0.983398_tt1024 | False | 1575.373891 | 135.75588466251537 | measured_int8_compute_with_source_backed_hbm_energy |
| score32_exp_lut_hbm_dram_service_closure_best | True | 12532.357427 | 494.831007886 | measured_wrapper_command_control_sram_envelope_hbm_command_service |
| die1200_dense_gemm_16x8_k1_p1_mac132736_lat1872.29_hbm0.465654_tt512 | True | 72544.06213406654 | 81.66413005453946 | measured_compute_with_source_backed_hbm_energy |

## Assumptions

- Rows are ranked by explicit metrics from merged evidence; no new PPA is synthesized in this audit.
- The score32 row is quality-backed by the bounded generation-quality gate and measured through wrapper, command-control, SRAM-envelope, and HBM/DRAM service closure.
- The mixed-int8 energy row is retained as a fast non-promotable latency candidate because its precision path is not promoted by the current real-checkpoint evidence.
- The older integrated-energy row is retained as planning-only because measured-compute closure made its abstract compute target infeasible.
