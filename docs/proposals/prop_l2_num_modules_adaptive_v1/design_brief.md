# Design Brief

## Proposal
- `proposal_id`: `prop_l2_num_modules_adaptive_v1`
- `title`: `Adaptive num_modules selection for imported softmax-tail workloads`

## Problem
- The original imported softmax-tail `num_modules` campaign favored `fp16_nm1`
  over `fp16_nm2`, but that result predates the later accepted mapper fix that
  materially improved the `nm2` softmax-tail path.
- Keeping the old module-count conclusion as if it were still current would mix
  an outdated mapper baseline with a current architecture discussion.
- We need one clean architecture-level refresh that asks whether the old `nm1`
  win survives after the mapper confound has been reduced.

## Hypothesis
- A rerun of the original imported softmax-tail `num_modules` comparison under
  the current accepted mapper baseline will either:
  - confirm that `nm1` still clearly dominates, closing the question cleanly, or
  - show that `nm2` has recovered enough that module-count choice should be
    treated as adaptive rather than fixed.
- This is an architecture follow-on, not a new mapper proposal.

## Evaluation Scope
- direct comparison set:
  - historical `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_num_modules_v1`
  - a fresh rerun of that same campaign under the current code baseline
- included architecture points:
  - `fp16_nm1`
  - `fp16_nm2`
- excluded first-stage work:
  - new benchmark families
  - additional mapper heuristics
  - unrelated architecture changes

## Knowledge Inputs
- `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_num_modules_v1/report.md`
- `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_num_modules_v1/best_point.json`
- `docs/proposals/prop_l2_mapper_memory_aware_split_v1/analysis_report.md`
- `control_plane/shadow_exports/l2_decisions/l2_prop_l2_mapper_memory_aware_split_v1_nm2_focus_r2.json`
- `docs/proposals/prop_l2_softmax_tile_fusion_v1/promotion_decision.json`
- `npu/docs/workflow.md`

## Candidate Direction
- Reuse the existing imported softmax-tail `num_modules` campaign as the first
  evidence refresh.
- Keep the rerun architecture-only:
  - no new mapper work beyond what is already merged
  - no new hardware points beyond `nm1` and `nm2`
  - no broader benchmark expansion in the first pass
- Decide from that rerun whether a real adaptive `num_modules` policy is worth
  pursuing or whether the old fixed `nm1` conclusion still stands.

## Direction Gate
- status: approved
- approved_by: `user`
- approved_utc: `2026-04-15T00:00:00Z`
- note: Proceed with the narrow rerun of the existing imported softmax-tail `num_modules` campaign under the current mapper baseline.
