# NVDLA Compatibility Notes (Control Plane vs. RTLGen NPU Shell)

## Purpose
This note explains how to confirm **compatibility in spirit** with NVDLA while
acknowledging that RTLGen targets GEMM/LLM workloads and is **not** binary- or
opcode-compatible with the NVDLA compute pipeline.

## Current status
- Shell contract aligns with NVDLA integration patterns.
- AXI-Lite MMIO wrapper provides a concrete integration bridge.

## 1) What “compatibility” means here
We define compatibility as:
- **Integration model alignment**: host-visible control plane, DMA concepts, and
  event/interrupt behavior that are similar to the NVDLA “shell” expectation.
- **SoC-level integration ease**: a block diagram and register interface that
  can be wired into a system using the same kinds of hooks (MMIO, DMA, IRQ).

We **do not** require:
- Matching NVDLA opcodes or internal engines.
- NVDLA’s convolution-centric microarchitecture.

## 2) How to confirm alignment with NVDLA
Use the following checks against the NVDLA references under `npu/nvdla/`:

### 2.1 Control plane and register interface
- Verify there is a **host-visible configuration plane** (MMIO/CSB-like).
- Confirm device status reporting (idle/busy/error).
- Confirm host-driven command submission (queue or equivalent).

Checklist:
- `npu/shell/spec.md` defines MMIO regs and a command queue.
- NVDLA references: `npu/nvdla/hw/` and `npu/nvdla/doc/` (integration guide).

### 2.2 DMA model
- Validate that the **DMA capabilities** align conceptually with NVDLA’s bulk
  tensor movement model.
- Confirm support for **strided** and/or **gather/scatter** semantics used in
  modern tensor layouts (KV paging, tiling).

Checklist:
- `DMA_COPY`, `DMA_STRIDED`, `DMA_GATHER`, `DMA_SCATTER` exist in spec.
- If NVDLA only supports a subset, document the delta.

### 2.3 Events and interrupts
- Verify a **fence/event model** for ordering and a standard **IRQ** path.
- Confirm error reporting hooks.

Checklist:
- `EVENT_SIGNAL`/`EVENT_WAIT` in `npu/shell/spec.md`.
- IRQ status/enable registers are defined.

## 3) Key differences vs. NVDLA (expected)

| Area | NVDLA Baseline | RTLGen NPU Shell (v0.1) | Expected Impact |
|---|---|---|---|
| Compute focus | Convolution/feature maps | GEMM + LLM ops | Different op encodings |
| Commanding | Register-programmed engines | Queue of fixed-size descriptors | Adapter layer in UMD |
| Data movement | Convolution-centric DMA | General DMA with gather/scatter | Better for KV layouts |
| ISA/ops | NVDLA engine set | Minimal GEMM/VEC/Softmax ops | Mapper defines semantics |

**Interpretation:** the shell is intentionally NVDLA-like in **integration
shape**, but not functionally identical. This is by design for LLM workloads.

## 4) Practical validation steps

1) **Doc-level comparison**
   - Cross-check `npu/shell/spec.md` against NVDLA integration docs to ensure
     you have the same SoC hooks (MMIO, DMA, IRQ).

2) **Driver interface mapping**
   - In the UMD/KMD layer, map NVDLA-style job submission to the queue model:
     - CSB register writes → queue writes + doorbell
     - NVDLA engine configuration → descriptor payloads

3) **Trace-level sanity**
   - Record a short NVDLA trace (if available) and confirm that the RTLGen NPU
     can express the same dataflow using DMA + GEMM/VEC ops, even if opcodes
     differ.

4) **Error/interrupt behavior**
   - Validate IRQs and error codes via a small “golden” stream (see
     `npu/shell/spec.md`).

## 5) Open questions to resolve early
- Do we need an explicit **CSB compatibility layer**, or is a clean “NPU v1”
  ABI acceptable for software?
- Should the command queue accept **variable-size descriptors** (v0.2), similar
  to NVDLA’s richer parameter blocks?
- Which subset of NVDLA SW/UMD concepts (loadables, tasks) should we reuse?

## 6) Next artifacts to create
- A short **compatibility checklist** in `npu/docs/` that is updated as the
  shell evolves.
- A **driver adapter sketch** showing how NVDLA tasks map to queue descriptors.

## 7) What to Borrow vs. Ignore (Keep It Simple)
If you want the simplest viable interface, treat NVDLA as a **reference for
integration habits**, not as an architectural template.

### Borrow (low risk, high value)
- **Control-plane shape**: MMIO status/control, doorbell, IRQ masking.
- **DMA expectations**: strided copies and robust error reporting.
- **Reset/clock/IRQ integration**: predictable SoC-level hooks.
- **Tooling discipline**: versioning, reproducible configs, and traceability.

### Ignore (unless you have a specific need)
- **Convolution engine topology** and pipeline microarchitecture.
- **NVDLA opcodes and loadable formats** (not needed for GEMM-first).
- **NVDLA SW runtime assumptions** about layers/graphs.

### Practical takeaway
You can keep a clean, minimal queue+descriptor ABI and still be “NVDLA‑compatible”
in the only way that matters for integration: **MMIO + DMA + IRQ behavior**.
The AXI-Lite wrapper in `npu/rtlgen/` provides a concrete MMIO bridge for SoC
integration without adopting NVDLA opcodes or microarchitecture.

## Next steps
- Review NVDLA integration guide for reset/clock/IRQ conventions once OpenROAD flow starts.
