# Softmax rowwise int8 r8 acc24 retryproof block

- item_id: `item_l1_softmax_rowwise_int8_r8_acc24_retryproof_v1`
- layer: `layer1`
- kind: `circuit`
- status: `promoted_to_proposal`
- priority: `medium`
- owner: `developer_agent`
- created_utc: `2026-04-01T12:16:17Z`
- updated_utc: `2026-04-01T12:16:17Z`
- proposal_id: `prop_l1_softmax_rowwise_int8_r8_acc24_retryproof_v1`
- proposal_path: `docs/proposals/prop_l1_softmax_rowwise_int8_r8_acc24_retryproof_v1`
- triggered_by_proposal:
- triggering_evidence:

## Problem
- evaluator-side submission interruption can leave a finished expensive run without an open PR, and later pulls used to erase the original canonical review diff

## Candidate Idea
- queue one fresh bounded softmax rowwise acc24 block under a unique canonical design path and use it as the proof item for frozen-evidence submission retry

## Why It Might Matter
- validates that completion-time frozen evidence survives submission retry after auth or network loss
- keeps the proof cheap by reusing the existing small softmax physical sweep

## Required Work
- l1 change? `config and docs only`
- l2 change? `no`
- mapper change? `no`
- quality gate required? `yes`

## Evaluation Sketch
- local JSON/config sanity check
- one remote Nangate45 L1 sweep
- intentional submission interruption
- submission retry without rerunning evaluation

## Inputs / Sources
- `runs/designs/activations/softmax_rowwise_int8_r8_acc24_wrapper/config_softmax_rowwise_int8_r8_acc24.json`
- `runs/designs/activations/sweeps/nangate45_softmax_rowwise_v1.json`

## Open Questions
- whether the frozen-evidence manifest remains sufficient if both branch push and PR creation fail

## Promotion Rule
- promote when the retryproof proposal is seeded and the first bounded remote sweep is queued
