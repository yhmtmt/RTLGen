# Quality Gate

## Proposal
- `proposal_id`: `prop_l1_terminal_hardsigmoid_retryresume_v1`
- `title`: `Terminal int8 hard-sigmoid retry/resume proof block`

## Why This Gate Is Required
- the proof depends on a clean proposal-backed review payload and recoverable completion state after submission interruption

## Reference
- baseline_ref: `docs/proposals/prop_l1_terminal_hardsigmoid_block_v1/promotion_result.json`
- reference_ref: `runs/designs/activations/terminal_hardsigmoid_int8_pwl_wrapper/config_terminal_hardsigmoid_int8_pwl.json`

## Checks
- metric: `review payload remains proposal-backed`
  - threshold: `required`
- metric: `dashboard Resume can recover submission after gh re-auth`
  - threshold: `required`

## Local Commands
- command: `python3 -m json.tool runs/designs/activations/terminal_hardsigmoid_int8_pwl_retryresume_wrapper/config_terminal_hardsigmoid_int8_pwl_retryresume.json`

## Result
- status: pending
- note: `awaiting first remote run`
