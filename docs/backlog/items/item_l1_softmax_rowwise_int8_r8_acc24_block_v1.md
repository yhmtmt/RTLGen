# Softmax rowwise int8 r8 acc24 block

- item_id: `item_l1_softmax_rowwise_int8_r8_acc24_block_v1`
- layer: `layer1`
- kind: `circuit`
- status: `promoted_to_proposal`
- priority: `medium`
- owner: `developer_agent`
- created_utc: `2026-03-30T10:48:20Z`
- updated_utc: `2026-03-30T10:48:20Z`
- proposal_id: `prop_l1_softmax_rowwise_int8_r8_acc24_block_v1`
- proposal_path: `docs/proposals/prop_l1_softmax_rowwise_int8_r8_acc24_block_v1`
- triggered_by_proposal:
- triggering_evidence:

## Problem
- the new worker/immediate-completion split needs a fresh small L1 proof item that produces a real canonical `runs/...` diff

## Candidate Idea
- evaluate one standalone rowwise int8 softmax r8 acc24 block under a new canonical proposal and unique design path

## Why It Might Matter
- validates the new service split on a small L1 path
- adds one more bounded circuit_block physical reference

## Required Work
- l1 change? `config and docs only`
- l2 change? `no`
- mapper change? `no`
- quality gate required? `yes`

## Evaluation Sketch
- local JSON/config sanity check
- one remote Nangate45 L1 sweep

## Inputs / Sources
- `runs/designs/activations/softmax_rowwise_int8_r8_acc20_wrapper/config_softmax_rowwise_int8_r8_acc20.json`
- `runs/designs/activations/sweeps/nangate45_softmax_rowwise_v1.json`

## Open Questions
- whether acc24 materially changes physical metrics versus acc20

## Promotion Rule
- promote when the corresponding proposal is seeded and the first bounded remote sweep is queued
