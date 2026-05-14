# Decoder Producer Physical Boundary

- make_target: `3_3_place_gp`
- timeout_seconds: `3600`
- stall_timeout_seconds: `1200`

| num_modules | status | elapsed_s | metrics_status | result_path | log |
|---:|---|---:|---|---|---|
| 16 | ok | 822.8 | ok | runs/designs/npu_blocks/npu_fp16_cpp_nm16_producer/work/3a2fb3e1/result.json | nm16_3_3_place_gp.log |

## Diagnosis

- decision: `producer_physical_boundary_not_reached`
- feasible_max_num_modules: `16`
- first_nonviable_num_modules: `None`
- recommended_next_step: Use the largest completed physical point for near-frontier extrapolation or extend cautiously.
