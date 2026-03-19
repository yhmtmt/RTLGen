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
- this is not mapper-only: nonlinear terminal activations need a real Layer 1
  circuit and physical implementation before perf-sim evaluation is credible
- the next question is therefore staged:
  - first Layer 1 circuit proof
  - then Layer 2 mapper lowering on top of that accepted physical block

## Hypothesis
- a bounded nonlinear terminal activation family can establish clean non-fused
  reference points first, then show a direct-output win on those same points
- the first proof must start with a bounded Layer 1 `int8` sigmoid block so
  that later perf-sim comparisons use real measured physical parameters
- any native `fp16` nonlinear block should be treated as a later follow-on, not
  part of this first proof

## Evaluation Scope
- direct comparison set:
  - measurement-only non-fused `nm1` reference metrics on a bounded nonlinear
    terminal activation suite
  - paired direct-output vs non-fused `nm1` comparison on the same suite
- evaluation modes:
  - prerequisite first-stage item: Layer 1 `measurement_only` physical sweep
    for a bounded terminal `int8` sigmoid block
  - first Layer 2 item: `measurement_only`
  - second Layer 2 item: `paired_comparison`
  - expected Layer 1 result: accepted physical timing, power, and area for the
    bounded sigmoid block
  - expected first Layer 2 result: record clean reference metrics and legality
    evidence without proposal judgment
  - expected second Layer 2 result: direct output should improve at least part
    of the bounded nonlinear activation suite
- dependency order:
  - the Layer 2 proposal depends on merged Layer 1 evidence from
    `l1_prop_l1_terminal_sigmoid_block_v1_nangate45_r3` / PR `#63`
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
- first create the smallest useful nonlinear activation block:
  - terminal `int8` `Sigmoid`, preferably via the existing `pwl` activation
    path in `src/rtlgen`
- only after accepted Layer 1 physical results:
  - expose the block in fixed `fp16_nm1`
  - define a tiny terminal activation suite
  - run measurement-first and dependency-gated paired-comparison stages

## Direction Gate
- status: approved
- approved_by: user
- approved_utc: 2026-03-19T11:20:00Z
- note: Approved to proceed only if the nonlinear family is reframed as
  Layer-1-first, with Layer 2 evaluation blocked on accepted physical results.
