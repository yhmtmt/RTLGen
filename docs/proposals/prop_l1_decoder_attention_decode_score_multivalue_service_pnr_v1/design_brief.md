# Design Brief

## Proposal
- `proposal_id`: `prop_l1_decoder_attention_decode_score_multivalue_service_pnr_v1`
- `title`: `First physical prep for multivalue composed service`

## Problem
The integrated shared-score multivalue service now has merged functional probe
evidence, but there is no dependency-gated Layer 1 path that can generate the
actual composed RTL, prove macro evidence for both score banks and value
storage, and reject undersized c1/c2 Nangate45 sweeps before dispatch.

## Hypothesis
A first physical patch anchored on `c1` at
`p128/b4/q4/rl2/round_robin`, with an exact-capacity `4 banks x 16 lanes` of
`fakeram45_64x32` value-memory macros and strict perimeter/macro guards, is
enough to make the composed service physically dispatchable without dragging
`c4/c8/c16/c32` into the same change. `c2` remains a conditional follow-on once
the same physical contract is proven cleanly on the current monolithic wrapper,
and its requested item now depends explicitly on
`l1_decoder_attention_decode_score_multivalue_service_c1_p128_b4_q4_rl2_rr_pnr_v1`.

## Scope
- include:
  - L1 generator wiring for `gen_attention_decode_score_multivalue_service.py`
  - strict pre-PPA guard and post-sweep checker
  - checked-in c1/c2 configs and Nangate45 sweeps
  - exact `4 bank x 16 lane x 64 row fakeram45_64x32` physical value-memory
    contract for `max_blocks=16`, while keeping behavioral mode for functional
    simulation and macro/backend equivalence testing
  - proposal items that depend on
    `l2_decoder_attention_decode_score_multivalue_integrated_service_llama7b_v1_r1`
- exclude:
  - c4/c8/activity work in this patch
  - c16/c32 dispatch in this patch
  - OpenROAD execution in this patch

## Follow-On Gates
- `c2` remains conditional on the corrected c1 macro-backed implementation and
  evidence remaining clean after merge, with an explicit dependency on
  `l1_decoder_attention_decode_score_multivalue_service_c1_p128_b4_q4_rl2_rr_pnr_v1`.
- `c8` remains a later-gated follow-up after c1/c2 runtime and feasibility are
  materialized.
- `c16` and `c32` remain later-gated follow-ups after `c8` proves both runtime
  practicality and physical feasibility.
