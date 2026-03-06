# Mapper Model Split Plan (Large ONNX)

## Purpose
Enable mapper execution for models that do not fit monolithically in on-chip
SRAM by introducing deterministic split/tiling in mapping phase.

## Current status
- **Implemented baseline**: phase-1 split support is active in
  `npu/mapper/onnx_to_schedule.py` for the current MLP lowering path when
  `GEMM2` weights/bias exceed available `weight_sram`.
- The emitted schedule now carries `mapper_notes.gemm2_*` provenance, and
  campaign rows can surface that split metadata for filtering/reporting.
- Regression coverage exists in:
  - `tests/test_mapper_split.py`
  - `tests/test_run_campaign_mapper_notes.py`

## Problem statement
- Current split support is still narrow: it is tied to the present MLP lowering
  shape and output-channel chunking only.
- Other SRAM-fit failures can still stop mapping with a hard failure.
- Broader practical ONNX coverage requires more general tiling/splitting than
  the current phase-1 path.

## Phase-1 split policy (implemented baseline)
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
1. Generalize the split analyzer/helper beyond `GEMM2`-only assumptions.
2. Support additional axes (M/K) and/or multi-layer chain handling where legal.
3. Keep schedule metadata/report fields recording split decisions and
   unsupported-case diagnostics.
4. Add more intentional-overflow regression cases beyond the current baseline.

## Immediate next step
Expand beyond the current MLP `GEMM2` N-axis chunking path while preserving
deterministic dependencies, event ordering, and current passing regressions.
