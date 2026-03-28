# Terminal int8 sigmoid block

- item_id: `item_l1_terminal_sigmoid_block_v1`
- layer: `layer1`
- kind: `circuit`
- status: `merged`
- priority: `high`
- owner: `developer_agent`
- created_utc: `2026-03-19T11:35:00Z`
- updated_utc: `2026-03-19T13:00:39Z`
- proposal_id: `prop_l1_terminal_sigmoid_block_v1`
- proposal_path: `docs/proposals/prop_l1_terminal_sigmoid_block_v1`
- triggered_by_proposal: `prop_l2_mapper_terminal_activation_family_v1`
- triggering_evidence:
  - `docs/proposals/prop_l2_mapper_terminal_activation_family_v1/proposal.json`
  - `docs/proposals/prop_l2_mapper_terminal_activation_family_v1/design_brief.md`
  - `docs/proposals/prop_l2_mapper_terminal_vecop_direct_output_v1/analysis_report.md`
  - `docs/proposals/prop_l2_mapper_terminal_vecop_direct_output_v1/promotion_decision.json`

## Problem
- nonlinear terminal activations cannot be evaluated credibly in Layer 2 perf
  campaigns without a real Layer 1 block and measured physical parameters
- the accepted direct-output mechanism is now beyond `Relu`, but there is no
  accepted physical block for a bounded nonlinear activation family

## Candidate Idea
- implement the smallest useful nonlinear terminal activation block:
  `int8 sigmoid`
- prefer a bounded piecewise-linear (`pwl`) implementation on the existing
  `src/rtlgen` integer activation path
- keep the first pass tightly bounded so later Layer 2 work can consume real
  physical timing, power, and area

## Why It Might Matter
- gives future Layer 2 perf simulation a real physical source for nonlinear
  activation timing and power
- keeps the nonlinear-family expansion technically valid
- may become the anchor block for later bounded `sigmoid` terminal-output
  evaluation on fixed `nm1`

## Required Work
- l1 change: yes
- l2 change: not in this proposal
- mapper change: no in this proposal
- quality gate required: no separate model-quality gate for the circuit itself;
  quality moves to the later Layer 2 use of the block

## Evaluation Sketch
- local:
  - define the bounded sigmoid block and wrapper contract
  - add local RTL/smoke checks
- remote:
  - first-stage Layer 1 physical sweep on one bounded sigmoid block family
  - accept `metrics.csv` evidence and physical implementation outputs
- follow-on:
  - unblock `prop_l2_mapper_terminal_activation_family_v1`

## Inputs / Sources
- `docs/proposals/prop_l2_mapper_terminal_activation_family_v1/proposal.json`
- `docs/proposals/prop_l2_mapper_terminal_activation_family_v1/design_brief.md`
- discussion on 2026-03-19 about nonlinear activations requiring Layer 1-first
  physical evaluation

## Open Questions
- which bounded `int8` sigmoid implementation style is the smallest viable
  first pass
- which first-pass `pwl` points are good enough to support physical
  characterization without widening the scope into a quality-study project
- whether one wrapper is enough or whether a tiny family is needed immediately
- what acceptance metric threshold is sufficient before Layer 2 consumption

## Promotion Rule
- promote when the proposal names one bounded sigmoid block path, keeps the
  remote evaluation focused on physical implementation evidence, and clearly
  unblocks the Layer 2 activation-family proposal

## Outcome
- merged evidence PR: `#63`
- accepted best point:
  - `param_hash`: `d3ba16d6`
  - `critical_path_ns`: `0.1904`
  - `die_area`: `25600.0`
  - `total_power_mw`: `5.84e-05`
- follow-on: unblock `prop_l2_mapper_terminal_activation_family_v1`
