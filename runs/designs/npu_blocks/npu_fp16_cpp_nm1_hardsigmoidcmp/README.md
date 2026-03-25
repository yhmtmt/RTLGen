# npu_fp16_cpp_nm1_hardsigmoidcmp

Integrated full-top `nm1` fp16 GEMM plus int8 hard-sigmoid vec path.

- source config: `runs/designs/npu_blocks/npu_fp16_cpp_nm1_hardsigmoidcmp/config_nm1_hardsigmoid.json`
- top module: `npu_top`
- intent: establish the bounded integrated hard-sigmoid-enabled `nm1` architecture-block path before any later Layer 2 work
- compute.gemm.num_modules: `1`
- compute.vec.ops: `add`, `mul`, `relu`, `hardsigmoid`
- compute.vec.activation_source: `rtlgen_cpp`
- compute.gemm.rtlgen_cpp.binary_path: `build/rtlgen`
- compute.vec.rtlgen_cpp.binary_path: `build/rtlgen`
