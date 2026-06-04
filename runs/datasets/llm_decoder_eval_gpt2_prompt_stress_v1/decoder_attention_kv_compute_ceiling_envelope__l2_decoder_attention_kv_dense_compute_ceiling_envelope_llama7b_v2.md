# Decoder Attention/KV Compute Ceiling Envelope

- model: `llm_decoder_attention_kv_compute_ceiling_envelope_v1`
- measured_best_density: `270.286` MAC/cycle/mm2
- measured_best_density_label: `rtlgen_npu_dense_gemm_tile_fp16_8x8_k1_p1_nangate45`
- measured_best_density_source: `rtlgen_npu_dense_gemm_tile_fp16_8x8_k1_p1_nangate45`
- hbm_floor_reachable_row_count: `4`
- best_latency_under_any_envelope_us: `280.032`

## Registry Evidence

Internal measurements:
- `rtlgen_llama7b_attention_kv_compute_floor_gap_v1`
- `rtlgen_npu_dense_gemm_tile_fp16_8x8_k1_p1_nangate45`
- `rtlgen_npu_fp16_nm64_flat_cmp33_nangate45`

External references:
- `diannao_asplos2014_peak_density`
- `tpu_v1_isca2017_peak_density_upper_bound`
- `eyeriss_isscc2016_peak_density`
- `eie_isca2016_sparse_fc_density`

Comparison claims:
- `rtlgen_dense_gemm_tile_improves_compute_density_v1`
- `rtlgen_llama7b_compute_density_gap_vs_external_refs_v1`

## Envelope Frontier

| die | logic frac | density label | ceiling MAC/cyc | HBM floor MAC/cyc | reaches HBM | selected MAC/cyc | latency us | resource |
|---:|---:|---|---:|---:|---|---:|---:|---|
| 400 | 0.2 | rtlgen_measured_best | 21622 | 131072 | False |  |  |  |
| 400 | 0.2 | density_150_mac_per_cycle_per_mm2 | 12000 | 131072 | False |  |  |  |
| 400 | 0.2 | density_300_mac_per_cycle_per_mm2 | 24000 | 131072 | False |  |  |  |
| 400 | 0.4 | rtlgen_measured_best | 43245 | 131072 | False | 32768 | 1081.63 | tile_attention |
| 400 | 0.4 | density_150_mac_per_cycle_per_mm2 | 24000 | 131072 | False |  |  |  |
| 400 | 0.4 | density_300_mac_per_cycle_per_mm2 | 48000 | 131072 | False | 32768 | 1081.63 | tile_attention |
| 400 | 0.6 | rtlgen_measured_best | 64868 | 131072 | False | 32768 | 1081.63 | tile_attention |
| 400 | 0.6 | density_150_mac_per_cycle_per_mm2 | 36000 | 131072 | False | 32768 | 1081.63 | tile_attention |
| 400 | 0.6 | density_300_mac_per_cycle_per_mm2 | 72000 | 131072 | False | 65536 | 547.104 | tile_attention |
| 800 | 0.2 | rtlgen_measured_best | 43245 | 131072 | False | 32768 | 1081.82 | tile_attention |
| 800 | 0.2 | density_150_mac_per_cycle_per_mm2 | 24000 | 131072 | False |  |  |  |
| 800 | 0.2 | density_300_mac_per_cycle_per_mm2 | 48000 | 131072 | False | 32768 | 1081.82 | tile_attention |
| 800 | 0.4 | rtlgen_measured_best | 86491 | 131072 | False | 65536 | 547.296 | tile_attention |
| 800 | 0.4 | density_150_mac_per_cycle_per_mm2 | 48000 | 131072 | False | 32768 | 1081.82 | tile_attention |
| 800 | 0.4 | density_300_mac_per_cycle_per_mm2 | 96000 | 131072 | False | 65536 | 547.296 | tile_attention |
| 800 | 0.6 | rtlgen_measured_best | 129737 | 131072 | False | 65536 | 547.296 | tile_attention |
| 800 | 0.6 | density_150_mac_per_cycle_per_mm2 | 72000 | 131072 | False | 65536 | 547.296 | tile_attention |
| 800 | 0.6 | density_300_mac_per_cycle_per_mm2 | 144000 | 131072 | True | 131072 | 280.032 | hbm |
| 1200 | 0.2 | rtlgen_measured_best | 64868 | 131072 | False | 32768 | 1082.02 | tile_attention |
| 1200 | 0.2 | density_150_mac_per_cycle_per_mm2 | 36000 | 131072 | False | 32768 | 1082.02 | tile_attention |
| 1200 | 0.2 | density_300_mac_per_cycle_per_mm2 | 72000 | 131072 | False | 65536 | 547.488 | tile_attention |
| 1200 | 0.4 | rtlgen_measured_best | 129737 | 131072 | False | 65536 | 547.488 | tile_attention |
| 1200 | 0.4 | density_150_mac_per_cycle_per_mm2 | 72000 | 131072 | False | 65536 | 547.488 | tile_attention |
| 1200 | 0.4 | density_300_mac_per_cycle_per_mm2 | 144000 | 131072 | True | 131072 | 280.224 | hbm |
| 1200 | 0.6 | rtlgen_measured_best | 194606 | 131072 | True | 131072 | 280.224 | hbm |
| 1200 | 0.6 | density_150_mac_per_cycle_per_mm2 | 108000 | 131072 | False | 65536 | 547.488 | tile_attention |
| 1200 | 0.6 | density_300_mac_per_cycle_per_mm2 | 216000 | 131072 | True | 131072 | 280.224 | hbm |

## External Density References

| measurement | 45nm-scaled MAC/cyc/mm2 | comparability |
|---|---:|---|
| `diannao_asplos2014_peak_density` | 171.335 | same_compute_class_different_workload |
| `tpu_v1_isca2017_peak_density_upper_bound` | 76.6554 | system_context_only |
| `eyeriss_isscc2016_peak_density` | 28.5811 | same_compute_class_different_workload |
| `eie_isca2016_sparse_fc_density` | 1.5674 | system_context_only |

## Assumptions

- Compute ceilings are calculated as die_area_mm2 * logic_area_fraction * density_envelope.
- The selected latency is taken from the merged compute-sensitivity sweep row whose MAC/cycle does not exceed the ceiling.
- External density rows are calibration references, not direct ranking baselines.
- Ideal node scaling is optimistic and does not include routing, voltage, SRAM, timing, or workload-utilization effects.
