# NPU Status Summary

## Purpose
Single-page snapshot of NPU development status for quick reference.

<!-- STATUS_META_START -->
Last updated: 2026-01-30
Git: unknown
<!-- STATUS_META_END -->

## Current status
- **Shell/ABI**: v0.1 spec written; MMIO + CQ + DMA semantics implemented in RTL.
- **RTLGen**: stub generator emits `top.v`, plus optional AXI‑Lite wrapper.
- **RTL sim**: end-to-end functional validation with DMA + AXI burst + AXI‑Lite tests.
- **SRAM sim**: AXI router + SRAM models integrated; SRAM DMA tests added.
- **SRAM PPA**: CACTI flow integrated with >90nm scaling and aggregation.
- **Mapper**: v0.1 IR and binary descriptor emission implemented.
- **Performance sim**: planned.
- **OpenROAD**: planned (block-level synthesis flow pending).

## Next steps
- Implement performance simulator stub.
- Add OpenROAD flow for DMA tile and CQ logic.
- Extend descriptor decode to GEMM and event ops.
- Add sky130hd SRAM macro generation and replace CACTI estimates for that PDK.

## Pointers
- Specs: `npu/docs/index.md`
- Workflow: `doc/npu_workflow.md`
- Logs: `npu/docs/rtl_sim_log.md`
