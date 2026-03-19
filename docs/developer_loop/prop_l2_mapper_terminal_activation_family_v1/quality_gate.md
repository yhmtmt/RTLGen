# Quality Gate

## Proposal
- `proposal_id`: `prop_l2_mapper_terminal_activation_family_v1`
- `title`: `Terminal activation-family direct output`

## Why This Gate Is Required
- the next bounded family should include nonlinear terminal activations beyond
  `Relu`
- those ops are more numerically sensitive than the accepted standalone `Relu`
  vec-op path
- remote PPA evaluation should not proceed until:
  - a real Layer 1 sigmoid block exists with accepted physical results
  - local output-quality checks are defined

## Reference
- baseline_ref: pending bounded nonlinear activation measurement suite
- reference_ref: pending software or accepted schedule reference

## Checks
- pending bounded family selection
- pending local output-quality comparison criteria

## Local Commands
- pending

## Result
- status: pending
- note: blocked on `prop_l1_terminal_sigmoid_block_v1`
