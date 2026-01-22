# NPU RTLGen Config (v0.1 Draft)

## Purpose
This file defines the minimal configuration schema for the NPU RTL generator
used in RTL simulation bring-up. The goal is a **small, stable config** that
can later be extended without breaking v0.1.

## Current status
- Implemented in `npu/rtlgen/gen.py` with RTL + AXI-Lite wrapper outputs.

## Inputs / outputs
- Input: JSON config (this schema).
- Outputs: `top.v`, optional `top_axi.v` and `axi_lite_mmio_bridge.sv`.

## Top-level fields
```json
{
  "version": "0.1",
  "top_name": "npu_top",
  "mmio_addr_width": 12,
  "data_width": 32,
  "queue_depth": 16,
  "enable_irq": true,
  "enable_dma_ports": true,
  "enable_cq_mem_ports": true,
  "enable_axi_ports": true,
  "enable_axi_lite_wrapper": false
}
```

## Field definitions
- `version` (string): config version, must be `"0.1"`.
- `top_name` (string): name of top module to emit.
- `mmio_addr_width` (int): address width for MMIO (bytes).
- `data_width` (int): data width for MMIO and control (bits).
- `queue_depth` (int): number of 32B descriptors in the command queue.
- `enable_irq` (bool): include IRQ output.
- `enable_dma_ports` (bool): include a stub DMA/memory interface.
- `enable_cq_mem_ports` (bool): include a command queue memory read port.
- `enable_axi_ports` (bool): include AXI4-like memory interface ports (stub).
- `enable_axi_lite_wrapper` (bool): emit an AXI-Lite wrapper module for MMIO.

## Notes
- The initial RTL is a stub for **simulation harnessing** only.
- Compute and DMA engines are placeholders; the interface and queues are the
  focus of v0.1.
- When `enable_axi_lite_wrapper` is true, the generator emits:
  - `top_axi.v` (AXI-Lite top wrapper)
  - `axi_lite_mmio_bridge.sv` (bridge module)

## Next steps
- Extend config fields to cover compute tiles and DMA parameters.
