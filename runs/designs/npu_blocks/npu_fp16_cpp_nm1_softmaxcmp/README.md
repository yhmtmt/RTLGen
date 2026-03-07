# npu_fp16_cpp_nm1_softmaxcmp

Mode-compare physical-synthesis target for fp16 C++ GEMM with the dedicated
row-wise SOFTMAX wrapper integrated into `npu_top`.
- source config: `runs/designs/npu_blocks/npu_fp16_cpp_nm1_softmaxcmp/config_nm1_softmax.json`
- top module: `npu_top`
- compute.gemm.num_modules: `1`
- compute.softmax.module_name: `softmax_rowwise_int8_r4_wrapper`
- compute.softmax.row_bytes: `4`
