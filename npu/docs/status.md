# NPU Status Summary

## Purpose
Single-page snapshot of NPU development status for quick reference.

<!-- STATUS_META_START -->
Last updated: 2026-02-07
Git: unknown
<!-- STATUS_META_END -->

## Current status
- **Shell/ABI**: v0.1 spec written; MMIO + CQ + DMA semantics implemented in RTL.
- **RTLGen**: stub generator emits `top.v`, plus optional AXI‑Lite wrapper.
- **RTL sim**: end-to-end functional validation with DMA + AXI burst + AXI‑Lite tests.
- **SRAM sim**: AXI router + SRAM models integrated; SRAM DMA tests added.
- **GEMM/Event**: stub decode paths raise IRQ_EVENT; basic TB coverage added.
- **SRAM PPA**: CACTI flow integrated with >90nm scaling and aggregation.
- **Mapper**: v0.1 IR and binary descriptor emission implemented.
- **Performance sim**: implemented (`npu/sim/perf/`).
  - Current op coverage: DMA_COPY, GEMM, EVENT_SIGNAL/WAIT, NOOP.
  - Next op coverage: VEC_OP and SOFTMAX (perf modeling + descriptor flags).
- **OpenROAD**: planned (block-level synthesis flow pending).
- **MAC backend**: `npu/rtlgen/gen.py` now supports optional C++ RTLGen MAC
  backend (`compute.gemm.mac_source=rtlgen_cpp`) for GEMM experiments.

## Next steps
- Extend RTLGen with MAC-based compute generation for GEMM/VEC (start with
  `int8` GEMM, then minimal VEC `add/mul/relu`).
- Integrate C++ `src/rtlgen` MAC generator (`operations[].type="mac"`) into
  NPU core exploration, starting with accumulator feedback into PP rows.
- Extend performance sim op coverage (VEC_OP / SOFTMAX).
- Refine external memory modeling (latency/burst/outstanding) and calibrate to PPA.
- Add OpenROAD flow for DMA tile and CQ logic.
- Extend descriptor decode to GEMM and event ops.
- Add sky130hd SRAM macro generation and replace CACTI estimates for that PDK.

## Pointers
- Specs: `npu/docs/index.md`
- Workflow: `npu/docs/workflow.md`
- Logs: `npu/docs/rtl_sim_log.md`
