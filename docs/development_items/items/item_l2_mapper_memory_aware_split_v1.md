# Memory-aware split policy

- item_id: `item_l2_mapper_memory_aware_split_v1`
- layer: `layer2`
- kind: `mapper`
- status: `promoted_to_proposal`
- priority: `high`
- owner: `developer_agent`
- created_utc: `2026-03-17T00:00:00Z`
- updated_utc: `2026-03-17T13:10:00Z`
- proposal_id: `prop_l2_mapper_memory_aware_split_v1`
- proposal_path: `docs/developer_loop/prop_l2_mapper_memory_aware_split_v1`
- triggered_by_proposal: `prop_l2_softmax_tile_fusion_v1`
- triggering_evidence:
  - `docs/developer_loop/prop_l2_softmax_tile_fusion_v1/analysis_report.md`
  - `docs/developer_loop/prop_l2_softmax_tile_fusion_v1/promotion_decision.json`
  - `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_softmax_macro_submit_v1/report.md`
  - `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_softmax_macro_fused_output_v1__l2_prop_l2_softmax_tile_fusion_v1_20260316051355/report.md`

## Problem
- the current multi-module mapper heuristic row-splits the tiny softmax-tail
  GEMM on `fp16_nm2_softmax_r4` by default
- that split adds synchronization overhead while preserving the same serial
  softmax tail, making the architecture comparison sensitive to one ad hoc
  lowering decision
- the current architecture result therefore answers "how this heuristic
  performs" more strongly than it answers "how good the hardware is"

## Candidate Idea
- add a bounded mapper policy for dedicated-softmax multi-module designs that
  compares at least:
  - monolithic GEMM lowering
  - current row-split lowering
  - a simple objective-aware chooser based on estimated sync and tail cost

## Why It Might Matter
- can separate mapper inefficiency from true architecture weakness
- can prevent multi-module hardware from being rejected prematurely on
  small-tail workloads
- provides a reusable mapper policy for later architecture proposals that reuse
  the same `softmaxcmp` hardware family

## Required Work
- l1 change: no
- l2 change: no new hardware required for the first pass
- mapper change: yes
- quality gate required: no new numerical gate expected if only schedule shape
  changes and tensor semantics remain unchanged

## Evaluation Sketch
- local:
  - schedule regression covering monolithic vs split lowering choices
  - perf-trace inspection for queue/event overhead and terminal softmax overlap
  - campaign validation for generated bounded candidate schedules
- remote:
  - first-stage: compare `{old mapper, new mapper}` on
    `fp16_nm2_softmax_r4` only, using the same `softmaxcmp` physical design
    points
  - follow-on broad sweep only if the local `nm2` mapper effect is positive or
    still ambiguous after the focused proof

## Focused Comparison Set
- direct comparison:
  - prior `fp16_nm2_softmax_r4` fused-output run under the old row-split
    heuristic
  - updated `fp16_nm2_softmax_r4` run under the bounded monolithic-vs-split
    chooser
- intentionally excluded from first-stage evaluation:
  - `fp16_nm1_softmax_r4`
  - global architecture ranking across both module-count points
- follow-on only after a positive or ambiguous focused result:
  - re-run `nm1` and `nm2` together to see whether the local `nm2` mapper gain
    changes the broader architecture conclusion

## Inputs / Sources
- `docs/developer_loop/prop_l2_softmax_tile_fusion_v1/analysis_report.md`
- `docs/developer_loop/prop_l2_softmax_tile_fusion_v1/promotion_decision.json`
- `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_softmax_macro_submit_v1/`
- `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_softmax_macro_fused_output_v1__l2_prop_l2_softmax_tile_fusion_v1_20260316051355/`
- discussion on 2026-03-17 about mapper optimality becoming part of the
  architecture evaluation validity

## Open Questions
- when should `num_modules > 1` still choose monolithic lowering on tiny
  workloads?
- should the chooser optimize latency only, or also include queue/event cost
  and flow-runtime cost?
- do we need an explicit bounded search over mapper candidates rather than a
  single improved heuristic?

## Promotion Rule
- promote when the mapper scope is bounded to multi-module softmax-tail
  scheduling on the existing `softmaxcmp` hardware and the proposal names the
  exact nm2 baseline campaign family used to judge whether the heuristic change
  improved evaluation fidelity before any broader nm1/nm2 sweep

## Promotion Outcome
- promoted to `docs/developer_loop/prop_l2_mapper_memory_aware_split_v1`
- promotion rationale:
  - PR `#36` and its follow-on analysis established that the fused-output
    proposal is still mapper-confounded on `fp16_nm2_softmax_r4`
  - the next bounded question is mapper-specific rather than architectural
