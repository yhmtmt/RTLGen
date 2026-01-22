# NPU Subsystem

## Purpose
This directory hosts the NPU development and evaluation toolchain that extends RTLGen
from small arithmetic blocks to NPU generation, mapping, and simulation. NVDLA is a
reference integration target, not a required architectural match.

## Current status
- RTL shell + DMA/AXI stub and RTL simulation path are implemented.
- AXI-Lite MMIO wrapper is available for integration testing.

Start with:
- `npu/docs/index.md`: documentation index (specs, plans, logs).
- `npu/setup.md`: sequential plan for establishing the environment.

Current structure:
- `npu/nvdla/`: NVDLA reference sources (submodule/subtree) and licensing notes.
- `npu/arch/`: architecture schema + example configs.
- `npu/shell/`: host interface and DMA shell contract.
- `npu/rtlgen/`: RTLGen-based generators and templates.
- `npu/synth/`: OpenROAD flows and floorplanning guidance.
- `npu/mapper/`: mapping/scheduling logic (e.g., TVM integration).
- `npu/sim/`: abstracted simulation and reporting.

## Next steps
- Integrate OpenROAD flow for NPU blocks.
- Expand mapper/simulator beyond RTL functional tests.
