# Quality Gate

## Proposal
- `proposal_id`: `prop_l1_terminal_sigmoid_block_v1`
- `title`: `Terminal int8 sigmoid block`

## Why This Gate Is Required
- no separate model-quality gate is required at the circuit-only stage
- correctness gates move to local RTL or wrapper checks here, and to later
  Layer 2 output-quality comparison when the block is used in mapped models
- the first pass is intentionally limited to an `int8` block so correctness and
  physical characterization can be established before any `fp16` follow-on

## Reference
- baseline_ref: pending
- reference_ref: pending

## Checks
- local bounded-curve checks against the chosen `pwl` sigmoid points
- local RTL smoke check for wrapper integration and signed int8 saturation

## Local Commands
- pending: generate the block from `src/rtlgen` `pwl` activation config
- pending: run local RTL smoke test on representative signed int8 inputs

## Result
- status: pending
- note:
