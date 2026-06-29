# Mixed-Int8 Quality/Energy Frontier Audit

- decision: `mixed_int8_quality_energy_frontier_composed_measurement_required`
- quality_best_candidate_id: `qkv8_float_exact`
- quality_best_top1_match_rate: `1.0`
- score32_top1_match_rate: `0.984375`
- q24_pwl_top1_match_rate: `0.96875`
- best_fp16_softmax_proxy_candidate_id: `qkv8_float_exact_fp16_softmax_nm2_proxy`
- best_fp16_softmax_proxy_critical_path_ns: `5.476841177082706`
- best_fp16_softmax_proxy_die_area_um2: `2250000.0`
- best_fp16_softmax_proxy_total_power_mw: `0.189074`

## Recommendation

Measure a composed q8/k8/v8 attention wrapper that keeps qkv8_float_exact quality semantics and substitutes a floating/near-exact softmax datapath; do not rank score32 exact-div or PWL rows as quality-backed frontier points.
