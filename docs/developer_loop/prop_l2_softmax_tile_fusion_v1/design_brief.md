# Design Brief

## Proposal
- `proposal_id`: `prop_l2_softmax_tile_fusion_v1`
- `title`: `Softmax-tail fused tile path`

## Problem
- The current softmax-tail path already has a softmax-integrated Layer 2 baseline,
  but the evidence still suggests overhead around descriptor movement, staging,
  and mapper assumptions rather than a clearly optimized softmax-specific tile.
- Current winning points prove the baseline is workable, but they do not answer
  whether a more specialized softmax-oriented architecture can outperform the
  existing `fp16_nm1_softmax_r4` style points enough to justify its added area
  and mapper complexity.
- We need a bounded proposal that can answer that question without expanding
  into a broad architecture rewrite.

## Hypothesis
- A fused softmax-tail tile that treats the softmax-heavy tail path as a first-class
  architectural pattern should reduce descriptor traffic and memory movement on
  imported softmax-tail workloads.
- If the mapper can express the new legality and scheduling rules cleanly, the
  resulting architecture may improve latency enough to justify the added hardware.
- This should be tested as a focused Layer 2 architecture proposal, not as a
  broad NPU redesign.

## Evaluation Scope
- direct comparison set:
  - current `fp16_nm1_softmax_r4` softmax baseline
  - fused-output candidate on the same `fp16_nm1_softmax_r4` hardware
- excluded first-stage comparisons:
  - `fp16_nm2_softmax_r4`
  - broad architecture ranking across both module-count points
- follow-on broad sweep:
  - reintroduce `nm2` only if the focused nm1 fusion result is positive or
    still ambiguous after the first-stage proof

## Knowledge Inputs
- `npu/docs/status.md`
- `npu/docs/workflow.md`
- `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_num_modules_v1/`
- `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_softmax_macro_submit_v1/`
- `runs/designs/activations/softmax_rowwise_int8_r4_wrapper/metrics.csv`
- discussion on 2026-03-15 about notebook-side autonomous development and
  softmax-specific architectural exploration

## Candidate Direction
- Add a new Layer 2 architecture direction optimized specifically for the
  imported softmax-tail workload family.
- Treat the proposal as a combined architecture-plus-mapper effort:
  - architecture agent proposes the fused tile path
  - mapping agent adds the legality/lowering rules needed to evaluate it
- Keep the evaluation bounded:
  - first prove the fusion effect on `nm1` only
  - defer `nm2` and broader architecture ranking until after the focused proof
  - use balanced and latency views only inside that first-stage direct
    comparison before considering broader rollout

## Direction Gate
- status: approved
- approved_by: user
- approved_utc: 2026-03-16T03:05:12Z
- note: Approved to proceed with bounded implementation of the softmax-tail fused tile direction, including the required mapper work.
