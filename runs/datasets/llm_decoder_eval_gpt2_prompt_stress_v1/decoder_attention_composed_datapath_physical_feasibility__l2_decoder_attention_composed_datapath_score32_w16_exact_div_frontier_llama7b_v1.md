# Llama7B Dual-Stream Physical Feasibility

- decision: `dual_stream_area_blocked`
- precision profile: `q8_k8_v8_a32_s32_w16_exact_div_int8_compute`
- source rows used: `3`
- physical feasible rows: `0`
- best requested mode: `dual_mac`
- best requested latency us: `1575.373891`
- best requested logic slack um2: `-26975519.9308`
- best requested compute area over budget um2: `26975519.9308`
- best requested required compute density gain: `1.06752`
- best requested compute substitution: `True`
- best requested substituted compute arch: `attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exact_div`
- best requested substituted compute variant: `attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exact_div`
- best requested substituted compute area um2: `426495152.0`
- recommended next step: `measure a denser dual-stream fused attention datapath or reduce compute replicas before promoting dual_mac`

## Best Requested

| mode | latency us | speedup | area fit | buffer fit | substituted variant | logic slack um2 | area over budget | density gain | required replicas | budget replicas | req buffer bytes |
|---|---:|---:|---|---|---|---:|---:|---:|---:|---:|---:|
| dual_mac | 1575.373891 | 1.357672 | False | True | attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exact_div | -26975519.9308 | 26975519.9308 | 1.06752 | 856 | 801 | 532608 |

## Rows

| mode | latency us | area fit | feasible | substituted variant | logic slack um2 | local datapath/cluster | compute area required |
|---|---:|---|---|---|---:|---:|---:|
| dual_mac | 1575.373891 | False | False | attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exact_div | -26975519.9308 | 0.0 | 426495152.0 |
| split_mac | 2042.378179 | False | False | attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exact_div | -26975519.9308 | 0.0 | 426495152.0 |
| shared_mac | 2141.903683 | False | False | attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exact_div | -26975519.9308 | 0.0 | 426495152.0 |

## Assumptions

- The dual_mac schedule requires an explicit compute_area_multiplier from the sub-tile scheduler.
- Measured full-value tile and softmax-weight generator PPA are used for local datapath overhead only.
- The dense GEMM compute array is treated as already packed into the current logic budget; extra dual-stream compute must fit that same budget to be feasible.
- Buffer capacity is checked against measured local SRAM bytes; an optional buffer-area proxy can be added for sensitivity but defaults to zero to avoid double-counting measured local SRAM.
- When composed dual-stream wrapper substitution is enabled, full-value and softmax measurements are treated as folded into the measured dual-stream RTL wrapper, and wrapper clock is used to scale feasible latency if it differs from source schedule clock.
