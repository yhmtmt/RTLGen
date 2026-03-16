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
  - compare against the current softmax-tail baselines
  - use the existing campaign family first
  - measure balanced and latency objectives before considering broader rollout

## Direction Gate
- status: pending
- approved_by:
- approved_utc:
- note: pending human decision on whether this direction is worth implementation and mapper work
