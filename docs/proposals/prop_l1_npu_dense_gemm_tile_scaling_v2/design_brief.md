# Design Brief

## Proposal
- `proposal_id`: `prop_l1_npu_dense_gemm_tile_scaling_v2`
- `title`: `Dense FP16 GEMM tile scaling V2`

## Problem
The 8x8 dense GEMM tile reached about `270 MAC/cycle/mm2`, enough to make the
Llama7B HBM floor plausible at the large 1200 mm2 / 60% logic point. We need to
know whether that density survives at 128 and 256 MAC/cycle tile sizes before
building a clustered dense compute hierarchy.

## Architecture
- exact RTLGen FP16 MAC primitive reused from the dense V1 tile.
- `8x16` and `16x8` p1 arrays for 128 MAC/cycle aspect-ratio comparison.
- `16x16` p2 array for first 256 MAC/cycle boundary point.
- narrow self-stimulating wrapper with all MAC outputs folded into
  `result_hash`.
- no memory, NoC, producer, vector tail, softmax, norm, or reducer.

## Direction Gate
- status: approved
- approved_by: developer_agent
- approved_utc: 2026-06-04T01:45:00Z
