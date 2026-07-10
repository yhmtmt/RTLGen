# Score32 Separated Compute Recost

- decision: `score32_separated_compute_recost_requires_precision_aligned_rtl`
- latency us: `1575.373891`
- throughput token/s: `634.769946177812`
- total energy mJ/token: `135.755919226219`
- logic area mm2: `179.6236140317`
- quality backed: `False`
- promotable: `False`

## Components

| component | area um2 | power mW | path ns | clock ok |
|---|---:|---:|---:|---:|
| dense_int8_gemm_fabric | 179098560.0 | 974.7 | 2.8003 | True |
| shared_score32_vector_softmax_overhead | 480367.9308 | 0.9456 | 5.5948 | True |
| command_dispatch_control | 15775.9 | 0.0587 | 0.4629 | True |
| hbm_replay_controller_c4 | 28910.2009 | 0.109 | 2.2087 | True |

## Remaining Abstractions

- the inherited q8/k8/v6 reciprocal-LUT energy row is not precision-aligned with the q8/k8/v8 score32 exp-LUT/div target
- producer-to-score32 ready/valid queues and backpressure are not yet embodied in one composed RTL block
- the inherited dense-int8 schedule has not yet been replayed against the separated score32 consumer
- full QK-to-softmax-to-V RTL/perf-sim tensor-hash equivalence is pending for the separated composition
- NoC and SRAM energy remain profile-scaled rather than gate-level toggle power
- HBM energy is source-backed aggregate energy, not vendor current signoff
