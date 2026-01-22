# NPU Schedule IR (v0.1 Draft)

## Purpose
This document defines a minimal schedule IR emitted by the mapper. The IR is
intended to be **directly mappable** to the queue descriptors in
`npu/shell/spec.md`. The first version is YAML for readability; a JSON schema
may be added later.

## Current status
- Implemented in `npu/mapper/run.py` and `npu/mapper/validate.py`.

## 1. Goals
- Represent **compute + DMA** at the level of the shell command queue.
- Capture **dependencies** with explicit events.
- Be small enough to hand-author for tests.

## 2. Top-Level Structure
```yaml
version: 0.1
arch: path/to/arch.yml
buffers:
  - id: A
    addr: 0x0000003000000000
    bytes: 1048576
  - id: B
    addr: 0x0000003000100000
    bytes: 1048576
ops:
  - id: dma1
    type: dma_copy
    src: A
    dst: B
    bytes: 4096
  - id: gemm1
    type: gemm
    a: A
    b: B
    c: C
    m: 64
    n: 64
    k: 64
    dtype: int8
    layout: row_major
deps:
  - wait: [dma1]
    then: gemm1
events:
  - id: e_done
    signal_on: gemm1
```

## 3. Object Definitions

### 3.1 buffers[]
Describes memory objects used in ops.
- `id` (string): symbolic name
- `addr` (u64): base address
- `bytes` (u32): size

### 3.2 ops[]
Each op is mapped to one shell descriptor.

#### dma_copy
- `src` (buffer id)
- `dst` (buffer id)
- `bytes` (u32)

#### dma_strided
- `src`, `dst` (buffer ids)
- `row_bytes` (u16)
- `rows` (u16)
- `src_stride` (u8)
- `dst_stride` (u8)

#### dma_gather / dma_scatter
- `list_addr` (u64)
- `list_count` (u32)
- `elem_size` (u32)

#### gemm
- `a`, `b`, `c` (buffer ids)
- `m`, `n`, `k` (u16/u32; must fit in v0.1 packing)
- `dtype` (enum: int8, fp16, bf16, fp8)
- `layout` (enum: row_major, col_major)

#### vec_op
- `src`, `dst` (buffer ids)
- `bytes` (u32)
- `op` (enum: relu, gelu, rmsnorm, layernorm, add, mul)
- `dtype` (enum)

#### softmax
- `src`, `dst` (buffer ids)
- `row_bytes` (u16)
- `rows` (u16)
- `dtype` (enum)

#### event_signal
- `event_id` (u16)
- `irq` (bool)

#### event_wait
- `event_id` (u16)

## 4. Dependencies
Dependencies are declared by listing ops that must complete before another.
The mapper should emit explicit events to enforce ordering.

### 4.1 deps[] form
```yaml
deps:
  - wait: [op_a, op_b]
    then: op_c
```

### 4.2 Event expansion (mapper behavior)
For each `deps` entry, the mapper emits:
1) `event_signal` after each wait op (or a shared event)
2) `event_wait` before `then`

## 5. Mapping to Shell Descriptors
Each IR op maps 1:1 to a shell descriptor:
- `dma_*` → DMA descriptor
- `gemm` → GEMM descriptor
- `vec_op` → VEC_OP descriptor
- `softmax` → SOFTMAX descriptor
- `event_*` → EVENT descriptor

## 6. Validation Rules (v0.1)
- All buffer ids referenced by ops must exist in `buffers`.
- All `addr` must be 32B-aligned.
- All ops must have unique `id`.
- GEMM `m/n/k` must fit in TAG packing for v0.1.
- `deps` must reference existing op ids.

Status:
- v0.1 IR is implemented in `npu/mapper/run.py` and `npu/mapper/validate.py`.

## Next steps
- Add IR fields for GEMM strides and explicit descriptor sizes.
