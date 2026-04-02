# Design Brief

## Proposal
- `proposal_id`: `prop_l1_terminal_hardsigmoid_retryresume_v1`
- `title`: `Terminal int8 hard-sigmoid retry/resume proof block`

## Problem
- evaluator-side submission interruption can still leave a finished bounded Layer 1 run stranded in `ARTIFACT_SYNC`

## Hypothesis
- a fresh proposal-backed hard-sigmoid block under a unique canonical path is sufficient to prove that dashboard Resume can recover the submission without rerunning evaluation

## Evaluation Scope
- direct comparison set:
  - one standalone `int8` hard-sigmoid `pwl` block only
- evaluation modes:
  - one `measurement_only` Layer 1 physical sweep
- dependency order:
  - none
- excluded first-stage comparisons:
  - integrated `nm1` work
  - mapper or Layer 2 ranking
- follow-on broad sweep:
  - none unless resume still fails after submission interruption

## Knowledge Inputs
- accepted hard-sigmoid block proposal
- dashboard resume discussion
- prior retryproof submission recovery work

## Candidate Direction
- reuse the accepted hard-sigmoid wrapper shape under a unique canonical wrapper path
- intentionally interrupt submission by logging out `gh` on the evaluator

## Direction Gate
- status: approved
- approved_by: `developer_agent`
- approved_utc: `2026-04-02T03:00:00Z`
- note: `bounded resume proof item`
