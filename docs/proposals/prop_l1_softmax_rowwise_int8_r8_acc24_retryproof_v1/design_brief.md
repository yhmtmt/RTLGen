# Design Brief

## Proposal
- `proposal_id`: `prop_l1_softmax_rowwise_int8_r8_acc24_retryproof_v1`
- `title`: `Softmax rowwise int8 r8 acc24 retryproof block`

## Problem
- evaluator-side submission failure can leave a completed bounded run without a PR, and later retries used to rebuild from mutable `runs/...` state instead of the original completion-time evidence

## Hypothesis
- a fresh standalone softmax rowwise acc24 block under a unique canonical design path is enough to prove that frozen completion-time evidence preserves retryable submission state after auth or network interruption

## Evaluation Scope
- direct comparison set:
  - one standalone rowwise int8 softmax r8 acc24 block under a unique canonical design path
- evaluation modes:
  - one `measurement_only` Layer 1 sweep on Nangate45
- dependency order:
  - none
- excluded first-stage comparisons:
  - integrated architecture evaluation
  - mapper or scheduler comparisons
  - broader softmax family parameter sweeps
- follow-on broad sweep:
  - none unless submission retry still loses the original reviewable diff

## Knowledge Inputs
- prior standalone rowwise softmax acc24 block evaluation
- discussion: 2026-04-01 frozen submission evidence recovery

## Candidate Direction
- reuse the small existing softmax rowwise physical sweep while moving the config to a fresh unique design path so the item carries a new canonical `runs/...` diff

## Direction Gate
- status: pending
- approved_by:
- approved_utc:
- note:
