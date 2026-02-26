# RTLGen NPU Generator (Stub)

## Purpose
This directory hosts the NPU RTL generator entrypoint and example configs.
The initial version is a **stub** that emits a minimal top module for RTL
simulation bring-up.

## Current status
- MMIO + CQ + DMA/AXI stub RTL generation is implemented.
- AXI-Lite wrapper generation is implemented.
- fp16 GEMM default backend is locked to C++ IEEE-half MAC generation
  (`compute.gemm.mac_type=fp16` defaults to `mac_source=rtlgen_cpp`).
- GEMM slot/module count is configurable with `compute.gemm.num_modules`
  (default `2`), with one MAC instance emitted per module.
- `compute.gemm.lanes_per_module` is supported as the preferred lane knob
  (`compute.gemm.lanes` remains as a compatible alias).
- Generated RTL now wraps GEMM arithmetic in a dedicated
  `gemm_compute_array` submodule with `(* keep_hierarchy = 1 *)`
  attributes on the module and instance.
- `gemm_compute_array` is emitted as a concrete (non-parameterized) module so
  OpenROAD/Yosys `SYNTH_KEEP_MODULES=gemm_compute_array` can match it directly
  without `$paramod` specialization names.

Start here:
- `npu/rtlgen/config_spec.md` for config fields
- `npu/rtlgen/examples/minimal.json` for a tiny config
- `npu/rtlgen/examples/minimal_gemm_4modules.json` for multi-module GEMM
- `npu/rtlgen/gen.py` to emit RTL

AXI-Lite MMIO:
- Set `enable_axi_lite_wrapper` to emit `top_axi.v` and `axi_lite_mmio_bridge.sv`.
- The wrapper exposes a simple AXI-Lite slave for register access.

Outputs:
- `top.v`: core top module with MMIO + queue + DMA/AXI ports
- `top_axi.v`: AXI-Lite wrapper (optional)
- `axi_lite_mmio_bridge.sv`: AXI-Lite to MMIO bridge (optional)

## How to run
```sh
python3 npu/rtlgen/gen.py --config npu/rtlgen/examples/minimal.json --out npu/rtlgen/out
```

## Next steps
- Add compute tile and DMA micro-architecture generation.
