# Design Brief

## Proposal
- `proposal_id`: `prop_cross_non_mlp_terminal_suite_v1`
- `title`: `Terminal-sensitive softmax suite`

## Problem
- the corrected-contract overlap probe proved the fused terminal-output win on a
  focused `nm1` proof, but only on the tiny logistic-regression benchmark
- the current mapper-supported ONNX subset in this repo is still centered on
  imported-style linear chains with terminal `Softmax`, so a broader non-MLP
  proof would currently conflate model-support work with terminal-output
  evaluation
- we still do not know whether that win survives on a slightly broader but
  still bounded terminal-sensitive softmax-tail slice

## Hypothesis
- the fused terminal-output path should continue to improve a corrected-contract
  non-fused `nm1` reference on a small, intentionally chosen terminal-sensitive
  softmax-tail suite
- that question should be answered with measurement-first staging, not by
  jumping straight to broad architecture ranking

## Evaluation Scope
- direct comparison set:
  - corrected-contract non-fused `nm1` reference metrics on a small selected
    terminal-sensitive softmax-tail suite
  - paired fused vs non-fused `nm1` comparison on the same suite
- evaluation modes:
  - first-stage item: `measurement_only`
  - second-stage item: `paired_comparison`
  - expected first-stage result: record the reference points cleanly without
    proposal judgment
  - expected second-stage result: fused should improve at least part of the
    suite
- excluded first-stage comparisons:
  - `nm1` vs `nm2`
  - broad ranking across many architectures or workloads
- follow-on broad sweep:
  - only if the per-model fused comparison is positive or mixed enough to
    justify reintegration

## Knowledge Inputs
- `docs/proposals/prop_cross_terminal_output_overlap_probe_v1/analysis_report.md`
- merged evidence from PRs `#47` and `#48`
- discussion on 2026-03-18 about enabling metric-only evaluation items

## Candidate Direction
- choose a small terminal-sensitive model slice already available in the repo
  if possible; otherwise use only the minimum local ONNX-lite generated
  softmax-tail slice needed for a bounded first-stage proof
- measure corrected-contract non-fused points first
- compare fused vs non-fused only after those reference points exist

## Direction Gate
- status: approved
- approved_by: user
- approved_utc: 2026-03-18T11:05:00Z
- note: Approved to proceed with a staged terminal-sensitive follow-on using
  the new measurement-only evaluation mode.
