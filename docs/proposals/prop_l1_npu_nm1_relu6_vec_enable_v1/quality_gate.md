# Quality Gate

## Proposal
- `proposal_id`: `prop_l1_npu_nm1_relu6_vec_enable_v1`
- `title`: `NPU nm1 ReLU6 vec enable`

## Checks
- local vec-op legality and descriptor decode checks
- local contract checks for the bounded ReLU6 vec op
- integrated `nm1` RTL generation smoke
- accepted reduced-proxy physical metrics from the first successful remote sweep

## Result
- status: pending
- note: Proposal seeded only. No integrated `nm1` ReLU6 physical evidence exists yet.
