# Implementation Summary

## Proposal
- `proposal_id`: `prop_l1_terminal_hardswish_retryresume_v1`
- `title`: `Terminal int8 hard-swish retry/resume proof block`

## Scope
- seeded a unique retry/resume wrapper config and sweep path
- kept the implementation bounded to the accepted hard-swish `pwl` block shape
- no RTL or mapper change is intended

## Files Changed
- `docs/backlog/items/item_l1_terminal_hardswish_retryresume_v1.md`
- `docs/proposals/prop_l1_terminal_hardswish_retryresume_v1/*`
- `runs/designs/activations/terminal_hardswish_int8_pwl_retryresume_wrapper/config_terminal_hardswish_int8_pwl_retryresume.json`
- `runs/designs/activations/sweeps/nangate45_terminal_hardswish_int8_pwl_retryresume_v1.json`

## Local Validation
- pending queue-time JSON sanity check

## Evaluation Request
- one remote `l1_sweep`
- cost class: `high`
- baseline: accepted `prop_l1_terminal_hardswish_block_v1`

## Risks
- the proof is workflow-focused, so the physical metrics may be redundant relative to the earlier hard-swish reference
