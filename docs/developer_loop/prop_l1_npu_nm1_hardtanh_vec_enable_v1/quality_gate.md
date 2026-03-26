# Quality Gate

## Proposal
- `proposal_id`: `prop_l1_npu_nm1_hardtanh_vec_enable_v1`
- `title`: `NPU nm1 hard-tanh vec enable`

## Checks
- local vec-op legality and descriptor decode checks
- local contract checks for the bounded hard-tanh vec op
- integrated `nm1` RTL generation smoke
- accepted reduced-proxy physical metrics from the first successful remote sweep

## Result
- status: pending
- note: Proposal seeded only. No integrated `nm1` hard-tanh physical evidence exists yet.
