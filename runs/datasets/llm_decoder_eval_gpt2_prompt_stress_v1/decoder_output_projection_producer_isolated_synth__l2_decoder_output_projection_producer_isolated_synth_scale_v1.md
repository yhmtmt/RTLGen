# Decoder Producer Synthesis Boundary

- make_target: `1_2_yosys`
- timeout_seconds: `1800`
- stall_timeout_seconds: `900`

| num_modules | status | elapsed_s | metrics_status | result_path | log |
|---:|---|---:|---|---|---|
| 1 | ok | 4.0 | ok | /orfs/flow/results/nangate45/npu_fp16_cpp_nm1_producer/producer_isolated_synth/1_2_yosys.v | nm1_1_2_yosys.log |
| 2 | ok | 8.0 | ok | /orfs/flow/results/nangate45/npu_fp16_cpp_nm2_producer/producer_isolated_synth/1_2_yosys.v | nm2_1_2_yosys.log |
| 3 | ok | 10.0 | ok | /orfs/flow/results/nangate45/npu_fp16_cpp_nm3_producer/producer_isolated_synth/1_2_yosys.v | nm3_1_2_yosys.log |
| 4 | ok | 14.0 | ok | /orfs/flow/results/nangate45/npu_fp16_cpp_nm4_producer/producer_isolated_synth/1_2_yosys.v | nm4_1_2_yosys.log |

## Diagnosis

- decision: `producer_synth_boundary_not_reached`
- feasible_max_num_modules: `4`
- first_nonviable_num_modules: `None`
- recommended_next_step: Extend the probe to the next producer scale before launching full PnR.
