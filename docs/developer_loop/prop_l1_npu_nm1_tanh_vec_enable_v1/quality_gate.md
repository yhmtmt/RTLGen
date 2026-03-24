# Quality Gate

## Proposal
- `proposal_id`: `prop_l1_npu_nm1_tanh_vec_enable_v1`
- `title`: `NPU nm1 tanh vec enable`

## Why This Gate Is Required
- this is an integrated `architecture_block` prerequisite for later Layer 2
  tanh evaluation
- correctness must first be established through local legality / smoke checks
  before any costly physical sweep is queued

## Checks
- local integrated generator/perf smoke checks
- hierarchy-preserving synthesis or canonicalize checkpoint if needed

## Result
- status: pending
- note: proposal seeded; integrated tanh-enable implementation not started yet
