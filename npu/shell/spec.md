# NPU Shell Contract (v0.1 Draft)

## Purpose
This document defines the host-visible control plane and DMA behavior shared by
RTLGen-generated NPUs. It is intended to be stable enough for RTL, mapper, and
simulator integration, while allowing future extensions.

## Current status
- v0.1 descriptor format and MMIO register map are implemented in RTL.
- AXI-Lite wrapper is available for MMIO integration tests.

## 1. Terminology
- **Host**: CPU-side software that programs the NPU.
- **NPU**: Device executing commands and DMA transfers.
- **Queue**: Command ring buffer in host memory.
- **Event**: Fence-like primitive for dependency ordering.
- **Descriptor**: Fixed-size command structure placed in the queue.

## 2. MMIO Register Map (Baseline)
All registers are 32-bit unless noted. All offsets are from the NPU base MMIO
address. Access rules: aligned 32-bit loads/stores; byte enables are ignored.

Implementation note: the RTL generator can emit an AXI-Lite wrapper
(`top_axi.v`) that maps these registers to a standard AXI-Lite slave interface.

| Offset | Name | Description |
|---:|---|---|
| 0x0000 | VERSION | [31:16] major, [15:0] minor |
| 0x0004 | CAPABILITIES | Bitfield of supported features |
| 0x0008 | STATUS | Device status (idle, busy, error) |
| 0x000C | CONTROL | Global control (reset, halt, resume) |
| 0x0010 | IRQ_STATUS | Interrupt status (W1C) |
| 0x0014 | IRQ_ENABLE | Interrupt enable mask |
| 0x0020 | CQ_BASE_LO | Command queue base, low 32 bits |
| 0x0024 | CQ_BASE_HI | Command queue base, high 32 bits |
| 0x0028 | CQ_SIZE | Queue size in bytes (power-of-two) |
| 0x002C | CQ_HEAD | Device read index (bytes) |
| 0x0030 | CQ_TAIL | Host write index (bytes) |
| 0x0040 | DOORBELL | Host writes to notify new commands |
| 0x0044 | ERROR_CODE | Sticky error code |
| 0x0048 | ERROR_ADDR_LO | Fault address low |
| 0x004C | ERROR_ADDR_HI | Fault address high |

### 2.1 Status bits (STATUS)
- bit 0: IDLE (1 when queue empty and no active work)
- bit 1: BUSY (1 when executing or DMA active)
- bit 2: ERROR (1 when ERROR_CODE is non-zero)

### 2.2 Control bits (CONTROL)
- bit 0: RESET (self-clearing reset pulse)
- bit 1: HALT (stop fetching new commands)
- bit 2: RESUME (clear HALT)

### 2.3 Interrupts
- IRQ bit 0: CQ_EMPTY (queue drained)
- IRQ bit 1: EVENT_SIGNAL (event signaled with IRQ flag)
- IRQ bit 2: ERROR (error latched)

## 3. Command Queue Format
The queue is a power-of-two byte ring in host memory. The device consumes
commands at CQ_HEAD and advances CQ_HEAD by each descriptor size. The host
writes descriptors at CQ_TAIL and advances CQ_TAIL. Queue empty when
CQ_HEAD == CQ_TAIL.

### 3.1 Descriptor header (common to all commands)
Each descriptor is 32 bytes, aligned to 32 bytes.

| Byte | Field | Description |
|---:|---|---|
| 0 | OPCODE | Command opcode |
| 1 | FLAGS | Command flags |
| 2 | SIZE | Descriptor size in 32B units (fixed to 1 for v0.1) |
| 3 | RESERVED | Must be 0 |
| 4..7 | TAG | Host tag for tracking |

### 3.2 Opcodes (v0.1)
- 0x01: DMA_COPY
- 0x02: DMA_STRIDED
- 0x03: DMA_GATHER
- 0x04: DMA_SCATTER
- 0x10: GEMM
- 0x11: VEC_OP
- 0x12: SOFTMAX
- 0x20: EVENT_SIGNAL
- 0x21: EVENT_WAIT
- 0x30: NOOP

## 4. DMA Descriptor Formats
All addresses are 64-bit. All sizes are in bytes unless noted. DMA engines
interpret source/destination addresses as system physical addresses.

### 4.1 DMA_COPY
Copies a contiguous byte range from SRC to DST.

| Byte | Field | Description |
|---:|---|---|
| 8..15 | SRC_ADDR |
| 16..23 | DST_ADDR |
| 24..27 | SIZE |
| 28..31 | RESERVED |

### 4.2 DMA_STRIDED
Copies a 2D region with row strides.

| Byte | Field | Description |
|---:|---|---|
| 8..15 | SRC_ADDR |
| 16..23 | DST_ADDR |
| 24..25 | ROW_BYTES |
| 26..27 | ROWS |
| 28 | SRC_STRIDE |
| 29 | DST_STRIDE |
| 30..31 | RESERVED |

### 4.3 DMA_GATHER / DMA_SCATTER
Reads or writes a list of base addresses plus lengths. The descriptor points
to a list in host memory.

| Byte | Field | Description |
|---:|---|---|
| 8..15 | LIST_ADDR |
| 16..19 | LIST_COUNT |
| 20..23 | ELEM_SIZE | Bytes per list entry |
| 24..31 | RESERVED |

Each list entry layout (ELEM_SIZE bytes) is:
- [0..7] base address
- [8..11] size (bytes)
- [12..15] reserved (or extension)

## 5. Compute Descriptor Formats
Compute descriptors are architectural placeholders for mapper/simulator. RTL
may implement only a subset initially.

### 5.1 GEMM
Required fields: A, B, C base addresses, M/N/K sizes, datatype and layout.

| Byte | Field | Description |
|---:|---|---|
| 8..15 | A_ADDR |
| 16..23 | B_ADDR |
| 24..31 | C_ADDR |

Additional parameters are encoded in the FLAGS field for v0.1:
- bits [3:0]: datatype (0=INT8, 1=FP16, 2=BF16, 3=FP8)
- bits [7:4]: layout (0=ROW_MAJOR, 1=COL_MAJOR)

Sizes are packed in TAG for v0.1 (M in [31:20], N in [19:10], K in [9:0]).
This is intentionally temporary; a v0.2 descriptor will add explicit fields.

#### 5.1.1 GEMM Contract (Proposed v0.2)
The nominal GEMM interface adds explicit shape/stride fields and optional
epilogue parameters. This is the **target contract** for the compute tile.

Required fields (v0.2 descriptor, SIZE=2):
- A_ADDR, B_ADDR, C_ADDR (u64)
- M, N, K (u16/u32, explicit fields)
- LDA/LDB/LDC (u32 bytes, leading dimension/stride per row)

Optional fields:
- BATCH (u16, for batched GEMM)
- TRANSPOSE_A / TRANSPOSE_B (flags)
- ALPHA / BETA (fp16/fp32 encoded, optional)
- BIAS_ADDR (u64, optional)
- EPILOGUE (enum: NONE, RELU, GELU, ADD, MUL)

Notes:
- v0.2 expands the descriptor to carry these fields; v0.1 remains packed in TAG.
- Mapper and perf sim should treat missing optional fields as defaults.

Header extension plan (v0.2):
- The 32-bit TAG field (bytes 4..7) is repurposed as a **GEMM_EXT** word when
  SIZE > 1. This leaves the header format unchanged while adding 4 bytes for
  options.
- GEMM_EXT bit layout (proposed):
  - [3:0]  EPILOGUE (0=NONE, 1=RELU, 2=GELU, 3=ADD, 4=MUL)
  - [4]    TRANSPOSE_A
  - [5]    TRANSPOSE_B
  - [6]    HAS_BIAS
  - [7]    HAS_ALPHA
  - [8]    HAS_BETA
  - [15:9] RESERVED (future)
  - [31:16] USER_TAG (opaque host tag, optional)
- For v0.1 (SIZE=1), TAG keeps its current packed M/N/K encoding.

#### 5.1.2 GEMM Descriptor Layout (v0.2, SIZE=2)
Base v0.2 GEMM uses a 64B descriptor (SIZE=2). TAG becomes GEMM_EXT (above).

| Byte | Field | Description |
|---:|---|---|
| 0 | OPCODE | 0x10 |
| 1 | FLAGS | dtype/layout (same as v0.1) |
| 2 | SIZE | 0x02 |
| 3 | RESERVED | 0 |
| 4..7 | GEMM_EXT | option bits (see 5.1.1) |
| 8..15 | A_ADDR | u64 |
| 16..23 | B_ADDR | u64 |
| 24..31 | C_ADDR | u64 |
| 32..35 | M | u32 |
| 36..39 | N | u32 |
| 40..43 | K | u32 |
| 44..47 | LDA | u32 bytes |
| 48..51 | LDB | u32 bytes |
| 52..55 | LDC | u32 bytes |
| 56..63 | RESERVED | for future extension |

#### 5.1.3 GEMM Optional Extension (v0.2, SIZE=3)
If any of {HAS_BIAS, HAS_ALPHA, HAS_BETA} is set, SIZE=3 (96B) and the final
32B carry optional fields:

| Byte | Field | Description |
|---:|---|---|
| 64..71 | BIAS_ADDR | u64 (optional) |
| 72..75 | ALPHA | fp32 (optional) |
| 76..79 | BETA | fp32 (optional) |
| 80..95 | RESERVED | for future extension |

### 5.2 VEC_OP
Vector unary/binary ops, such as activation and normalization.

| Byte | Field | Description |
|---:|---|---|
| 8..15 | SRC_ADDR |
| 16..23 | DST_ADDR |
| 24..27 | SIZE |
| 28..31 | RESERVED |

FLAGS encode op type (ReLU, GELU, RMSNorm) and datatype.

### 5.3 SOFTMAX
Row-wise softmax with optional scaling.

| Byte | Field | Description |
|---:|---|---|
| 8..15 | SRC_ADDR |
| 16..23 | DST_ADDR |
| 24..25 | ROW_BYTES |
| 26..27 | ROWS |
| 28..31 | RESERVED |

## 6. Event Model
Events are 16-bit IDs scoped to a queue. The host manages ID reuse.

- EVENT_SIGNAL: sets an event to signaled state; can raise IRQ if FLAGS[0]=1.
- EVENT_WAIT: stalls command processing until the event is signaled.
- Events are auto-cleared after a successful EVENT_WAIT.

## 7. Error Reporting
On error, the device sets STATUS.ERROR, latches ERROR_CODE and ERROR_ADDR, and
raises IRQ_ERROR if enabled.

### 7.1 Error codes (v0.1)
- 0x0001: INVALID_OPCODE
- 0x0002: BAD_DESCRIPTOR
- 0x0003: DMA_FAULT
- 0x0004: ALIGNMENT_ERROR
- 0x0005: TIMEOUT

## 8. Capability Flags (CAPABILITIES)
- bit 0: DMA_COPY
- bit 1: DMA_STRIDED
- bit 2: DMA_GATHER
- bit 3: DMA_SCATTER
- bit 4: GEMM
- bit 5: VEC_OP
- bit 6: SOFTMAX
- bit 7: EVENT_IRQ

## 9. Compatibility and Versioning
- v0.1 descriptors are fixed-size (32B) and aligned to 32B.
- Future revisions may introduce extended descriptors with SIZE > 1.
- Backward compatibility: unknown opcodes must raise INVALID_OPCODE.

## 10. Open Items (for v0.2)
- Explicit GEMM shape fields and stride parameters.
- Formal datatype/layout enums in a shared header.
- Multi-queue support and context IDs.
- Memory protection/IOMMU hooks.

## Next steps
- Promote v0.2 fields once the mapper and simulator need them.
- Align error reporting with OpenROAD and simulation artifacts.

## 11. Golden Command Stream Example (v0.1)
This example assumes:
- Queue base = 0x00000010_00000000, size = 0x1000 bytes
- CQ_HEAD = CQ_TAIL = 0 at start
- CAPABILITIES includes DMA_COPY, GEMM, EVENT_IRQ

### 11.1 Host setup (MMIO)
1) Write CQ_BASE_LO = 0x00000000
2) Write CQ_BASE_HI = 0x00000010
3) Write CQ_SIZE = 0x00001000
4) Write IRQ_ENABLE = (1 << 1) | (1 << 2)

### 11.2 Queue contents (three descriptors, 32B each)
Descriptor 0: DMA_COPY (copy 4KB from A to B)
- OPCODE = 0x01, FLAGS = 0x00, SIZE = 0x01, TAG = 0x00000001
- SRC_ADDR = 0x00000020_00000000
- DST_ADDR = 0x00000020_00001000
- SIZE = 0x00001000

Descriptor 1: GEMM (INT8, row-major, M=64, N=64, K=64)
- OPCODE = 0x10, FLAGS = 0x00, SIZE = 0x01, TAG = pack(M,N,K)
- A_ADDR = 0x00000030_00000000
- B_ADDR = 0x00000030_00100000
- C_ADDR = 0x00000030_00200000

Descriptor 2: EVENT_SIGNAL (event 3, with IRQ)
- OPCODE = 0x20, FLAGS = 0x01, SIZE = 0x01, TAG = 0x00000003

### 11.3 Host tail update and doorbell
- CQ_TAIL = 0x00000060 (3 * 32B)
- Write DOORBELL = 1

### 11.4 Expected behavior
- Device copies 4KB, runs GEMM, then signals event 3.
- IRQ bit 1 fires (EVENT_SIGNAL), CQ_HEAD advances to 0x00000060.
