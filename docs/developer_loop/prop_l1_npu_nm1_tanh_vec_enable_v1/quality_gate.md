# Quality Gate

## Proposal
- `proposal_id`: `prop_l1_npu_nm1_tanh_vec_enable_v1`
- `title`: `NPU nm1 tanh vec enable`

## Checks
- local vec-op legality and descriptor decode checks
- local contract checks for the bounded tanh vec op
- integrated `nm1` RTL generation smoke
- accepted reduced-proxy physical metrics from `r2`

## Result
- status: passed
- note: The integrated tanh-enabled `nm1` architecture-block now has accepted reduced-proxy physical metrics from `r2`.
