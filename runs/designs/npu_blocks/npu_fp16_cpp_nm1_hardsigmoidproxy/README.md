# npu_fp16_cpp_nm1_hardsigmoidproxy

Reduced integrated physical proxy for the fixed `nm1` fp16 GEMM plus int8 hard-sigmoid vec path.

- source config: `runs/designs/npu_blocks/npu_fp16_cpp_nm1_hardsigmoidproxy/config_nm1_hardsigmoidproxy.json`
- top module: `npu_hardsigmoid_proxy_top`
- intent: preserve the integrated compute path while removing shell-facing
  DMA/CQ/AXI/MMIO wrapper overhead that made full `npu_top` synthesis
  impractical for first-pass Layer 1 physical characterization
- compute.gemm.num_modules: `1`
- compute.vec.ops: `add`, `mul`, `relu`, `hardsigmoid`
- compute.vec.activation_source: `rtlgen_cpp`
- compute.gemm.rtlgen_cpp.binary_path: `build/rtlgen`
- compute.vec.rtlgen_cpp.binary_path: `build/rtlgen`
