# Terminal int8 hard-sigmoid retry/resume proof block

- item_id: `item_l1_terminal_hardsigmoid_retryresume_v1`
- layer: `layer1`
- kind: `circuit`
- status: `promoted_to_proposal`
- priority: `medium`
- owner: `developer_agent`
- created_utc: `2026-04-02T03:00:00Z`
- updated_utc: `2026-04-02T03:00:00Z`
- proposal_id: `prop_l1_terminal_hardsigmoid_retryresume_v1`
- proposal_path: `docs/proposals/prop_l1_terminal_hardsigmoid_retryresume_v1`
- triggered_by_proposal:
- triggering_evidence:

## Problem
- evaluator-side submission interruption can still leave a finished bounded Layer 1 run stranded in `ARTIFACT_SYNC`

## Candidate Idea
- queue one fresh standalone hard-sigmoid block under a unique canonical design path and use it to prove dashboard `Resume` recovery

## Why It Might Matter
- validates the new dashboard resume flow on a normal proposal-backed Layer 1 item
- keeps the proof cheap by reusing the accepted hard-sigmoid wrapper shape

## Required Work
- l1 change? `config and docs only`
- l2 change? `no`
- mapper change? `no`
- quality gate required? `yes`

## Evaluation Sketch
- local JSON/config sanity check
- one remote Nangate45 L1 sweep
- intentional submission interruption via evaluator-side `gh` logout
- dashboard `Resume` after `gh` re-authentication

## Inputs / Sources
- `runs/designs/activations/terminal_hardsigmoid_int8_pwl_wrapper/config_terminal_hardsigmoid_int8_pwl.json`
- `runs/designs/activations/sweeps/nangate45_terminal_hardsigmoid_int8_pwl_v1.json`
- `docs/proposals/prop_l1_terminal_hardsigmoid_block_v1/proposal.json`

## Open Questions
- whether the resume path needs any extra operator hinting when the saved submission branch already exists

## Promotion Rule
- promote when the retry/resume proof proposal is seeded and the first bounded remote sweep is queued
