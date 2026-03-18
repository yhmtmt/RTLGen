# Design Brief

## Proposal
- `proposal_id`: `prop_cross_terminal_output_overlap_probe_v1`
- `title`: `Terminal-output overlap probe`

## Problem
- the focused `nm1` fused-output proof from `prop_l2_softmax_tile_fusion_v1`
  produced valid evidence but no measurable gain over the accepted non-fused
  baseline
- that flat result conflicts with the expected mechanism, because the fused path
  removes the terminal intermediate memory hop
- before spending more budget on broader architecture comparisons, we need to
  determine whether the skipped hop is already hidden by overlap or whether the
  benchmark simply does not stress terminal output traffic enough

## Hypothesis
- a bounded overlap-sensitive follow-on can prove or disprove the expected fused
  benefit more directly than the original tiny benchmark
- if the terminal memory hop is currently hidden by overlap, trace-based
  inspection should expose that and explain the flat result
- if benchmark shape is the limiting factor, a more terminal-output-sensitive
  proof setup on the same fixed architecture should reveal a measurable fused
  delta without needing a broad nm1/nm2 sweep

## Evaluation Scope
- direct comparison set:
  - non-fused vs fused execution on one fixed architecture under a
    terminal-output-sensitive proof setup
  - perf-trace or schedule evidence tied to that same focused comparison
- excluded first-stage comparisons:
  - `nm1` vs `nm2` architecture ranking
  - broad multi-workload evaluation
- follow-on broad sweep:
  - widen to a broader architecture or workload comparison only if the focused
    overlap-sensitive result is positive or still ambiguous

## Knowledge Inputs
- `docs/developer_loop/prop_l2_softmax_tile_fusion_v1/analysis_report.md`
- `docs/developer_loop/prop_l2_softmax_tile_fusion_v1/promotion_decision.json`
- `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_softmax_macro_submit_v1/`
- `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_softmax_macro_fused_output_nm1_v1__l2_prop_l2_softmax_tile_fusion_v1_nm1_focus_r2/`
- discussion on 2026-03-18 about proving whether fused-output benefit is hidden
  by overlap or benchmark shape

## Candidate Direction
- keep the hardware fixed and focus the next proof on mechanism visibility
- inspect emitted schedules and traces to determine whether terminal `dma_y`
  cost is already overlapped in the current perf path
- if needed, define a slightly more stress-relevant benchmark slice that keeps
  the same fused-output question but makes terminal traffic more visible on the
  critical path

## Direction Gate
- status: approved
- approved_by: user
- approved_utc: 2026-03-18T07:16:43Z
- note: Approved to proceed with a bounded mechanism-level follow-on after the
  merged fused-output evidence was recorded.
