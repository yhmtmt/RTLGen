# Llama7B HBM/DRAM Service Energy

## Decision

- decision: `hbm_dram_service_energy_preserves_energy_frontier`
- previous_hbm_sensitivity_energy_best: `die400_kv8_gqa8_lat66.432_hbm0.266583_dt6400_eff0.75_tt1024`
- hbm_dram_energy_best: `die400_kv8_gqa8_lat66.432_hbm0.266583_dt6400_eff0.35_tt1024`
- service_slowdown_vs_hbm_sensitivity_latency_best: `3.405436741716686`

## Best Points

| role | candidate | latency us | throughput tok/s | energy mJ | area mm2 | dominant energy |
|---|---|---:|---:|---:|---:|---|
| latency | die400_kv8_gqa8_lat66.432_hbm0.266583_dt6400_eff0.35_tt1024 | 105.37783453568113 | 9489.661695993555 | 3.8321431139716426 | 400.0 | compute |
| energy | die400_kv8_gqa8_lat66.432_hbm0.266583_dt6400_eff0.35_tt1024 | 105.37783453568113 | 9489.661695993555 | 3.8321431139716426 | 400.0 | compute |
| balanced | die400_kv8_gqa8_lat66.432_hbm0.266583_dt6400_eff0.35_tt1024 | 105.37783453568113 | 9489.661695993555 | 3.8321431139716426 | 400.0 | compute |

## DRAM Model Parameters

| parameter | value |
|---|---:|
| read_hit_pj_per_byte | 4.0 |
| read_miss_pj_per_byte | 10.0 |
| write_pj_per_byte | 6.0 |
| activate_precharge_pj_per_row | 3000.0 |
| command_pj_per_burst | 5.0 |
| noc_energy_pj_per_byte_hop | 0.02 |

## Pareto Rows

| candidate | latency us | energy mJ | area mm2 | service scale |
|---|---:|---:|---:|---:|
| die400_kv8_gqa8_lat66.432_hbm0.266583_dt6400_eff0.35_tt1024 | 105.37783453568113 | 3.8321431139716426 | 400.0 | 2.675003205670294 |
| die400_kv8_gqa8_lat66.432_hbm0.266583_dt3200_eff0.35_tt1024 | 105.37783453568113 | 3.8321431139716426 | 400.0 | 2.675003205670294 |
| die200_kv8_gqa8_lat48_hbm0.633292_dt9000_eff0.35_tt512 | 221.09232646888324 | 5.083068162241973 | 200.0 | 6.694198149934629 |
| die200_kv8_gqa8_lat43.84_hbm0.633292_dt6400_eff0.55_tt512 | 229.52794648090082 | 4.9319290390419726 | 200.0 | 7.688198683740625 |
| die200_kv8_gqa8_lat34.4_hbm0.633292_dt6400_eff0.75_tt512 | 241.00924210408263 | 4.588959490241972 | 200.0 | 10.483907296009942 |
| die100_kv8_gqa8_lat54.656_hbm0.816646_dt6400_eff0.55_tt512 | 353.1810982239275 | 6.285096916475597 | 100.0 | 7.688198683740625 |
| die100_kv8_gqa8_lat40.512_hbm0.816646_dt9000_eff0.55_tt512 | 355.45326935034154 | 5.771223897595597 | 100.0 | 10.519454235611562 |
| die100_kv8_gqa8_lat30.944_hbm0.816646_dt9000_eff0.75_tt512 | 368.16875081512563 | 5.4236039142355965 | 100.0 | 14.344710321288492 |

## Remaining Abstractions
- HBM/DRAM service is now command-class and row-hit aware, but still not a cycle-accurate controller simulation.
- HBM/DRAM energy parameters are explicit pJ values; they need source-backed stack-current calibration before final energy claims.
- Compute energy remains scaled from the nearest measured dense compute reference until the selected MAC/cycle point is measured.
- NoC/SRAM energy remains profile-scaled rather than routed switching or SRAM compiler signoff.
