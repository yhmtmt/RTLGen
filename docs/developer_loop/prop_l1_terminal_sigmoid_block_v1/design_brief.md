# Design Brief

## Proposal
- `proposal_id`: `prop_l1_terminal_sigmoid_block_v1`
- `title`: `Terminal sigmoid block`

## Problem
- nonlinear terminal activation evaluation in Layer 2 currently lacks a real
  physical block
- without physical timing, power, and area, perf-sim-based Layer 2 evaluation
  would be technically weak

## Hypothesis
- one bounded sigmoid block is enough to establish the Layer 1 physical anchor
  for later fixed-`nm1` terminal nonlinear activation evaluation

## Evaluation Scope
- direct comparison set:
  - one bounded sigmoid block candidate
  - one physical sweep on the target platform
- evaluation modes:
  - first-stage item: `measurement_only`
  - expected result: accepted physical metrics and wrapper evidence
- dependency order:
  - this proposal unblocks `prop_l2_mapper_terminal_activation_family_v1`
- excluded first-stage comparisons:
  - broader nonlinear block families
  - any Layer 2 mapper or architecture comparisons
- follow-on broad sweep:
  - only if the first sigmoid block is accepted but insufficient

## Knowledge Inputs
- `docs/developer_loop/prop_l2_mapper_terminal_activation_family_v1/proposal.json`
- `docs/developer_loop/prop_l2_mapper_terminal_activation_family_v1/design_brief.md`
- discussion on 2026-03-19 about Layer 1-first nonlinear activation evaluation

## Candidate Direction
- choose the smallest bounded sigmoid block implementation path
- target physical implementation evidence, not broad circuit-family ranking

## Direction Gate
- status: approved
- approved_by: user
- approved_utc: 2026-03-19T11:35:00Z
- note: Approved as the prerequisite Layer 1 path before any Layer 2 nonlinear
  activation-family perf evaluation.
