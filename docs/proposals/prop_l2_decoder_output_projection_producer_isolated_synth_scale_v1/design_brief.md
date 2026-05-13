# Design Brief

## Goal
Extend the isolated decoder output-projection producer synth probe from nm1/nm2 to nm1 through nm4.

## Rationale
The prior isolated probe showed that `gemm_compute_array` synth is viable at nm1 and nm2, while the whole `npu_top` producer probe timed out at nm2. The next boundary question is whether the arithmetic array itself remains easy to synthesize at nm3/nm4.

## Evaluation
- top: `gemm_compute_array`
- flow target: `1_2_yosys`
- configs: `npu_fp16_cpp_nm1_producer` through `npu_fp16_cpp_nm4_producer`
- sweep: `runs/campaigns/npu/output_projection_producer_scale/sweeps/nangate45_isolated_synth.json`

