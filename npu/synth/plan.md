# NPU OpenROAD Synthesis Plan

This plan outlines how to integrate NVDLA hardware references into RTLGen's
OpenROAD evaluation flow for block-level NPU macros.

## Goals
- Reuse NVDLA `hw/syn` scripts as a baseline for constraints and targets.
- Provide RTLGen wrappers that emit consistent `verilog/` outputs for OpenROAD.
- Record results in `runs/designs/` using the same append-only `metrics.csv`.

## Reference inputs
- NVDLA HW repository: `npu/nvdla/hw`
  - `syn/` contains example synthesis scripts and constraints.
  - `spec/` contains configuration settings and performance assumptions.

## Proposed wrapper flow
1) Generate RTL (RTLGen NPU generator) for a target macro:
   - compute tile
   - SRAM wrapper
   - DMA engine
2) Emit a design directory under `runs/designs/npu/<design>/` with:
   - `verilog/`
   - `config.json` or `arch.yml`
   - `README.md` describing the macro and config hash
3) Provide a sweep definition in `runs/campaigns/npu/<campaign>/sweeps/`.
4) Invoke OpenROAD via `scripts/run_sweep.py` (or a new NPU-specific wrapper).

## Constraint alignment
- Translate NVDLA `syn` SDC parameters into OpenROAD constraints:
  - clock period / uncertainty
  - IO delays
  - load assumptions
- Capture default floorplan hints in `npu/synth/floorplan.md`.

## Output expectations
- Timing, area, and power in `metrics.csv`.
- Config hashes recorded per run.
- Any NVDLA-specific knobs reflected in `params_json`.

## Near-term tasks
- Inventory key NVDLA `syn` scripts and extract common SDC knobs.
- Draft a minimal NPU macro wrapper config in `runs/campaigns/npu/`.
- Validate that `scripts/run_sweep.py` can target NPU macro designs with
  custom SDC and floorplan constraints.
