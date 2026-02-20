# NPU Subsystem

## Purpose
This directory contains the NPU development flow built on top of RTLGen:
architecture config, RTL generation, mapper descriptors, RTL/perf simulation,
and block-level OpenROAD evaluation.

## Current status
- **Implemented**: shell/MMIO/CQ/DMA RTL path with AXI and AXI-Lite testbenches.
- **Implemented**: mapper descriptor flow (`npu/mapper/`) and golden schedule assets.
- **Implemented**: performance simulator (`npu/sim/perf/`) with RTL/perf comparison scripts.
- **Implemented**: OpenROAD block flow wrappers (`npu/synth/run_block_sweep.py`).
- **Implemented**: fp16 backend comparison sweep at `make_target=finish` with report:
  `runs/designs/npu_blocks/fp16_backend_decision_nangate45.md`.
- **Locked policy**: fp16 GEMM default backend is `rtlgen_cpp` (IEEE-half path), with
  `builtin_raw16` retained as explicit non-IEEE baseline.
- **Implemented**: `arch v0.2-draft` hierarchy schema + example and
  architecture-to-rtlgen derivation adapter in `npu/arch/to_rtlgen.py`.

## Quick start
- Documentation hub: `npu/docs/index.md`
- Environment/setup phases: `npu/setup.md`
- Golden RTL+perf regression: `npu/sim/run_golden.sh`
- Perf unit tests: `make -f npu/sim/perf/Makefile test`
- fp16 backend sweep: `python3 npu/synth/run_fp16_backend_sweep.py --platform nangate45 --sweep npu/synth/fp16_backend_sweep_nangate45.json --make_target finish`

## Directory map
- `npu/nvdla/`: NVDLA reference sources and compatibility references.
- `npu/arch/`: architecture schema, examples, and converters.
- `npu/shell/`: shell/MMIO contract and interface spec.
- `npu/rtlgen/`: NPU RTL generator and configuration schema.
- `npu/mapper/`: schedule/descriptors and mapping helpers.
- `npu/sim/`: RTL and performance simulation flows.
- `npu/synth/`: OpenROAD sweep wrappers, floorplan notes, and synthesis plans.
- `npu/docs/`: status, workflow, and development plans.

## Next steps
- Expand C++ MAC generator integration (`pp_row_feedback`) into NPU backend options.
- Strengthen fp16 numerical validation coverage (random stress and policy edge cases).
- Extend vector-op constrained-random and derivative-op RTL/perf parity tests.
- Harden `arch v0.2` validation and map interconnect/mapping constraints into
  mapper/perf policy for hierarchical execution.
