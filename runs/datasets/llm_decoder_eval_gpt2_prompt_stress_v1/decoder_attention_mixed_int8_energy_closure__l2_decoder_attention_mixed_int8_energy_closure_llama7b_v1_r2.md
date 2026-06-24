# Llama7B Mixed-Precision Int8 Compute Energy Closure

- decision: `mixed_precision_int8_compute_improves_latency_not_energy`
- source rows used: `3`
- physical feasible rows: `3`
- best requested mode: `dual_mac`
- best requested adjusted latency us: `1575.373891`
- best requested substituted compute arch: `dense_gemm_int8_16x8_k1_p1`
- best requested substituted compute area um2: `89549280.0`
- best requested substituted compute power mw: `974.7`
- baseline fp16 v3 energy mJ: `82.92581224371085`
- baseline fp16 v3 latency us: `95126.8919364575`
- recommended next step: `keep exact-FP16 V3 as the energy baseline and use mixed/int8 as the latency frontier pending real-checkpoint quality validation`

## Best Measured Point

| candidate | latency us | throughput tok/s | energy mJ | area mm2 | compute mJ | HBM mJ | sram mJ | dominant |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| die800_dense_gemm_int8_16x8_k1_p1_rep855_lat1575.37_hbm0.983398_tt1024 | 1575.373891 | 634.7699461778119 | 135.75588466251537 | 800.0 | 1.5372362316073815 | 134.14461348516411 | 4.349128155786915e-05 | hbm |

## Pareto Rows

| candidate | latency us | energy mJ | area mm2 | compute arch | compute replicas | dominant |
|---|---:|---:|---:|---|---:|---|
| die800_dense_gemm_int8_16x8_k1_p1_rep855_lat1575.37_hbm0.983398_tt1024 | 1575.373891 | 135.75588466251537 | 800.0 | dense_gemm_int8_16x8_k1_p1 | 855 | hbm |

## Remaining Abstractions

- HBM and SRAM energy are sourced from existing aggregate campaign helpers; NoC still uses the payload-byte-hop model.
- Compute energy is from substituted_compute_power_mw plus measured local L1 overhead power carried by mixed-precision feasibility rows, not from a fresh end-to-end measured compute rerun.
- adjusted_latency_us_if_feasible is used when present and source latency is used as a fallback.
- Mixed/int8 quality remains proxy-backed, not real Llama7B checkpoint perplexity or task accuracy.
