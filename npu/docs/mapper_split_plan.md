# Mapper Model Split Plan (Large ONNX)

## Purpose
Enable mapper execution for models that do not fit monolithically in on-chip
SRAM by introducing deterministic split/tiling in mapping phase.

## Problem statement
- Current `npu/mapper/onnx_to_schedule.py` allocates full tensors for each MLP
  stage in SRAM regions.
- When a layer footprint exceeds SRAM capacity, mapping fails with
  `out of space in region ...` and campaign execution stops.
- This blocks scaling from smoke models to practical ONNX workloads.

## Phase-1 split policy (next implementation target)
- Target path: MLP chain lowered by `onnx_to_schedule.py`.
- Keep architecture fixed; solve fit at mapper level.
- If `W2` + `b2` does not fit `weight_sram`, split second GEMM by output
  channels (N-axis chunking).
- Emit repeated GEMM descriptors per chunk:
  - same input activation tile source,
  - chunk-local weight/bias DMA,
  - output writes to disjoint address ranges with deterministic offsets.
- Preserve functional equivalence and deterministic event ordering.

## Fit rule (phase-1)
For int8 MLP lowering:
- `bytes_w2 = hidden_dim * out_dim`
- `bytes_b2 = out_dim`
- choose `out_chunk` such that:
  `hidden_dim * out_chunk + out_chunk <= weight_sram_available`
- require `out_chunk > 0`, then iterate chunks until `out_dim` is covered.

## Deliverables
1. Mapper split analyzer helper with explicit fit report.
2. Chunked schedule emission in `onnx_to_schedule.py` for oversize cases.
3. Schedule metadata/report fields that record split decisions.
4. Regression case proving previous overflow model maps successfully.

## Immediate next step
Implement phase-1 N-axis chunking in `npu/mapper/onnx_to_schedule.py` and add
a regression test that previously failed with SRAM overflow.
