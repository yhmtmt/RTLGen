# Simulation Development Plan (RTL + Performance)

## Purpose
This plan defines two simulation schemes:
1) **RTL functional validation** (logic correctness)
2) **Abstracted performance simulation** (GPU-accelerated if available)

## Current status
- RTL functional simulation path is implemented.
- Performance simulation is implemented (analytical v0.1 under `npu/sim/perf/`).
- Process note: re-run RTL simulation whenever `npu/rtlgen/gen.py` changes.
- Mapper golden schedule validates cleanly (`npu/mapper/examples/golden_schedule.yml`).
- Golden mapping sim flow: RTL (Makefile `BIN=`) and perf (`npu/sim/perf/run.py --bin`).

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

## A.1) Compute Bring-up Plan (GEMM + VEC via RTLGen MAC generators)

### Purpose
- Add a minimal but real compute path so GEMM/VEC are no longer timing-only
  stubs in `npu/rtlgen/out/top.v`.
- Keep compute generation parameterized so future architecture sweeps can
  switch MAC styles without rewriting top-level RTL.

### Scope (initial implementation)
- GEMM: integer MAC array with deterministic accumulate/writeback behavior.
- VEC: minimal elementwise ops (`add`, `mul`, `relu`) using the same MAC
  datapath where possible.
- Keep descriptor/IRQ semantics stable with `npu/shell/spec.md`.

### RTLGen extension points
1) Extend config schema with a compute section:
   - `compute.enabled`
   - `compute.gemm.mac_type` (e.g., `int8`, `int16`, `fp16`)
   - `compute.gemm.lanes`, `compute.gemm.accum_width`, `compute.gemm.pipeline`
   - `compute.vec.ops` (allowed op list)
2) Add generator output modules for MAC variants under `npu/rtlgen/`:
   - reusable MAC primitive(s)
   - lane array wrapper
   - GEMM/VEC control wrapper
3) Update top generation:
   - wire descriptor decode to compute issue/complete
   - keep DMA and CQ flow unchanged for compatibility
   - expose a clear fallback path when `compute.enabled=false`

### Validation gates
1) RTL functional:
   - add GEMM correctness checks in `npu/sim/rtl/` (small matrix sanity tests)
   - add VEC op checks for `add/mul/relu`
   - keep existing DMA/CQ regressions green
2) Mapping/perf alignment:
   - mapper emits descriptors that match new compute fields
   - perf sim uses matching op semantics and latency knobs
3) Synthesis readiness:
   - create a dedicated design directory under `runs/designs/npu_blocks/`
     for compute-enabled top
   - run `npu/synth/run_block_sweep.py` on that target (Nangate45 first)

### Delivery phases
1) Phase 1: single MAC type (`int8`) + GEMM correctness in RTL sim.
2) Phase 2: add VEC minimal ops (`add/mul/relu`) on shared datapath.
3) Phase 3: add second MAC type (`int16` or `fp16`) behind config switch.
4) Phase 4: run OpenROAD block sweep and compare against DMA/CQ-only baseline.
5) Phase 5: integrate C++ `src/rtlgen` MAC generator path into NPU MAC-core
   exploration:
   - add `mac` operation config in C++ RTLGen
   - feed accumulator input back into partial-product rows (`pp_row_feedback`)
   - evaluate PPA/timing tradeoffs with the same OpenROAD block sweep flow

## B) Abstracted Performance Simulation (Second Priority)

### Goals
- Estimate performance without full RTL timing.
- Enforce NPU constraints while using software/GPU to compute.

### Scope (v0.1)
- Consume binary descriptor stream from `npu/mapper/run.py --out-bin`.
- Use simple cost models (compute + DMA + fixed overheads).
- Emit a JSON timing trace + summary metrics.

### Deliverables
- `npu/sim/perf/model.py`: cost model stubs
- `npu/sim/perf/run.py`: parse descriptor bin + emit JSON trace
- `npu/sim/report.md`: JSON trace schema + summary fields

### Suggested steps
1) Define model parameters (bandwidth/throughput/overheads).
2) Implement analytical simulator (no GPU required).
3) Add optional GPU kernels later for accuracy.

## C) Interfaces Between RTL and Performance Sims
- Shared descriptors (binary) from `npu/mapper/run.py --out-bin`
- Shared config schema (arch + shell + perf model config)
- Shared error/IRQ semantics (from `npu/shell/spec.md`)

## Next steps
- Start Phase 2 of compute bring-up: minimal VEC decode/execution path
  (`add/mul/relu`) after GEMM Phase 1.
- Start Phase 5 scaffold: wire C++ RTLGen `mac` config + `pp_row_feedback`
  generation path and add a focused Verilog regression.
- Extend perf sim model coverage (VEC_OP / SOFTMAX) and refine the memory model
  (latency/burst/outstanding).
- Keep bandwidth parameterization documented in `npu/sim/perf/README.md`.
