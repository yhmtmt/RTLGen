# Llama7B Integrated Energy Closure

## Selected Frontier
- arch_id: `physical_hbm_gqa8_kv8_service_frontier`
- latency_us: `30.944`
- token_throughput_per_s: `32316.442605997934`
- die_area_mm2: `100.0`
- energy_mj: `8.14357724928343`
- energy_status: `parameterized_integrated_energy_not_full_measurement`
- dominant_energy_component: `hbm`

## Energy Components

| component | status | energy_mj |
|---|---|---:|
| compute | parameterized_from_nearest_measured_compute_density | 1.12424255488 |
| hbm | parameterized_hbm_energy_per_byte | 7.014935724818432 |
| sram | profile_scaled_from_measured_cacti_sram_buffers | 0.00012002985704362652 |
| noc | parameterized_payload_byte_hop_energy | 0.00427893972795392 |

## Closure Flags
- integrated_energy_accounting_available: `True`
- full_measured_energy_available: `False`
- compute_energy_directly_measured_at_selected_point: `False`
- hbm_energy_parameterized: `True`
- noc_energy_parameterized: `True`
- sram_energy_profile_scaled: `True`

## Remaining Abstractions
- HBM energy uses an explicit pJ/byte sensitivity parameter, not a cycle-accurate DRAM timing/power model.
- NoC energy uses payload byte-hop accounting, not routed wire/switching simulation.
- SRAM energy scales CACTI macro access estimates by traffic bytes; it is not a placed SRAM compiler energy signoff.
- Selected 524288 MAC/cycle compute energy is scaled from the nearest measured dense compute reference, not directly measured at that service point.
