# Design Brief

## Proposal
- `proposal_id`: `prop_l1_terminal_tanh_block_v1`
- `title`: `Terminal int8 tanh block`

## Problem
- the accepted bounded activation-family work now covers terminal `Sigmoid`, but no lower-layer `tanh` block exists yet
- without physical timing, power, and area for `tanh`, any broader nonlinear activation evaluation would be technically weak again

## Hypothesis
- one bounded `int8` tanh block is enough to establish the next Layer 1 physical anchor for broadening terminal nonlinear activation evaluation beyond sigmoid
- this first pass should not attempt native `fp16` tanh; it should produce a small, measurable nonlinear block first

## Evaluation Scope
- direct comparison set:
  - one bounded `int8` tanh block candidate
  - one physical sweep on the target platform
- evaluation modes:
  - first-stage item: `measurement_only`
  - expected result: accepted physical metrics and wrapper evidence
- dependency order:
  - this proposal should unblock a later integrated `nm1` tanh-enable item, not Layer 2 directly
- excluded first-stage comparisons:
  - broader nonlinear block families
  - any integrated `nm1` or Layer 2 mapper/architecture comparisons
  - native `fp16` tanh implementation
- follow-on broad sweep:
  - only if the first tanh block is accepted but insufficient

## Knowledge Inputs
- `docs/developer_loop/prop_l2_mapper_terminal_activation_family_v1/analysis_report.md`
- `docs/developer_loop/prop_l1_terminal_sigmoid_block_v1/design_brief.md`
- discussion on 2026-03-24 about returning to lower-layer grounding before broadening beyond sigmoid

## Candidate Direction
- choose the smallest bounded `int8` tanh block implementation path
- prefer the existing `src/rtlgen` integer activation path with `function=pwl` and user-specified points for a first-pass tanh approximation
- treat any later integrated `nm1` enable or Layer 2 use as separate follow-ons once the first physical block is accepted
- target physical implementation evidence, not broad circuit-family ranking

## Direction Gate
- status: approved
- approved_by: user
- approved_utc: 2026-03-24T12:00:00Z
- note: Approved as the next lower-layer bounded nonlinear activation path after sigmoid.
