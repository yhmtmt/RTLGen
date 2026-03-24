# npu_fp16_cpp_nm1_tanhcmp

Integrated fixed `nm1` fp16 GEMM plus int8 tanh support in the fixed `nm1` vec path.

- source config: `runs/designs/npu_blocks/npu_fp16_cpp_nm1_tanhcmp/config_nm1_tanh.json`
- top module: `npu_top`
- compute.vec.ops: `add`, `mul`, `relu`, `tanh`
- compute.vec.activation_source: `rtlgen_cpp`
- compute.gemm.rtlgen_cpp.binary_path: `build/rtlgen`
- compute.vec.rtlgen_cpp.binary_path: `build/rtlgen`
