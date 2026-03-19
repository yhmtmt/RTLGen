# npu_fp16_cpp_nm1_sigmoidcmp

Mode-compare physical-synthesis target for fp16 C++ GEMM with integrated int8
sigmoid support in the fixed `nm1` vec path.

- source config: `runs/designs/npu_blocks/npu_fp16_cpp_nm1_sigmoidcmp/config_nm1_sigmoid.json`
- top module: `npu_top`
- compute.gemm.num_modules: `1`
- compute.vec.ops: `add`, `mul`, `relu`, `sigmoid`
- compute.vec.activation_source: `rtlgen_cpp`
- compute.gemm.rtlgen_cpp.binary_path: `build/rtlgen`
- compute.vec.rtlgen_cpp.binary_path: `build/rtlgen`
