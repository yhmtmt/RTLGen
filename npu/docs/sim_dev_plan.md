# Simulation Development Plan (RTL + Performance)

## Purpose
This plan defines two simulation schemes:
1) **RTL functional validation** (logic correctness)
2) **Abstracted performance simulation** (GPU-accelerated if available)

## Current status
- RTL functional simulation path is implemented.
- Performance simulation remains planned.

## A) RTL Functional Validation (First Priority)

### Goals
- Validate that RTLGen-produced shell + compute RTL responds correctly to
  command descriptors.
- Provide a minimal, repeatable testbench for logic correctness.

### Scope (v0.1)
- MMIO init (CQ base/size, tail, doorbell)
- Command parsing (DMA_COPY, GEMM stub, EVENT_SIGNAL)
- IRQ behavior and status updates
- Optional: memory model hooks for DMA sanity

### Deliverables
- `npu/rtlgen/` generator stub emitting a tiny top module
- `npu/rtlgen/examples/` config(s)
- `npu/sim/rtl/` testbench that:
  - reads `*.bin` descriptors
  - drives MMIO writes and doorbell
  - checks expected status/IRQ/events
 - AXI memory model for DMA validation (shared)

### Suggested steps
1) Define RTLGen NPU config format (JSON/YAML). **Done**
2) Create a **minimal RTL top** with MMIO + CQ + DMA stub. **Done**
3) Build testbenches for MMIO and AXI-Lite. **Done**
4) Run golden command streams through RTL. **Done**

## B) Abstracted Performance Simulation (Second Priority)

### Goals
- Estimate performance without full RTL timing.
- Enforce NPU constraints while using software/GPU to compute.

### Scope (v0.1)
- Consume schedule IR from `npu/mapper/ir.md`.
- Use simple cost models (compute + DMA).
- Produce a timeline and utilization report.

### Deliverables
- `npu/sim/model.py`: cost model stubs
- `npu/sim/run.py`: run schedule IR + arch config
- `npu/sim/report.md`: report format (already drafted)

### Suggested steps
1) Define model parameters in `npu/arch/schema.yml`.
2) Implement analytical simulator (no GPU required).
3) Add optional GPU kernels later for accuracy.

## C) Interfaces Between RTL and Performance Sims
- Shared descriptors (binary) from `npu/mapper/run.py --out-bin`
- Shared config schema (arch + shell)
- Shared error/IRQ semantics (from `npu/shell/spec.md`)

## Next steps
- Implement analytical simulator stub under `npu/sim/`.
