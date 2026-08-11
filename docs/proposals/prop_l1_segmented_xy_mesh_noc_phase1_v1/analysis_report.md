# Analysis Report

## Candidate
- `proposal_id`: `prop_l1_segmented_xy_mesh_noc_phase1_v1`
- `candidate_id`: `l1_segmented_xy_mesh_noc_phase1_v1`

## Evaluations Consumed
- Pending remote Nangate45 evaluation from the exact finalized source commit.

## Baseline Comparison
- Legacy comparison: separately measured synthetic 4-port router and FIFO
  primitives.
- Candidate: the exact five-port router with four per-input VCs and depth-4
  buffering used by the merged 4x4 mesh RTL/model.

## Result
- Pending. No measured area, timing, or power claim is made before the result
  artifacts merge.

## Failures and Caveats
- This item is a single-router macro anchor, not aggregate 4x4 placement.
- Vectorless power will not close workload-specific NoC activity energy.
- SRAM endpoints and external memory are not part of this block.

## Recommendation
- Measure the primitive remotely, consume it in the Phase 2 schedule recost,
  then evaluate whether aggregate 4x4 placement is required to bound wire cost.
