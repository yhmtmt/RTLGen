# Design Brief

## Proposal
- `proposal_id`: `prop_l2_mapper_terminal_op_generalization_v1`
- `title`: `Generalized terminal-op direct output`

## Problem
- the accepted fused terminal-output win is currently proven only on a bounded
  softmax-tail family
- the active mapper rule is still specialized to terminal `Softmax`, so any
  broader claim would currently mix mechanism generalization with unsupported
  lowering behavior
- the next clean question is therefore mapper-specific: can the direct-output
  rule be generalized to a small eligible terminal-op family without reopening
  broad ranking too early

## Hypothesis
- a bounded mapper generalization can extend direct terminal output beyond
  `Softmax` on the existing `nm1` hardware
- that proof should be staged as measurement-only non-fused references first,
  then a paired direct-output comparison on those same points

## Evaluation Scope
- direct comparison set:
  - measurement-only non-fused `nm1` reference metrics on a minimal generalized
    terminal-op suite
  - paired direct-output vs non-fused `nm1` comparison on the same suite
- evaluation modes:
  - first-stage item: `measurement_only`
  - second-stage item: `paired_comparison`
  - expected first-stage result: record reference metrics and legality evidence
    without proposal judgment
  - expected second-stage result: direct output should improve at least part of
    the bounded terminal-op suite
- excluded first-stage comparisons:
  - `nm1` vs `nm2`
  - broad ranking across architecture points
  - broad non-MLP model support claims outside the chosen first-pass terminal
    op family
- follow-on broad sweep:
  - only if the generalized terminal-op comparison is positive or mixed enough
    to justify reintegration

## Knowledge Inputs
- `docs/developer_loop/prop_cross_non_mlp_terminal_suite_v1/analysis_report.md`
- merged evidence from PRs `#49` and `#52`
- discussion on 2026-03-18 about measurement-only and baseline-refresh items

## Candidate Direction
- choose the smallest new terminal-op family that exercises mapper
  generalization beyond softmax-only direct output
- keep the architecture fixed to `nm1` for the first pass
- require schedule-level evidence and quality checks before any broader remote
  spend

## Direction Gate
- status: approved
- approved_by: user
- approved_utc: 2026-03-18T13:25:00Z
- note: Approved to proceed with a mapper-generalization proposal that stages
  measurement-only reference collection before the paired comparison.
