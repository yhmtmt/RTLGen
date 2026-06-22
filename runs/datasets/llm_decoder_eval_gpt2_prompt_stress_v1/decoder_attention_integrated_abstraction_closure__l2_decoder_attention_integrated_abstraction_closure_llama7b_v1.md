# Llama7B Integrated Abstraction Closure

## Selected Frontier
- arch_id: `physical_hbm_gqa8_kv8_service_frontier`
- latency_us: `30.944`
- token_throughput_per_s: `32316.442605997934`
- die_area_mm2: `100.0`
- kv: `gqa8 / 8b`
- dominant_resource: `hbm`
- energy_status: `full_integrated_energy_missing`

## Closure Flags
- q12_pwl_composed_datapath_measured: `True`
- q12_pwl_dual_stream_promotable: `False`
- native_7b_quality_available: `True`
- conservative_kv8_quality_backed: `True`
- kv4_promotable_without_recovery: `False`
- hbm_model_cycle_accurate: `False`
- integrated_energy_model_available: `False`

## Ranked Candidates
- `quality_backed_hbm_gqa8_kv8`: `current_selected_service_frontier`
- `q12_pwl_dual_stream_composed_datapath`: `blocked_not_promotable`

## Remaining Abstractions
- HBM/DRAM service is still an aggregate bandwidth/efficiency model, not cycle-accurate DRAM timing.
- NoC/SRAM contention in the selected HBM frontier is still a compact service model.
- Full Llama7B integrated energy is not yet composed from measured compute, SRAM, NoC, and HBM energy.
- Measured q12/PWL dual-stream composed datapath is available, but the current dual-stream frontier is blocked by area or clock and cannot be promoted.
- KV4 remains precision-risky without QAT, scale-granularity recovery, or a larger 7B-class confirmation.

## Recommended Next Jobs
- `integrated_energy_closure`: Token throughput and area are bounded, but full Llama7B energy is still not comparable across candidates.
- `hbm_noc_sram_service_detail`: The selected frontier is still HBM-service dominated and uses aggregate NoC/SRAM service assumptions.
- `kv4_recovery_or_larger_quality_confirmation`: KV4 has top-k stability but misses the cosine/KL caution line.
