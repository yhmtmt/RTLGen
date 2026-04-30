# Design Brief

## Proposal
- `proposal_id`: `prop_l2_decoder_q8_norm_distribution_robustness_v1`
- `title`: `Decoder q8/bf16 normalization distribution robustness`

## Problem
The current q8 normalization frontier ranks bf16 reciprocal normalization first
by measured row-8 Nangate45 critical path, with q8 reciprocal q10 as the best
q8 reciprocal row. That evidence is still tied to a specific prompt-stress
setup. Normalization quality is distribution-sensitive, so the next job should
check a broader prompt/logit distribution before treating that ranking as an
architecture direction.

## Evaluation Scope
- run `decoder_q8_normalization_frontier_v1` on
  `manifest_distribution_v1.json`
- include bf16 reciprocal, q8 exact, and q8 reciprocal q10/q12/q14/q16 rows
- rank exact-safe measured rows by critical path, then area, then power
- depend on the merged q8 normalization frontier and distribution robustness
  artifacts

## Exclusions
- no new RTL/OpenROAD measurement
- no mapper changes
- no final model-family robustness claim

## Direction Gate
- status: approved
- approved_by: developer_agent
- approved_utc: 2026-04-30T21:40:30Z
- note: queue after the generator hook is merged and dispatch to the remote evaluator.
