# NPU Status Summary

## Purpose
Single-page snapshot of NPU development status for quick reference.

<!-- STATUS_META_START -->
Last updated: 2026-02-20
Git: e6c62e5
<!-- STATUS_META_END -->

## Current status
- **Shell/ABI (Implemented)**: v0.1 MMIO/CQ/DMA semantics are documented and
  exercised in RTL benches.
- **RTLGen core path (Implemented)**: generator emits `top.v`, `mmio_map.vh`,
  `sram_map.vh`, and optional AXI-Lite wrapper.
- **Mapper (Implemented)**: schedule IR + binary descriptor emission are active
  in `npu/mapper/`.
- **RTL simulation (Implemented)**: golden regression covers DMA/GEMM/VEC/event
  paths with RTL logs consumed by compare scripts.
- **Performance simulation (Implemented)**: descriptor-driven analytical model
  plus unit tests and RTL/perf comparison hooks.
- **SRAM PPA (Implemented)**: CACTI-based flow and aggregation pipeline are available.
- **OpenROAD block flow (Implemented)**: `run_block_sweep.py` wrapper is active.
- **fp16 backend sweep (Implemented)**: `make_target=finish` comparison completed:
  - `builtin_raw16`: `critical_path_ns=5.4287`, `die_area=2250000`, `total_power_mw=0.233`
  - `cpp_ieee`: `critical_path_ns=5.6462`, `die_area=2250000`, `total_power_mw=0.229`
  - report: `runs/designs/npu_blocks/fp16_backend_decision_nangate45.md`
- **fp16 backend lock (Implemented)**: generator default for
  `compute.gemm.mac_type=fp16` is `mac_source=rtlgen_cpp` (IEEE-half path);
  `builtin_raw16` remains explicit non-IEEE baseline.
- **Architecture layering v0.2 draft (Implemented)**: draft schema + example and
  `npu/arch/to_rtlgen.py` derivation path are active for `gemm`/`vec` candidate
  emission.
- **SRAM pre-synthesis flow (Implemented)**: `npu/synth/pre_synth_memory.py`
  selects memgen when configured and falls back to CACTI estimation.

## In progress
- C++ MAC generator extension for explicit MAC operation modes including
  accumulator feedback (`pp_row_feedback`) for NPU exploration.
- Expanded vector-op constrained-random coverage for activation and derivative ops.
- Stronger `arch v0.2` validation (types/ranges/enums) and mapper/perf usage of
  interconnect + mapping constraints.
- Post-physical SRAM metric extraction and feedback loop into perf simulation.

## Planned
- Broader compute-enabled OpenROAD sweeps (beyond fp16 backend comparison).
- Additional numeric-policy hardening and stress tests for fp16 edge behavior.
- Optional future datatype exploration (bf16/fp8) after fp16 path maturity.

## Pointers
- Index: `npu/docs/index.md`
- Workflow: `npu/docs/workflow.md`
- Simulation plan: `npu/docs/sim_dev_plan.md`
- Synthesis plan: `npu/synth/plan.md`
