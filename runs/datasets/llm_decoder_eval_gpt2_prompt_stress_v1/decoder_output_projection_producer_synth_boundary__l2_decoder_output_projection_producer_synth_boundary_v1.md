# Decoder Producer Synthesis Boundary

- make_target: `1_2_yosys`
- timeout_seconds: `1800`
- stall_timeout_seconds: `900`

| num_modules | status | elapsed_s | metrics_status | result_path | log |
|---:|---|---:|---|---|---|
| 2 | rtlgen_failed |  |  |  |  |

## Diagnosis

- decision: `producer_synth_boundary_recorded`
- feasible_max_num_modules: `None`
- first_nonviable_num_modules: `2`
- recommended_next_step: Use the largest completed synth point for near-frontier extrapolation and split or macro-harden larger producers before retrying full physical implementation.
