# Terminal-output overlap probe

- item_id: `item_eval_terminal_output_overlap_probe_v1`
- layer: `cross`
- kind: `architecture`
- status: `promoted_to_proposal`
- priority: `high`
- owner: `developer_agent`
- created_utc: `2026-03-18T07:16:43Z`
- updated_utc: `2026-03-18T07:16:43Z`
- proposal_id: `prop_cross_terminal_output_overlap_probe_v1`
- proposal_path: `docs/developer_loop/prop_cross_terminal_output_overlap_probe_v1`
- triggered_by_proposal: `prop_l2_softmax_tile_fusion_v1`
- triggering_evidence:
  - `docs/developer_loop/prop_l2_softmax_tile_fusion_v1/analysis_report.md`
  - `docs/developer_loop/prop_l2_softmax_tile_fusion_v1/promotion_decision.json`
  - `control_plane/shadow_exports/l2_decisions/l2_prop_l2_softmax_tile_fusion_v1_nm1_focus_r2.json`
  - `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_softmax_macro_submit_v1/report.md`
  - `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_softmax_macro_fused_output_nm1_v1__l2_prop_l2_softmax_tile_fusion_v1_nm1_focus_r2/report.md`

## Problem
- the fused-output mechanism should help by removing the terminal intermediate
  memory hop, but the focused `nm1` evaluation showed no measurable latency or
  energy improvement
- the current evidence does not tell us whether the skipped hop is already
  hidden by overlap in the perf path or whether the benchmark is too small to
  expose the mechanism
- without that mechanism-level answer, a broader architecture sweep would add
  ranking noise without clarifying why the fused path stayed flat

## Candidate Idea
- run a bounded follow-on that proves or disproves the expected fused-output
  benefit by combining:
  - trace-based inspection of terminal DMA overlap and dependency behavior
  - a slightly more stress-relevant benchmark or campaign slice where terminal
    output traffic is more likely to sit on the critical path

## Why It Might Matter
- can distinguish "good mechanism hidden by workload/perf-model" from "no real
  fused-output benefit"
- prevents the fused-output proposal from stalling on an under-informative
  benchmark
- improves future proposal design by making terminal-memory sensitivity an
  explicit first-stage proof choice

## Required Work
- l1 change: no
- l2 change: no new hardware required for the first pass
- mapper change: possibly no, unless the follow-on requires a dedicated
  benchmark-lowering tweak
- quality gate required: no new numerical gate expected if the follow-on stays
  within equivalent output semantics

## Evaluation Sketch
- local:
  - inspect emitted schedules and perf traces for `dma_y` overlap and event
    ordering
  - identify or synthesize a benchmark slice where terminal output traffic is a
    larger share of total time
  - validate that the comparison still isolates the fused-output mechanism
- remote:
  - first-stage: compare `{non-fused, fused}` on one fixed architecture under a
    terminal-output-stressing benchmark or validated no-overlap proof setup
  - follow-on broad sweep only if that focused mechanism proof is positive or
    still ambiguous

## Inputs / Sources
- `docs/developer_loop/prop_l2_softmax_tile_fusion_v1/analysis_report.md`
- `docs/developer_loop/prop_l2_softmax_tile_fusion_v1/promotion_decision.json`
- `control_plane/shadow_exports/l2_decisions/l2_prop_l2_softmax_tile_fusion_v1_nm1_focus_r2.json`
- `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_softmax_macro_submit_v1/`
- `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_softmax_macro_fused_output_nm1_v1__l2_prop_l2_softmax_tile_fusion_v1_nm1_focus_r2/`
- discussion on 2026-03-18 about proving whether fused-output benefit is hidden
  by overlap or benchmark shape

## Open Questions
- is terminal `dma_y` already overlapped enough that removing it cannot change
  the current critical path?
- which benchmark family or shape most cleanly stresses terminal output traffic
  without turning the proposal into a broad workload sweep?
- should the next proof be framed as perf-model validation, benchmark-suite
  expansion, or a narrow fused-output reevaluation?

## Promotion Rule
- promote when the scope is bounded to a mechanism-level proof of the fused
  terminal-output benefit, the direct comparison set is explicit, and the
  proposal avoids broad nm1/nm2 ranking until the overlap-vs-benchmark question
  is answered

## Promotion Outcome
- promoted to `docs/developer_loop/prop_cross_terminal_output_overlap_probe_v1`
- promotion rationale:
  - PR `#41` established valid but flat fused-output evidence on the focused
    `nm1` proof
  - the next question is now cross-cutting and mechanism-oriented: overlap
    modeling vs benchmark sensitivity
