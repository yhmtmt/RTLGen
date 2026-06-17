# Llama7B Dual-Stream Physical Feasibility

- decision: `dual_stream_feasible`
- precision profile: `q8_k8_v6_a24_s8_w8_recip_lut_q10_int8_compute`
- source rows used: `3`
- physical feasible rows: `3`
- best requested mode: `dual_mac`
- best requested latency us: `1575.373891`
- best requested logic slack um2: `168128417.0692`
- best requested compute area over budget um2: `0.0`
- best requested required compute density gain: `0.579174`
- best requested compute substitution: `True`
- best requested substituted compute arch: `attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q10`
- best requested substituted compute area um2: `231391215.0`
- recommended next step: `promote dual-stream schedule into a measured RTL/PPA wrapper`

## Best Requested

| mode | latency us | speedup | area fit | buffer fit | logic slack um2 | area over budget | density gain | required replicas | budget replicas | req buffer bytes |
|---|---:|---:|---|---|---:|---:|---:|---:|---:|---:|
| dual_mac | 1575.373891 | 1.357672 | True | True | 168128417.0692 | 0.0 | 0.579174 | 855 | 1476 | 532608 |

## Rows

| mode | latency us | area fit | feasible | logic slack um2 | local datapath/cluster | compute area required |
|---|---:|---|---|---:|---:|---:|
| dual_mac | 1575.373891 | True | True | 168128417.0692 | 0.0 | 231391215.0 |
| split_mac | 2042.378179 | True | True | 168128417.0692 | 0.0 | 231391215.0 |
| shared_mac | 2141.903683 | True | True | 168128417.0692 | 0.0 | 231391215.0 |

## Assumptions

- The dual_mac schedule requires an explicit compute_area_multiplier from the sub-tile scheduler.
- Measured full-value tile and softmax-weight generator PPA are used for local datapath overhead only.
- The dense GEMM compute array is treated as already packed into the current logic budget; extra dual-stream compute must fit that same budget to be feasible.
- Buffer capacity is checked against measured local SRAM bytes; an optional buffer-area proxy can be added for sensitivity but defaults to zero to avoid double-counting measured local SRAM.
- When composed dual-stream wrapper substitution is enabled, full-value and softmax measurements are treated as folded into the measured dual-stream RTL wrapper, and wrapper clock is used to scale feasible latency if it differs from source schedule clock.
