# Design Brief

## Proposal
- `proposal_id`: `prop_l2_mapper_memory_aware_split_v1`
- `title`: `Memory-aware split policy for multi-module softmax-tail mapping`

## Problem
- The current softmax-tail evaluation shows that `fp16_nm2_softmax_r4` is
  judged under one heuristic row-split lowering, while `fp16_nm1_softmax_r4`
  remains the winning point.
- That result is technically valid, but it does not cleanly separate hardware
  weakness from mapper weakness because the benchmark is small and the current
  heuristic may be injecting unnecessary synchronization overhead.
- We need a bounded mapper proposal that answers whether multi-module
  softmax-tail points are being evaluated fairly before drawing stronger
  architecture conclusions.

## Hypothesis
- A mapper policy that can choose between monolithic and split multi-module GEMM
  lowering, using simple sync and tail-cost signals, should reduce avoidable
  control overhead on small softmax-tail workloads.
- If that policy improves `fp16_nm2_softmax_r4` materially on the existing
  `softmaxcmp` hardware, then the prior architecture result should remain in
  `iterate` rather than being interpreted as a hardware loss.
- If the bounded mapper alternatives still do not close the gap, the negative
  architecture conclusion becomes higher-confidence.

## Evaluation Scope
- direct comparison set:
  - prior `fp16_nm2_softmax_r4` fused-output run under the old row-split
    heuristic
  - updated `fp16_nm2_softmax_r4` run under the bounded mapper chooser
- excluded first-stage comparisons:
  - `fp16_nm1_softmax_r4`
  - broad cross-architecture ranking across both module-count points
- follow-on broad sweep:
  - re-run `nm1` and `nm2` together only after the local `nm2` mapper effect
    is established or remains ambiguous

## Knowledge Inputs
- `docs/developer_loop/prop_l2_softmax_tile_fusion_v1/analysis_report.md`
- `docs/developer_loop/prop_l2_softmax_tile_fusion_v1/promotion_decision.json`
- `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_softmax_macro_submit_v1/`
- `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_softmax_macro_fused_output_v1__l2_prop_l2_softmax_tile_fusion_v1_20260316051355/`
- discussion on 2026-03-17 about mapper optimality and benchmark-shape-aware
  evaluation
- `npu/docs/workflow.md`

## Candidate Direction
- Add a bounded mapper-only update for `softmaxcmp` multi-module hardware:
  - keep the existing hardware fixed
  - compare monolithic and row-split lowering on the same benchmark family
  - introduce a simple chooser based on estimated synchronization and terminal
    softmax tail cost
- Keep the scope narrow:
  - first prove the mapper effect on `nm2` only
  - defer `nm1` and broader architecture ranking until after the focused proof
  - no new RTL or architecture config for the first pass
  - no broad mapper rewrite
  - no new benchmark family until the current ambiguity is resolved

## Direction Gate
- status: pending
- approved_by:
- approved_utc:
- note:
