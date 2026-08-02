# Quality Gate

- microarchitecture profile must remain `score32_online_exact_partial_pair_merge_folded_sharedscale_v1`
- numerical semantics must remain `score32_online_exact_partial_pair_merge_v1`
- the folded schedule and service latency contract must remain unchanged
- `scale_divider_impl = mersenne24_correction2_exact` must forbid raw generic `/ 16777215` division in generated RTL
- the explicit divider must preserve exact signed and unsigned saturation behavior
