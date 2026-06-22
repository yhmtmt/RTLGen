# Llama7B HBM Energy Calibration

## Decision

- decision: `hbm_energy_calibration_preserves_energy_frontier`
- primary_measurement_id: `hbm2_fgdram_micro2017_access_energy`
- previous_energy_family: `die400:kv8:gqa8:tt1024`
- calibrated_energy_family: `die400:kv8:gqa8:tt1024`
- dominant_energy_component_changed: `True`

## Best Point

| candidate | latency us | throughput tok/s | energy mJ | area mm2 | dominant energy | HBM pJ/bit |
|---|---:|---:|---:|---:|---|---:|
| die400_kv8_gqa8_lat66.432_hbm0.266583_dt6400_eff0.35_tt1024 | 105.37783453568113 | 9489.661695993555 | 11.522041553338012 | 400.0 | hbm | 3.97 |

## Calibration Sweeps

| measurement | HBM pJ/bit | energy best | energy mJ | dominant energy |
|---|---:|---|---:|---|
| hbm3_pawlowski_mchpc2019_projected_full_page_energy | 3.5 | die400_kv8_gqa8_lat66.432_hbm0.266583_dt6400_eff0.35_tt1024 | 10.445650994988616 | hbm |
| hbm2_fgdram_micro2017_access_energy | 3.97 | die400_kv8_gqa8_lat66.432_hbm0.266583_dt6400_eff0.35_tt1024 | 11.522041553338012 | hbm |
| hbm2e_pawlowski_mchpc2019_full_page_energy | 4.5 | die400_kv8_gqa8_lat66.432_hbm0.266583_dt6400_eff0.35_tt1024 | 12.735843672327752 | hbm |

## Remaining Abstractions
- HBM energy is calibrated from aggregate source pJ/bit references, not matched stack-current tables.
- The calibration preserves the HBM/DRAM service latency model but does not simulate a cycle-accurate controller.
- Compute energy remains scaled from the nearest measured dense compute reference until the selected MAC/cycle point is measured.
- NoC/SRAM energy remains profile-scaled rather than routed switching or SRAM compiler signoff.
