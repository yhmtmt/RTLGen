# Shell Spec Work Log (v0.1)

This log captures the initial work done around the NPU shell specification
and the related mapper artifacts that align to it.

## 1) Shell spec updates
- `npu/shell/spec.md` expanded from placeholder to **v0.1 draft**:
  - MMIO register map, status/control bits, IRQs
  - command queue semantics (ring buffer)
  - 32B descriptor header format
  - DMA descriptors (copy/strided/gather/scatter)
  - compute descriptors (GEMM/VEC/Softmax)
  - event model + error reporting
  - compatibility and versioning notes
- Added **golden command stream example** showing:
  - MMIO setup
  - three descriptors (DMA, GEMM, EVENT_SIGNAL)
  - tail update and expected behavior

## 2) NVDLA compatibility notes
- Added `npu/docs/nvdla_compatibility.md`:
  - Defines **compatibility scope** (integration model only)
  - Checklists for MMIO/DMA/IRQ alignment
  - Expected differences (conv vs GEMM, opcode formats)
  - “Borrow vs Ignore” guidance to keep ABI minimal

## 3) Mapper IR alignment
- `npu/mapper/ir.md` expanded to **v0.1 draft**:
  - YAML schedule IR aligned 1:1 with shell descriptors
  - dependencies modeled with events
  - validation rules and mapping notes

## 4) Mapper tooling
- Added `npu/mapper/validate.py`:
  - minimal IR validation checks
- Added `npu/mapper/run.py`:
  - emits YAML descriptors
  - emits **binary 32B descriptor stream** (`--out-bin`)
  - expands deps/events into queue commands
- Added example schedule:
  - `npu/mapper/examples/minimal_schedule.yml`
  - outputs YAML or binary descriptors
- Added `npu/mapper/Makefile`:
  - `example`, `example-bin`, `validate` targets

## 5) Status
The shell ABI is now stable enough to drive:
- a driver prototype (queue + doorbell)
- a lightweight RTL testbench (descriptor parsing)
- early mapper + simulator alignment
- an AXI-Lite wrapper for MMIO register access

## Next steps
- Add v0.2 descriptor fields when compute ops are implemented.
