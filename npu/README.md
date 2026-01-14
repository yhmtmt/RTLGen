# NPU Subsystem

This directory hosts the NPU development and evaluation toolchain that extends RTLGen
from small arithmetic blocks to NVDLA-based NPU generation, mapping, and simulation.

Start with:
- `npu/setup.md`: sequential plan for establishing the environment.

Planned structure (to be created):
- `npu/nvdla/`: NVDLA reference sources (submodule/subtree) and licensing notes.
- `npu/arch/`: architecture schema + example configs.
- `npu/shell/`: host interface and DMA shell contract.
- `npu/rtlgen/`: RTLGen-based generators and templates.
- `npu/synth/`: OpenROAD flows and floorplanning guidance.
- `npu/mapper/`: mapping/scheduling logic (e.g., TVM integration).
- `npu/sim/`: abstracted simulation and reporting.
