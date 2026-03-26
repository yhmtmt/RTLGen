# Design Brief

## Proposal
- `proposal_id`: `prop_l1_npu_nm1_hardtanh_vec_enable_v1`
- `title`: `NPU nm1 hard-tanh vec enable`
- `abstraction_layer`: `architecture_block`

## Objective
- integrate bounded `int8` hard-tanh support into the fixed `nm1` vec path
- produce an accepted reduced integrated physical source before any Layer 2
  hard-tanh campaign is queued

## Constraints
- keep `nm1` fixed
- keep the first pass bounded to one integrated hard-tanh-enabled path
- prefer hierarchy-preserving evaluation and avoid early full-top flattening
- use the accepted standalone `int8` hard-tanh block as the lower-layer source

## Initial Plan
- add hard-tanh vec op support to the integrated `nm1` generator/perf path
- stage an early legality checkpoint if needed
- stage a reduced physical proxy before another full-top attempt
