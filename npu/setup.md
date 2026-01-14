# NPU Environment Setup Plan

This document defines a sequential workflow to establish the NPU development and evaluation toolchain inside the RTLGen repository.

## Phase 0: Repository scaffolding
- Create `npu/` subtree for NPU-specific assets.
- Add a top-level `npu/README.md` describing the directory purpose and ownership.
- Keep all NPU toolchain scripts and configs under `npu/` to avoid mixing with existing `runs/` workflows.

## Phase 1: NVDLA integration baseline
- Import an NVDLA reference repository as a subtree or submodule under `npu/nvdla/`.
- Record the source commit hash and license in `npu/nvdla/README.md`.
- Define a "shell contract" file in `npu/shell/spec.md` that documents the host interface, DMA model, and command queue format.

## Phase 2: Architecture parameterization
- Define a canonical architecture schema in `npu/arch/schema.yml`.
- Add example configurations in `npu/arch/examples/`.
- Provide a validation script (Python) in `npu/arch/validate.py` to enforce schema requirements.

## Phase 3: RTLGen integration
- Implement a generator entrypoint under `npu/rtlgen/` that can emit NPU modules based on the schema.
- Keep NVDLA shell stable while allowing compute core swapping.
- Emit outputs similar to existing RTLGen flows:
  - `verilog/` sources
  - `config.json` or `arch.yml` snapshot
  - metadata describing clocks/resets/IO

## Phase 4: OpenROAD evaluation flow
- Add OpenROAD wrappers under `npu/synth/` for block-level PPA runs.
- Define macro-level floorplanning guidance for NPU tiles in `npu/synth/floorplan.md`.
- Ensure the flow runs inside the devcontainer environment and records results compatible with `runs/` indexing.

## Phase 5: Mapping and scheduling
- Integrate a scheduler backend (TVM or equivalent) under `npu/mapper/`.
- Define a schedule IR in `npu/mapper/ir.md`.
- Add a driver script `npu/mapper/run.py` to map a benchmark to an arch config and emit schedule stats.

## Phase 6: Simulation environment
- Implement a simulator under `npu/sim/` that consumes schedule IR + arch config.
- Support analytical mode first; trace-driven simulation as a follow-up.
- Define output metrics formats in `npu/sim/report.md`.

## Phase 7: End-to-end workflow glue
- Add a single sequential pipeline script (or Makefile) in `npu/` that runs:
  1) arch validation
  2) RTL generation
  3) OpenROAD block synthesis
  4) mapping
  5) simulation
  6) report aggregation
- Ensure all outputs are recorded with stable IDs and hashes.

## Initial deliverables checklist
- `npu/README.md`
- `npu/setup.md` (this file)
- `npu/nvdla/README.md` documenting source and license
- `npu/arch/schema.yml` + one example config
- `npu/shell/spec.md`
- `npu/synth/floorplan.md`
- `npu/mapper/ir.md`
- `npu/sim/report.md`
