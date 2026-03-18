# Terminal-sensitive softmax suite

- item_id: `item_eval_non_mlp_terminal_suite_v1`
- layer: `cross`
- kind: `architecture`
- status: `promoted_to_proposal`
- priority: `high`
- owner: `developer_agent`
- created_utc: `2026-03-18T11:05:00Z`
- updated_utc: `2026-03-18T12:05:00Z`
- proposal_id: `prop_cross_non_mlp_terminal_suite_v1`
- proposal_path: `docs/developer_loop/prop_cross_non_mlp_terminal_suite_v1`
- triggered_by_proposal: `prop_cross_terminal_output_overlap_probe_v1`
- triggering_evidence:
  - `docs/developer_loop/prop_cross_terminal_output_overlap_probe_v1/analysis_report.md`
  - `docs/developer_loop/prop_cross_terminal_output_overlap_probe_v1/promotion_decision.json`
  - `control_plane/shadow_exports/l2_decisions/l2_prop_cross_terminal_output_overlap_probe_v1_nm1_baseline_r1.json`
  - `control_plane/shadow_exports/l2_decisions/l2_prop_cross_terminal_output_overlap_probe_v1_nm1_fused_r1.json`
  - `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_softmax_macro_submit_nm1_v2__l2_prop_cross_terminal_output_overlap_probe_v1_nm1_baseline_r1/report.md`
  - `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_softmax_macro_fused_output_nm1_v2__l2_prop_cross_terminal_output_overlap_probe_v1_nm1_fused_r1/report.md`

## Problem
- the fused terminal-output benefit is now proven on the corrected-contract
  `nm1` softmax-tail proof, but only for the tiny logistic-regression model
- the current mapper-supported ONNX subset in this repo is still centered on
  imported-style `Cast/Gemm/Softmax` classifier tails, so a true non-MLP suite
  would currently require a broader lowering item
- that leaves the next question unresolved: does the same fused benefit appear
  on a slightly broader terminal-sensitive softmax-tail slice, or was the proof
  too narrow to generalize
- broad architecture ranking is still too early unless we first establish the
  per-model terminal-output behavior on a small, intentional suite

## Candidate Idea
- build a small terminal-sensitive softmax-tail evaluation slice from local
  ONNX-lite generated classifier graphs, record corrected non-fused reference
  points first, then compare fused vs non-fused on those same models

## Why It Might Matter
- tests whether the fused win survives beyond the original tiny proof without
  opening a broader model-support change first
- gives a better basis for deciding whether broader architecture or workload
  sweeps are worth spending next
- fits the new evaluation model cleanly:
  - `measurement_only` or `baseline_refresh` to record corrected references
  - `paired_comparison` to emit the actual proposal judgment

## Required Work
- l1 change: no
- l2 change: likely no new hardware
- mapper change: not expected for the first pass
- quality gate required: only if the chosen models or lowering path can alter
  output semantics beyond the accepted fused/non-fused equivalence

## Evaluation Sketch
- local:
  - identify 2-3 terminal-sensitive models already available in the repo, or
    define a narrow locally generated imported-style softmax-tail slice
  - confirm the selected models keep the question focused on terminal-output
    behavior rather than reopening broad architecture ranking
- remote:
  - stage 1: `measurement_only` or `baseline_refresh` for corrected-contract
    non-fused `nm1` reference points on the chosen models
  - stage 2: `paired_comparison` for fused vs non-fused `nm1` on those same
    models
  - defer any `broad_ranking` sweep until the per-model comparison results are
    in

## Inputs / Sources
- `docs/developer_loop/prop_cross_terminal_output_overlap_probe_v1/analysis_report.md`
- `docs/developer_loop/prop_cross_terminal_output_overlap_probe_v1/promotion_decision.json`
- `npu/sim/perf/run.py`
- `npu/shell/spec.md`
- `npu/rtlgen/gen.py`
- merged evidence from PRs `#47` and `#48`
- discussion on 2026-03-18 about moving to metric-only first-stage evaluation

## Open Questions
- whether the first-stage suite should be a locally generated softmax-tail
  slice given the current mapper-supported ONNX subset
- whether the first remote stage should be `measurement_only` or
  `baseline_refresh` for those models
- whether any of the candidate models require a quality gate before remote
  spend

## Promotion Rule
- promote when the proposal is explicitly staged as:
  - point measurement or baseline refresh first
  - paired fused vs non-fused comparison second
  - broad ranking deferred until after the focused per-model evidence
