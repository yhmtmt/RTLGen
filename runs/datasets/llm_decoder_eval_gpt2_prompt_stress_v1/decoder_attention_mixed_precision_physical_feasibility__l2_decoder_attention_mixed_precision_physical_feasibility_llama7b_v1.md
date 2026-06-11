# Llama7B Dual-Stream Physical Feasibility

- decision: `dual_stream_area_blocked`
- precision profile: `q8_k8_v6_a24_s24_w16`
- source rows used: `3`
- physical feasible rows: `2`
- best requested mode: `dual_mac`
- best requested latency us: `1575.373891`
- best requested logic slack um2: `-397395735.8284`
- best requested compute area over budget um2: `397395735.8284`
- best requested required compute density gain: `2.003777`
- recommended next step: `measure a denser dual-stream fused attention datapath or reduce compute replicas before promoting dual_mac`

## Best Requested

| mode | latency us | speedup | area fit | buffer fit | logic slack um2 | area over budget | density gain | required replicas | budget replicas | req buffer bytes |
|---|---:|---:|---|---|---:|---:|---:|---:|---:|---:|
| dual_mac | 1575.373891 | 1.357672 | False | True | -397395735.8284 | 397395735.8284 | 2.003777 | 1712 | 856 | 532608 |

## Rows

| mode | latency us | area fit | feasible | logic slack um2 | local datapath/cluster | compute area required |
|---|---:|---|---|---:|---:|---:|
| dual_mac | 1575.373891 | False | False | -397395735.8284 | 186416.18 | 793296288.0 |
| split_mac | 2042.378179 | True | True | 743737.6116 | 93208.09 | 396648144.0 |
| shared_mac | 2141.903683 | True | True | 743737.6116 | 93208.09 | 396648144.0 |

## Assumptions

- The dual_mac schedule requires an explicit compute_area_multiplier from the sub-tile scheduler.
- Measured full-value tile and softmax-weight generator PPA are used for local datapath overhead only.
- The dense GEMM compute array is treated as already packed into the current logic budget; extra dual-stream compute must fit that same budget to be feasible.
- Buffer capacity is checked against measured local SRAM bytes; an optional buffer-area proxy can be added for sensitivity but defaults to zero to avoid double-counting measured local SRAM.
