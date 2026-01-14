# NPU Workflow (High-Level)

This document defines the sequential, end-to-end workflow for NPU development and evaluation
inside RTLGen. It complements `npu/setup.md`, which focuses on environment setup.

## 1) Architecture definition
- Create or edit an NPU architecture config (YAML) under `npu/arch/examples/`.
- Validate against `npu/arch/schema.yml` using `npu/arch/validate.py`.

## 2) RTL generation
- Use the NPU generator entrypoint under `npu/rtlgen/` to emit:
  - RTL sources (`verilog/` or `rtl/`)
  - an immutable copy of the architecture config
  - metadata describing top-level IO, clocks, and resets
- Keep the NVDLA shell stable while iterating on compute and memory subsystems.

## 3) Block-level synthesis (OpenROAD)
- Run OpenROAD block-level PPA for key NPU macros (compute tile, SRAM wrapper, DMA).
- Apply macro-level floorplanning guidance from `npu/synth/floorplan.md`.
- Record results in `runs/designs/` with unique design directories per experiment.

## 4) Mapping and scheduling
- Map target benchmarks to the architecture using `npu/mapper/run.py`.
- Produce a schedule IR and legality report (capacity, bandwidth, and alignment).

## 5) Abstracted simulation
- Run the simulator (`npu/sim/`) with the schedule IR and architecture config.
- Emit timeline metrics and resource utilization summaries.

## 6) Aggregation and iteration
- Aggregate PPA and simulation results into a consistent, versioned index.
- Use results to revise architecture parameters and re-run the pipeline.

## Data management expectations
- Each experiment creates a new design directory under `runs/designs/`.
- Results are append-only (`metrics.csv`) and indexed by `runs/index.csv`.
- Record tool versions, config hashes, and environment details for reproducibility.
