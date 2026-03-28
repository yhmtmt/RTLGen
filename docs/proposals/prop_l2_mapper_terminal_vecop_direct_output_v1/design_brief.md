# Design Brief

## Proposal
- `proposal_id`: `prop_l2_mapper_terminal_vecop_direct_output_v1`
- `title`: `Terminal vec-op direct output`

## Problem
- direct terminal-output is now accepted for final GEMM and final GEMM+`Relu`
  tails on fixed `nm1`
- that still leaves a gap for broader terminal-op claims because terminal
  standalone vec-op style tails do not yet have a bounded direct-output path
- the next clean question is therefore mapper-specific: can a minimal terminal
  vec-op family be brought into the same measurement-first, paired-comparison
  workflow without reopening ranking noise

## Hypothesis
- a bounded terminal vec-op family can establish clean non-fused reference
  points first, then show a direct-output win on those same points
- the first proof should stay on fixed `fp16_nm1` and defer broader ranking

## Evaluation Scope
- direct comparison set:
  - measurement-only non-fused `nm1` reference metrics on a bounded terminal
    vec-op suite
  - paired direct-output vs non-fused `nm1` comparison on the same suite
- evaluation modes:
  - first-stage item: `measurement_only`
  - second-stage item: `paired_comparison`
  - expected first-stage result: record clean reference metrics and legality
    evidence without proposal judgment
  - expected second-stage result: direct output should improve at least part of
    the bounded terminal vec-op suite
- excluded first-stage comparisons:
  - `nm1` vs `nm2`
  - broad ranking across architecture points
  - broader terminal-op support claims outside the chosen vec-op family
- follow-on broad sweep:
  - only if the bounded vec-op comparison is positive or mixed enough to
    justify reintegration

## Knowledge Inputs
- `docs/proposals/prop_l2_mapper_terminal_op_generalization_v1/analysis_report.md`
- merged evidence from PRs `#54` and `#56`
- discussion on 2026-03-18 about stepping next to broader terminal-op family
  support instead of ranking

## Candidate Direction
- pick the smallest terminal vec-op family that is not already covered by final
  GEMM epilogue handling
- first bounded family: standalone terminal `Relu`, including one
  `Flatten -> Relu` prelude case to keep the proof on a real imported-graph
  shape rather than a hand-authored schedule only
- keep the architecture fixed to plain `fp16_nm1` for the first pass
- record non-fused references first and require schedule-level evidence before
  any broader remote spend

## Direction Gate
- status: approved
- approved_by: user
- approved_utc: 2026-03-18T14:05:00Z
- note: Approved to proceed with a measurement-first mapper proposal for
  terminal vec-op direct-output support.
