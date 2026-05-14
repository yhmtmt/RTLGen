# Decoder Producer Synthesis Boundary

- make_target: `1_2_yosys`
- timeout_seconds: `1800`
- stall_timeout_seconds: `900`

| num_modules | status | elapsed_s | metrics_status | result_path | log |
|---:|---|---:|---|---|---|
| 8 | ok | 202.2 | ok | runs/designs/npu_blocks/npu_fp16_cpp_nm8_producer/work/3a2fb3e1/result.json | nm8_1_2_yosys.log |
| 16 | ok | 228.2 | ok | runs/designs/npu_blocks/npu_fp16_cpp_nm16_producer/work/3a2fb3e1/result.json | nm16_1_2_yosys.log |

## Diagnosis

- decision: `producer_synth_boundary_not_reached`
- feasible_max_num_modules: `16`
- first_nonviable_num_modules: `None`
- recommended_next_step: Extend the probe to the next producer scale before launching full PnR.
