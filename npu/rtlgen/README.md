# RTLGen NPU Generator (Stub)

## Purpose
This directory hosts the NPU RTL generator entrypoint and example configs.
The initial version is a **stub** that emits a minimal top module for RTL
simulation bring-up.

## Current status
- MMIO + CQ + DMA/AXI stub RTL generation is implemented.
- AXI-Lite wrapper generation is implemented.

Start here:
- `npu/rtlgen/config_spec.md` for config fields
- `npu/rtlgen/examples/minimal.json` for a tiny config
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
