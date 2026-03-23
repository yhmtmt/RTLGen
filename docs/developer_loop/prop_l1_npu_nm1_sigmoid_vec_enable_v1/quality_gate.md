# Quality Gate

## Proposal
- `proposal_id`: `prop_l1_npu_nm1_sigmoid_vec_enable_v1`
- `title`: `NPU nm1 sigmoid vec enable`

## Checks
- local vec-op legality and descriptor decode checks
- local contract checks for the bounded sigmoid vec op
- integrated `nm1` RTL generation smoke
- accepted integrated canonicalize checkpoint from `r14`
- accepted reduced-proxy physical metrics from `r18`

## Result
- status: passed
- note: The integrated sigmoid-enabled `nm1` architecture-block now has both an accepted legality checkpoint (`r14`) and accepted reduced-proxy physical metrics (`r18`).
