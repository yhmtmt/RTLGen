# RTL Simulation Bring-up Log

This log summarizes the RTL simulation bring-up work for the NPU shell,
including queue handling, DMA, and AXI memory integration.

## 1) RTLGen stub + config
- Added `npu/rtlgen/config_spec.md` (v0.1 config fields).
- Added `npu/rtlgen/examples/minimal.json`.
- Added `npu/rtlgen/gen.py` to emit a minimal top module.
- Extended the top with:
  - MMIO registers (VERSION/CAPS/STATUS/CONTROL/IRQ/CQ)
  - CQ head/tail tracking
  - descriptor fetch logic
  - DMA request stub
  - AXI4-style memory ports (stubbed)

## 2) Queue + descriptor plumbing
- Added CQ memory read port (`cq_mem_addr/cq_mem_rdata`) and a two-stage
  fetch/decode step.
- Implemented minimal descriptor decode for `DMA_COPY` (opcode 0x01).
- Linked decoded fields to DMA request signals.

## 3) DMA + AXI integration
- Implemented a minimal AXI DMA shim:
  - burst read (AR/R) into an internal buffer
  - burst write (AW/W/B) from that buffer
  - raises IRQ_EVENT on B response
- Fixed burst sizing for 8KB transfers (256 beats) with 9-bit counters.

## 4) RTL testbench + memory model
- Added `npu/sim/rtl/tb_npu_shell.sv`:
  - drives MMIO, doorbell, and CQ tail
  - reads descriptor stream from `*.bin`
  - checks CQ_HEAD, IRQ bits, and memory copy correctness
- Added a shared AXI RAM model (`npu/sim/rtl/axi_mem_model.sv`) used by both testbenches.
- Added `npu/sim/rtl/Makefile` with `gen/build/run/clean` targets and
  `BYTES` plusarg support.

## 5) Mapper integration
- `npu/mapper/run.py --out-bin` generates the descriptor stream used by the TB.
- `npu/mapper/examples/minimal_schedule.yml` set to 8KB DMA for burst testing.

## 6) Status
- RTL sim passes end-to-end with 8KB DMA copy.
- Queue handling, DMA decode, and AXI burst path verified in the TB.
- AXI-Lite wrapper path verified by `tb_axi_lite_mmio.sv`.

## 7) Arch-driven shell + SRAM PPA scaffolding (2026-01-27)
- Added arch→RTLGen adapter so shell config is driven by `npu/arch/*.yml`.
- Extended AXI/DMA width fields in config and generator; updated RTL sim targets to accept `CONFIG` and `ARCH`.
- Added SRAM instance list to arch + RTLGen config and emit `sram_models.sv` (1R1W sim model).
- Added CACTI submodule and PPA script (`npu/synth/sram_ppa.py`) writing to `runs/designs/sram/<id>/sram_metrics.json`.
- Added CACTI template and pipeline hook; scale CACTI outputs for tech nodes > 90nm.
- Note: sky130hd SRAM macro generation is planned; current flow uses CACTI estimates and sim-only SRAM models.

## 8) GEMM/EVENT stub coverage (2026-01-30)
- Added stub decode for GEMM/EVENT opcodes (IRQ_EVENT only, no compute).
- Added `+event_test=1` to RTL benches (shell + AXI‑Lite) for descriptor coverage.

## Next steps
- Implement sky130hd SRAM macro generation path and hook it into synthesis.
- Add functional GEMM path once the compute core interface is defined.
