# NPU OpenROAD Synthesis Plan

## Purpose
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
4) Invoke OpenROAD via `npu/synth/run_block_sweep.py` (block-level wrapper).

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
- Validate that `npu/synth/run_block_sweep.py` can target NPU macro designs
  with custom SDC and floorplan constraints.
- Add a C++ RTLGen MAC block target (`operations[].type="mac"`,
  `accumulation_mode="pp_row_feedback"`) for multiplier/MAC PPA exploration.

## Status
- RTL shell and DMA stub are available.
- FP16 backend sweep harness is available:
  - `npu/synth/run_fp16_backend_sweep.py`
  - `npu/synth/fp16_backend_sweep_nangate45.json`
  - `runs/designs/npu_blocks/npu_fp16_builtin_l1`
  - `runs/designs/npu_blocks/npu_fp16_cpp_l1`
- FP16 backend sweep executed at `make_target=3_5_place_dp` (Nangate45):
  - report: `runs/designs/npu_blocks/fp16_backend_decision_nangate45.md`
  - measured `builtin_raw16` and `cpp_ieee` successfully
  - latest metrics:
    - `builtin_raw16`: `critical_path_ns=5.4414`, `die_area=2250000`, `total_power_mw=0.2014`
    - `cpp_ieee`: `critical_path_ns=5.6592`, `die_area=2250000`, `total_power_mw=0.1976`
  - default recommendation is `cpp_ieee` (builtin excluded from default lock
    because it is a non-IEEE placeholder backend)

## Next steps
- Implement a minimal block-level OpenROAD run for the DMA tile.
- Add a `runs/designs/npu_blocks/<design>/` example and sweep in `npu/synth/`.
- Run a follow-up fp16 backend confirmation sweep at `make_target=finish`
  before signing off backend lock for full-flow PPA.
