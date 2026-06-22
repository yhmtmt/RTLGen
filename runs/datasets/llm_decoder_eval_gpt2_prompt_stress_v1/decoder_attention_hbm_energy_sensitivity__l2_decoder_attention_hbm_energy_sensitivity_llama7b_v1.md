# Llama7B HBM Energy Sensitivity

## Decision

- decision: `hbm_energy_sensitivity_changes_energy_optimum`
- nominal_hbm_energy_pj_per_byte: `8.0`
- energy_changes_frontier: `True`

## Nominal Bests

| role | candidate | latency us | throughput tok/s | energy mJ | area mm2 | hbm share | dominant energy |
|---|---|---:|---:|---:|---:|---:|---|
| latency | die100_kv8_gqa8_lat30.944_hbm0.816646_dt9000_eff0.75_tt512 | 30.944 | 32316.442605997934 | 8.14357724928343 | 100.0 | 0.816646 | hbm |
| energy | die400_kv8_gqa8_lat66.432_hbm0.266583_dt6400_eff0.75_tt1024 | 66.432 | 15052.986512524085 | 4.719907157640776 | 400.0 | 0.266583 | compute |

## Sweep Summary

| hbm pJ/B | latency best | energy best | energy best mJ | energy best area | pareto rows |
|---:|---|---|---:|---:|---:|
| 1.0 | die100_kv8_gqa8_lat30.944_hbm0.816646_dt9000_eff0.75_tt512 | die200_kv8_gqa8_lat34.4_hbm0.633292_dt6400_eff0.75_tt512 | 1.9382528613053847 | 200.0 | 4 |
| 2.0 | die100_kv8_gqa8_lat30.944_hbm0.816646_dt9000_eff0.75_tt512 | die200_kv8_gqa8_lat34.4_hbm0.633292_dt6400_eff0.75_tt512 | 2.6182449685099924 | 200.0 | 4 |
| 4.0 | die100_kv8_gqa8_lat30.944_hbm0.816646_dt9000_eff0.75_tt512 | die400_kv8_gqa8_lat66.432_hbm0.266583_dt6400_eff0.75_tt1024 | 3.5749418909712074 | 400.0 | 10 |
| 8.0 | die100_kv8_gqa8_lat30.944_hbm0.816646_dt9000_eff0.75_tt512 | die400_kv8_gqa8_lat66.432_hbm0.266583_dt6400_eff0.75_tt1024 | 4.719907157640776 | 400.0 | 10 |
| 16.0 | die100_kv8_gqa8_lat30.944_hbm0.816646_dt9000_eff0.75_tt512 | die400_kv8_gqa8_lat66.432_hbm0.266583_dt6400_eff0.75_tt1024 | 7.0098376909799125 | 400.0 | 10 |
| 32.0 | die100_kv8_gqa8_lat30.944_hbm0.816646_dt9000_eff0.75_tt512 | die400_kv8_gqa8_lat66.432_hbm0.266583_dt6400_eff0.75_tt1024 | 11.589698757658185 | 400.0 | 10 |

## Remaining Abstractions
- HBM energy remains a pJ/byte sensitivity sweep rather than a DRAM command/current model.
- HBM timing still comes from the merged physical-HBM service frontier, not a cycle-accurate memory controller.
- Compute energy remains scaled from the nearest measured dense compute reference until the selected MAC/cycle point is measured.
- NoC and SRAM energy remain profile-scaled as in the integrated energy closure.
