# Design Brief

## Proposal

- `proposal_id`: `prop_l1_npu_dense_gemm_tile_scaling_v3`
- `title`: `Dense FP16 GEMM tile depth scaling V3`

## Problem

PR #981 replaced the abstract Llama7B compute target with measured dense-tile
capacity and showed that the old `524288 MAC/cycle` point would require about
`1888.64512 mm2` of compute area. The corrected frontier is therefore limited
by exact-FP16 measured MAC density.

## Architecture

- exact RTLGen FP16 MAC primitive reused from dense tile V2.
- `16x16 k1 p2` baseline remeasured under the V3 floorplan.
- `16x16 k1 p1` pipeline comparison.
- `16x16 k2 p2` depth scaling point.
- `16x16 k4 p2` config is present but reserved for a later boundary dispatch.
- narrow self-stimulating wrapper with all MAC outputs folded into
  `result_hash`.
- no memory, NoC, producer, vector tail, softmax, normalization, or reducer.

## Direction Gate

- status: approved_after_source_merge
- dispatch: remote evaluator `eval-daemon-b7c2d9c80c1c`
