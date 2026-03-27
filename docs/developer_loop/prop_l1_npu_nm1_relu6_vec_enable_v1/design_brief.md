# Design Brief

## Proposal
- `proposal_id`: `prop_l1_npu_nm1_relu6_vec_enable_v1`
- `title`: `NPU nm1 ReLU6 vec enable`
- `abstraction_layer`: `architecture_block`

## Objective
- integrate bounded `int8` ReLU6 support into the fixed `nm1` vec path
- produce an accepted reduced integrated physical source before any Layer 2
  ReLU6 campaign is queued

## Constraints
- keep `nm1` fixed
- keep the first pass bounded to one integrated ReLU6-enabled path
- prefer hierarchy-preserving evaluation and avoid early full-top flattening
- use the accepted standalone `int8` ReLU6 block as the lower-layer source

## Initial Plan
- add ReLU6 vec op support to the integrated `nm1` generator/perf path
- stage an early legality checkpoint if needed
- stage a reduced physical proxy before another full-top attempt
