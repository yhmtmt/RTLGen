# Design Brief

## Proposal
- `proposal_id`: `prop_l1_npu_dense_gemm_tile_v1`
- `title`: `Dense FP16 GEMM tile V1`

## Problem
The Llama7B compute-ceiling envelope shows that measured `nm64_flat` density
does not reach the HBM-bound floor. We need to determine whether a regular
dense compute tile can improve density before exploring larger clustered
memory/NoC schedules.

## Architecture
- exact RTLGen FP16 MAC primitive reused from corrected compute baseline.
- `4x4` and `8x8` MAC arrays.
- narrow self-stimulating wrapper: `clk`, `rst_n`, `start`, `seed`,
  `done`, and `result_hash`.
- all MAC outputs feed the visible result hash to prevent synthesis pruning.
- no dynamic dispatcher, CQ, DMA, softmax, norm, reducer, or vector tail.

## Direction Gate
- status: approved
- approved_by: developer_agent
- approved_utc: 2026-06-03T10:55:00Z
