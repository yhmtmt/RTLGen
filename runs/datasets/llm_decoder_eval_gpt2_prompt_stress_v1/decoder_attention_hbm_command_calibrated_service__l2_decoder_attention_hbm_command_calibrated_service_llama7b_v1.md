# Llama7B HBM Command-Calibrated Service

## Decision

- decision: `hbm_command_calibrated_service_preserves_frontier`
- command_energy_scale: `6.484297689339423`
- previous_energy_family: `die400:kv8:gqa8:tt1024`
- command_calibrated_energy_family: `die400:kv8:gqa8:tt1024`
- any_row_hit_scenario_changes_energy_family: `False`

## Best Point

| candidate | latency us | throughput tok/s | energy mJ | area mm2 | dominant energy | row hit |
|---|---:|---:|---:|---:|---|---:|
| die400_kv8_gqa8_lat66.432_hbm0.266583_dt6400_eff0.35_tt1024 | 105.37783453568113 | 9489.661695993555 | 11.522041553338012 | 400.0 | hbm | 0.9 |

## Row-Hit Scenarios

| row hit | latency best | energy best | energy mJ | dominant energy |
|---:|---|---|---:|---|
| 0.5 | die400_kv8_gqa8_lat66.432_hbm0.266583_dt6400_eff0.35_tt1024 | die400_kv8_gqa8_lat66.432_hbm0.266583_dt6400_eff0.35_tt1024 | 18.151705265775963 | hbm |
| 0.7 | die400_kv8_gqa8_lat66.432_hbm0.266583_dt6400_eff0.35_tt1024 | die400_kv8_gqa8_lat66.432_hbm0.266583_dt6400_eff0.35_tt1024 | 14.836863683110453 | hbm |
| 0.9 | die400_kv8_gqa8_lat66.432_hbm0.266583_dt6400_eff0.35_tt1024 | die400_kv8_gqa8_lat66.432_hbm0.266583_dt6400_eff0.35_tt1024 | 11.522041553338012 | hbm |
| 0.95 | die400_kv8_gqa8_lat66.432_hbm0.266583_dt6400_eff0.35_tt1024 | die400_kv8_gqa8_lat66.432_hbm0.266583_dt6400_eff0.35_tt1024 | 10.693326294448369 | hbm |

## Remaining Abstractions
- HBM command-class terms are globally scaled to an aggregate source pJ/bit anchor; this is not vendor stack-current signoff.
- Row-hit service sensitivity is analytic and reuses the existing HBM controller service model, not a cycle-accurate RTL controller.
- Compute energy remains scaled from the nearest measured dense compute reference.
- NoC/SRAM energy remains profile-scaled rather than routed switching or SRAM compiler signoff.
