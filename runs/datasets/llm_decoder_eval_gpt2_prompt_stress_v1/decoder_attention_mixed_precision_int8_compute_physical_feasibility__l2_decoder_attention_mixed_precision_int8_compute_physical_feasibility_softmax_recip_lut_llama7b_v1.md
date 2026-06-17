# Llama7B Dual-Stream Physical Feasibility

- decision: `dual_stream_feasible`
- precision profile: `q8_k8_v6_a24_s8_w8_recip_lut_q10_int8_compute`
- source rows used: `3`
- physical feasible rows: `3`
- best requested mode: `dual_mac`
- best requested latency us: `1575.373891`
- best requested logic slack um2: `216801992.1716`
- best requested compute area over budget um2: `0.0`
- best requested required compute density gain: `0.452383`
- best requested compute substitution: `True`
- best requested substituted compute arch: `dense_gemm_int8_16x8_k1_p1`
- best requested substituted compute area um2: `89549280.0`
- recommended next step: `promote dual-stream schedule into a measured RTL/PPA wrapper`

## Best Requested

| mode | latency us | speedup | area fit | buffer fit | logic slack um2 | area over budget | density gain | required replicas | budget replicas | req buffer bytes |
|---|---:|---:|---|---|---:|---:|---:|---:|---:|---:|
| dual_mac | 1575.373891 | 1.357672 | True | True | 216801992.1716 | 0.0 | 0.452383 | 1710 | 3779 | 532608 |

## Rows

| mode | latency us | area fit | feasible | logic slack um2 | local datapath/cluster | compute area required |
|---|---:|---|---|---:|---:|---:|
| dual_mac | 1575.373891 | True | True | 216801992.1716 | 186416.18 | 179098560.0 |
| split_mac | 2042.378179 | True | True | 307842601.6116 | 93208.09 | 89549280.0 |
| shared_mac | 2141.903683 | True | True | 307842601.6116 | 93208.09 | 89549280.0 |

## Assumptions

- The dual_mac schedule requires an explicit compute_area_multiplier from the sub-tile scheduler.
- Measured full-value tile and softmax-weight generator PPA are used for local datapath overhead only.
- The dense GEMM compute array is treated as already packed into the current logic budget; extra dual-stream compute must fit that same budget to be feasible.
- Buffer capacity is checked against measured local SRAM bytes; an optional buffer-area proxy can be added for sensitivity but defaults to zero to avoid double-counting measured local SRAM.
- When compute-block substitution is enabled, measured block area/power/clock replace the source dense compute block, but the upstream schedule latency is not recomputed; this is an area-feasibility substitution and a conservative latency view when the substituted block clock is no slower than the source clock.
