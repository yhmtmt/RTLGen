# Llama7B Mixed/Int8 Energy Closure

This proposal records the missing comparison between the quality-gated mixed/int8
softmax-recip physical-feasibility point and the exact-FP16 dense-GEMM V3
measured-compute closure.

The job is a low-cost audit. It consumes existing artifacts, uses the
`substituted_compute_*` int8 PPA fields from the physical-feasibility row, adds
measured local L1 overhead power when present, and emits a comparable
throughput/energy/area/precision closure report. It does not run OpenROAD.
