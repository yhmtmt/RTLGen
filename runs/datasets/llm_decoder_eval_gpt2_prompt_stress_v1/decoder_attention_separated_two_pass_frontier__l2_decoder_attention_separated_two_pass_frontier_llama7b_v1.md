# Separated Two-Pass Frontier

- decision: `score32_separated_two_pass_frontier_ranked`
- recommended candidate: `score32_separated_zero_tail_two_pass_nominal_per_head_iterdiv`
- recommended latency us: `1595.42090302109`
- minimum-area candidate: `score32_separated_zero_tail_two_pass_nominal_shared_iterdiv`
- quality status: `mixed_int8_generation_quality_pass`

| candidate | latency us | token/s | energy mJ/token | embodied logic + score macro mm2 |
|---|---:|---:|---:|---:|
| score32_separated_zero_tail_two_pass_nominal_per_head_iterdiv | 1595.42090302109 | 626.793843622331 | 137.330868813197 | 249.4256151009 |
| score32_separated_zero_tail_two_pass_conservative_per_head_iterdiv | 1600.407500163976 | 624.840860779233 | 137.755482392336 | 249.4256151009 |
| score32_separated_zero_tail_two_pass_nominal_shared_iterdiv | 1744.22090302109 | 573.32187584035 | 137.330868813197 | 245.8940641009 |
| score32_separated_zero_tail_two_pass_conservative_shared_iterdiv | 1749.207500163976 | 571.687464126616 | 137.755482392336 | 245.8940641009 |

## Assumptions

- The separated score32 recost supplies the baseline dense producer, dispatch, controller, NoC, and tile-SRAM costs.
- Score-SRAM integration transfers only the HBM-share scale ratio onto inherited latency and HBM energy; it does not reuse the slow wrapper's absolute latency.
- The old shared_score32_vector_softmax_overhead component is replaced by measured iterative two-pass service rather than stacked on top of it.
- Divider total active work energy is identical across per-head and shared deployments; only area, instantaneous power, and serialized latency change.
- Score SRAM raw macro area is reported separately from its placement envelope so the envelope is not double-counted as embodied silicon.
- Zero-tail quality pass is treated as the precision-aligned quality witness for the two-pass recost.
