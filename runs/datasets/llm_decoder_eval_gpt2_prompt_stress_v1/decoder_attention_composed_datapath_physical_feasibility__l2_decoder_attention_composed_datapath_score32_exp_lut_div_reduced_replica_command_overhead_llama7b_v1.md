# Llama7B Dual-Stream Physical Feasibility

- decision: `dual_stream_feasible`
- precision profile: `q8_k8_v8_a32_s32_w16_exp_lut_div_b20_int8_compute`
- source rows used: `3`
- physical feasible rows: `36`
- best requested mode: `dual_mac`
- best requested latency us: `1575.373891`
- best requested logic slack um2: `109322.0692`
- best requested compute area over budget um2: `0.0`
- best requested required compute density gain: `0.999726`
- best requested compute substitution: `True`
- best requested substituted compute arch: `attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20`
- best requested substituted compute variant: `attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20`
- best requested substituted compute semantic profile: `score32_exp_lut_div`
- best requested substituted compute area um2: `399410310.0`
- best requested command dispatch control variant: `None`
- best requested command dispatch control area um2: `None`
- best requested command dispatch control clock ok: `True`
- recommended next step: `promote dual-stream schedule into a measured RTL/PPA wrapper`

## Best Requested

| mode | latency us | speedup | area fit | buffer fit | substituted variant | semantic profile | logic slack um2 | area over budget | density gain | required replicas | budget replicas | req buffer bytes |
|---|---:|---:|---|---|---|---|---:|---:|---:|---:|---:|---:|
| dual_mac | 1575.373891 | 1.357672 | True | True | attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20 | score32_exp_lut_div | 109322.0692 | 0.0 | 0.999726 | 815 | 815 | 532608 |

## Rows

| mode | latency us | area fit | feasible | substituted variant | semantic profile | command ctrl | logic slack um2 | local datapath/cluster | compute area required |
|---|---:|---|---|---|---|---|---:|---:|---:|
| dual_mac | 1575.373891 | True | True | attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20 | score32_exp_lut_div | None | 109322.0692 | 0.0 | 399410310.0 |
| dual_mac | 1587.623184 | True | True | attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20 | score32_exp_lut_div | None | 109322.0692 | 0.0 | 399410310.0 |
| dual_mac | 1624.371062 | True | True | attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20 | score32_exp_lut_div | None | 109322.0692 | 0.0 | 399410310.0 |
| dual_mac | 1599.872477 | True | True | attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20 | score32_exp_lut_div | None | 109322.0692 | 0.0 | 399410310.0 |
| dual_mac | 1612.12177 | True | True | attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20 | score32_exp_lut_div | None | 109322.0692 | 0.0 | 399410310.0 |
| dual_mac | 1648.869648 | True | True | attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20 | score32_exp_lut_div | None | 109322.0692 | 0.0 | 399410310.0 |
| dual_mac | 1673.368234 | True | True | attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20 | score32_exp_lut_div | None | 109322.0692 | 0.0 | 399410310.0 |
| dual_mac | 1685.617526 | True | True | attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20 | score32_exp_lut_div | None | 109322.0692 | 0.0 | 399410310.0 |
| dual_mac | 1722.365405 | True | True | attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20 | score32_exp_lut_div | None | 109322.0692 | 0.0 | 399410310.0 |
| dual_mac | 1967.351261 | True | True | attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20 | score32_exp_lut_div | None | 109322.0692 | 0.0 | 399410310.0 |
| dual_mac | 1979.600554 | True | True | attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20 | score32_exp_lut_div | None | 109322.0692 | 0.0 | 399410310.0 |
| dual_mac | 2016.348432 | True | True | attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20 | score32_exp_lut_div | None | 109322.0692 | 0.0 | 399410310.0 |
| split_mac | 2042.378179 | True | True | attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20 | score32_exp_lut_div | None | 109322.0692 | 0.0 | 399410310.0 |
| split_mac | 2054.627472 | True | True | attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20 | score32_exp_lut_div | None | 109322.0692 | 0.0 | 399410310.0 |
| split_mac | 2091.37535 | True | True | attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20 | score32_exp_lut_div | None | 109322.0692 | 0.0 | 399410310.0 |
| split_mac | 2066.876765 | True | True | attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20 | score32_exp_lut_div | None | 109322.0692 | 0.0 | 399410310.0 |
| split_mac | 2079.126058 | True | True | attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20 | score32_exp_lut_div | None | 109322.0692 | 0.0 | 399410310.0 |
| split_mac | 2115.873936 | True | True | attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20 | score32_exp_lut_div | None | 109322.0692 | 0.0 | 399410310.0 |
| split_mac | 2140.372522 | True | True | attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20 | score32_exp_lut_div | None | 109322.0692 | 0.0 | 399410310.0 |
| split_mac | 2152.621814 | True | True | attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20 | score32_exp_lut_div | None | 109322.0692 | 0.0 | 399410310.0 |
| split_mac | 2189.369693 | True | True | attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20 | score32_exp_lut_div | None | 109322.0692 | 0.0 | 399410310.0 |
| split_mac | 2434.355549 | True | True | attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20 | score32_exp_lut_div | None | 109322.0692 | 0.0 | 399410310.0 |
| split_mac | 2446.604842 | True | True | attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20 | score32_exp_lut_div | None | 109322.0692 | 0.0 | 399410310.0 |
| split_mac | 2483.35272 | True | True | attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20 | score32_exp_lut_div | None | 109322.0692 | 0.0 | 399410310.0 |
| shared_mac | 2141.903683 | True | True | attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20 | score32_exp_lut_div | None | 109322.0692 | 0.0 | 399410310.0 |
| shared_mac | 2154.152976 | True | True | attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20 | score32_exp_lut_div | None | 109322.0692 | 0.0 | 399410310.0 |
| shared_mac | 2190.900854 | True | True | attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20 | score32_exp_lut_div | None | 109322.0692 | 0.0 | 399410310.0 |
| shared_mac | 2166.402269 | True | True | attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20 | score32_exp_lut_div | None | 109322.0692 | 0.0 | 399410310.0 |
| shared_mac | 2178.651562 | True | True | attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20 | score32_exp_lut_div | None | 109322.0692 | 0.0 | 399410310.0 |
| shared_mac | 2215.39944 | True | True | attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20 | score32_exp_lut_div | None | 109322.0692 | 0.0 | 399410310.0 |
| shared_mac | 2239.898026 | True | True | attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20 | score32_exp_lut_div | None | 109322.0692 | 0.0 | 399410310.0 |
| shared_mac | 2252.147318 | True | True | attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20 | score32_exp_lut_div | None | 109322.0692 | 0.0 | 399410310.0 |
| shared_mac | 2288.895197 | True | True | attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20 | score32_exp_lut_div | None | 109322.0692 | 0.0 | 399410310.0 |
| shared_mac | 2533.881053 | True | True | attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20 | score32_exp_lut_div | None | 109322.0692 | 0.0 | 399410310.0 |
| shared_mac | 2546.130346 | True | True | attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20 | score32_exp_lut_div | None | 109322.0692 | 0.0 | 399410310.0 |
| shared_mac | 2582.878224 | True | True | attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20 | score32_exp_lut_div | None | 109322.0692 | 0.0 | 399410310.0 |

## Assumptions

- The dual_mac schedule requires an explicit compute_area_multiplier from the sub-tile scheduler.
- Measured full-value tile and softmax-weight generator PPA are used for local datapath overhead only.
- The dense GEMM compute array is treated as already packed into the current logic budget; extra dual-stream compute must fit that same budget to be feasible.
- Buffer capacity is checked against measured local SRAM bytes; an optional buffer-area proxy can be added for sensitivity but defaults to zero to avoid double-counting measured local SRAM.
- When composed dual-stream wrapper substitution is enabled, full-value and softmax measurements are treated as folded into the measured dual-stream RTL wrapper, and wrapper clock is used to scale feasible latency if it differs from source schedule clock.
