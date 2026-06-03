# Decoder Attention/KV Compute Floor Gap

- model: `llm_decoder_attention_kv_compute_floor_gap_v1`
- best_measured_density_arch: `nm64_flat`
- best_measured_macs_per_cycle_per_mm2: `70.9436`
- max_measured_macs_per_cycle: `17024`
- min_hbm_floor_macs_per_cycle: `131072`
- all_measured_points_below_hbm_floor: `True`

## Gap By Die

| die | HBM floor MAC/cyc | measured MAC/cyc | measured arch | clusters | multiplier | target area frac @ measured density | measured resource |
|---:|---:|---:|---|---:|---:|---:|---|
| 400 | 131072 | 5632 | nm64_flat | 8 | 23.2727 | 4.61888 | tile_attention |
| 800 | 131072 | 11328 | nm64_flat | 1 | 11.5706 | 2.30944 | tile_attention |
| 1200 | 131072 | 17024 | nm64_flat | 2 | 7.69925 | 1.53963 | tile_attention |

## Target Sizing At Best Measured Density

| die | logic frac | target MAC/cyc | required density x | required compute area frac | fits |
|---:|---:|---:|---:|---:|---|
| 400 | 0.2 | 131072 | 23.0944 | 4.61888 | False |
| 400 | 0.2 | 262144 | 46.1888 | 9.23776 | False |
| 400 | 0.2 | 524288 | 92.3776 | 18.4755 | False |
| 400 | 0.4 | 131072 | 11.5472 | 4.61888 | False |
| 400 | 0.4 | 262144 | 23.0944 | 9.23776 | False |
| 400 | 0.4 | 524288 | 46.1888 | 18.4755 | False |
| 400 | 0.6 | 131072 | 7.69813 | 4.61888 | False |
| 400 | 0.6 | 262144 | 15.3963 | 9.23776 | False |
| 400 | 0.6 | 524288 | 30.7925 | 18.4755 | False |
| 800 | 0.2 | 131072 | 11.5472 | 2.30944 | False |
| 800 | 0.2 | 262144 | 23.0944 | 4.61888 | False |
| 800 | 0.2 | 524288 | 46.1888 | 9.23776 | False |
| 800 | 0.4 | 131072 | 5.7736 | 2.30944 | False |
| 800 | 0.4 | 262144 | 11.5472 | 4.61888 | False |
| 800 | 0.4 | 524288 | 23.0944 | 9.23776 | False |
| 800 | 0.6 | 131072 | 3.84907 | 2.30944 | False |
| 800 | 0.6 | 262144 | 7.69813 | 4.61888 | False |
| 800 | 0.6 | 524288 | 15.3963 | 9.23776 | False |
| 1200 | 0.2 | 131072 | 7.69813 | 1.53963 | False |
| 1200 | 0.2 | 262144 | 15.3963 | 3.07925 | False |
| 1200 | 0.2 | 524288 | 30.7925 | 6.15851 | False |
| 1200 | 0.4 | 131072 | 3.84907 | 1.53963 | False |
| 1200 | 0.4 | 262144 | 7.69813 | 3.07925 | False |
| 1200 | 0.4 | 524288 | 15.3963 | 6.15851 | False |
| 1200 | 0.6 | 131072 | 2.56604 | 1.53963 | False |
| 1200 | 0.6 | 262144 | 5.13209 | 3.07925 | False |
| 1200 | 0.6 | 524288 | 10.2642 | 6.15851 | False |

## Top Measured Compute Density Rows

| arch | MAC/cyc | area mm2 | clock ns | MAC/cyc/mm2 | metrics |
|---|---:|---:|---:|---:|---|
| nm64_flat | 64 | 0.902125 | 6.6331 | 70.9436 | `runs/designs/npu_blocks/npu_fp16_cpp_nm64_cmp/metrics.csv` |
| nm64_hier | 64 | 0.904046 | 6.7889 | 70.7929 | `runs/designs/npu_blocks/npu_fp16_cpp_nm64_cmp/metrics.csv` |
| nm32_flat | 32 | 0.731536 | 6.3103 | 43.7436 | `runs/designs/npu_blocks/npu_fp16_cpp_nm32_cmp/metrics.csv` |
| nm32_hier | 32 | 0.732854 | 6.3814 | 43.6649 | `runs/designs/npu_blocks/npu_fp16_cpp_nm32_cmp/metrics.csv` |
| nm16_flat | 16 | 0.647381 | 6.1518 | 24.715 | `runs/designs/npu_blocks/npu_fp16_cpp_nm16_cmp/metrics.csv` |
| nm16_hier | 16 | 0.64741 | 6.2277 | 24.7139 | `runs/designs/npu_blocks/npu_fp16_cpp_nm16_cmp/metrics.csv` |
| nm8_flat | 8 | 0.60446 | 5.9453 | 13.235 | `runs/designs/npu_blocks/npu_fp16_cpp_nm8_cmp/metrics.csv` |
| nm4_flat | 4 | 0.582822 | 5.9724 | 6.86316 | `runs/designs/npu_blocks/npu_fp16_cpp_nm4_cmp/metrics.csv` |
| nm4_hier | 4 | 0.583087 | 6.3871 | 6.86004 | `runs/designs/npu_blocks/npu_fp16_cpp_nm4_cmp/metrics.csv` |
| nm2_flat | 2 | 0.571595 | 5.9136 | 3.49898 | `runs/designs/npu_blocks/npu_fp16_cpp_nm2_cmp/metrics.csv` |

## Assumptions

- The HBM floor comes from the merged physical HBM compute-sensitivity planning model.
- Measured compute rows come from merged NPU compute PPA and measured-compute partition reports.
- Density is reported as MAC/cycle per mm2 of measured compute block area; it is not a replacement for routed large-array timing closure.
- A target that fails at best measured density should be treated as a compute-architecture gap before requesting detailed global NoC simulation.
