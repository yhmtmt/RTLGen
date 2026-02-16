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
  "dma_addr_width": 64,
  "dma_data_width": 256,
  "axi_addr_width": 64,
  "axi_data_width": 256,
  "axi_id_width": 4,
  "sram_instances": [
    {
      "name": "activation_sram",
      "depth": 16384,
      "width": 256,
      "banks": 8,
      "read_latency": 1,
      "byte_en": true,
      "port": "1r1w",
      "pdk": "sky130",
      "tech_node_nm": 130,
      "base_addr": "0x80000000",
      "alignment_bytes": 64
    }
  ],
  "queue_depth": 16,
  "enable_irq": true,
  "enable_dma_ports": true,
  "enable_cq_mem_ports": true,
  "enable_axi_ports": true,
  "enable_axi_lite_wrapper": false,
  "compute": {
    "enabled": true,
    "gemm": {
      "mac_type": "int8",
      "lanes": 8,
      "accum_width": 32,
      "pipeline": 1
    },
    "vec": {
      "ops": ["add", "mul", "relu"]
    }
  }
}
```

## Field definitions
- `version` (string): config version, must be `"0.1"`.
- `top_name` (string): name of top module to emit.
- `mmio_addr_width` (int): address width for MMIO (bytes).
- `data_width` (int): data width for MMIO and control (bits).
- `dma_addr_width` (int): DMA address width (bits).
- `dma_data_width` (int): DMA data width (bits).
- `axi_addr_width` (int): AXI address width (bits).
- `axi_data_width` (int): AXI data width (bits).
- `axi_id_width` (int): AXI ID width (bits).
- `sram_instances` (list): optional SRAM instances for shell integration and PPA estimation.
  - Each instance should include `name`, `depth`, `width`, `banks`, `read_latency`,
    `byte_en`, `port` (1r1w), and `pdk` or `tech_node_nm`.
  - Optional fields: `base_addr` (hex string or int) and `alignment_bytes` (int).
- `queue_depth` (int): number of 32B descriptors in the command queue.
- `enable_irq` (bool): include IRQ output.
- `enable_dma_ports` (bool): include a stub DMA/memory interface.
- `enable_cq_mem_ports` (bool): include a command queue memory read port.
- `enable_axi_ports` (bool): include AXI4-like memory interface ports (stub).
- `enable_axi_lite_wrapper` (bool): emit an AXI-Lite wrapper module for MMIO.
- `compute` (object, optional): Phase 1 compute generation controls.
  - `compute.enabled` (bool): enable generated GEMM compute datapath hooks.
  - `compute.gemm.mac_type` (string): currently supports `int8` (Phase 1).
  - `compute.gemm.lanes` (int): number of int8 MAC lanes (1..8).
  - `compute.gemm.accum_width` (int): signed accumulator width (16..64).
  - `compute.gemm.pipeline` (int): reserved pipeline knob (must be >=1).
  - `compute.vec.ops` (list[string]): declared vector ops for staged bring-up.

## Notes
- The initial RTL is a stub for **simulation harnessing** only.
- Compute and DMA engines are placeholders; the interface and queues are the
  focus of v0.1.
- SRAM instances are emitted as standalone 1R1W modules for simulation and
  blackbox/synth integration (wiring TBD).
- Phase 1 adds an int8 MAC primitive (`gemm_mac_int8`) and uses it in GEMM
  slot execution while preserving existing descriptor timing behavior.
- When `enable_axi_lite_wrapper` is true, the generator emits:
  - `top_axi.v` (AXI-Lite top wrapper)
  - `axi_lite_mmio_bridge.sv` (bridge module)

## Next steps
- Extend config fields to cover compute tiles and DMA parameters.
- Add additional MAC types (`int16`, `fp16`) behind config switches.
- Keep compatibility with `compute.enabled=false` for stub-only validation
  flows during migration.
- See `npu/docs/sim_dev_plan.md` section "A.1) Compute Bring-up Plan" for
  phased implementation and validation gates.
