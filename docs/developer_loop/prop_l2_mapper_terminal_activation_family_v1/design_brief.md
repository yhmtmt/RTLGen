# Design Brief

## Proposal
- `proposal_id`: `prop_l2_mapper_terminal_activation_family_v1`
- `title`: `Terminal activation-family direct output`

## Problem
- direct terminal-output is now accepted for:
  - final GEMM tails
  - terminal linear plus terminal `Relu`
  - standalone terminal `Relu` vec-op tails
- the next unsupported area is a broader nonlinear terminal activation family
- this is still a mapper and legality question, not a broad architecture ranking
  question

## Hypothesis
- a bounded nonlinear terminal activation family can establish clean non-fused
  reference points first, then show a direct-output win on those same points
- the first proof should stay on fixed `fp16_nm1` and require a quality gate
  before remote spend

## Evaluation Scope
- direct comparison set:
  - measurement-only non-fused `nm1` reference metrics on a bounded nonlinear
    terminal activation suite
  - paired direct-output vs non-fused `nm1` comparison on the same suite
- evaluation modes:
  - first-stage item: `measurement_only`
  - second-stage item: `paired_comparison`
  - expected first-stage result: record clean reference metrics and legality
    evidence without proposal judgment
  - expected second-stage result: direct output should improve at least part of
    the bounded nonlinear activation suite
- dependency order:
  - the paired item depends on
    `l2_prop_l2_mapper_terminal_activation_family_v1_nm1_measurement_r1`
  - it requires both merged inputs and materialized repo refs before export
- excluded first-stage comparisons:
  - `nm1` vs `nm2`
  - broad ranking across architecture points
  - broader activation-family claims outside the chosen first-pass nonlinear
    family
- follow-on broad sweep:
  - only if the bounded activation-family comparison is positive or mixed
    enough to justify reintegration

## Knowledge Inputs
- `docs/developer_loop/prop_l2_mapper_terminal_vecop_direct_output_v1/analysis_report.md`
- merged evidence from PRs `#58` and `#61`
- discussion on 2026-03-19 about dependency ordering and measurement-only
  evaluation modes

## Candidate Direction
- pick the smallest nonlinear activation family beyond standalone `Relu`
- likely first pass:
  - terminal `Sigmoid`
  - optional second member only if the family stays small enough for clear
    quality-gate reasoning
- keep the architecture fixed to plain `fp16_nm1`
- require local quality-gate evidence before queueing the first remote item

## Direction Gate
- status: approved
- approved_by: user
- approved_utc: 2026-03-19T11:20:00Z
- note: Approved to proceed with a bounded nonlinear terminal activation-family
  mapper proposal using staged dependency-ordered evaluation.
