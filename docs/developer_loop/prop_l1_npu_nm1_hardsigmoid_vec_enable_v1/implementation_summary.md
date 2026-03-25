# Implementation Summary

## Proposal
- `proposal_id`: `prop_l1_npu_nm1_hardsigmoid_vec_enable_v1`
- `title`: `NPU nm1 hard-sigmoid vec enable`

## Scope
- proposal seeded only; integrated `nm1` hard-sigmoid support is not implemented yet
- intended shape mirrors the accepted sigmoid/tanh path:
  - local vec-op legality/generation support first
  - reduced integrated physical proxy second
  - Layer 2 later

## Planned Work
- add hard-sigmoid vec op support to the integrated `nm1` generator and perf path
- add local legality / smoke checks for the bounded op
- define a reduced integrated physical proxy suitable for first-pass `architecture_block` measurement
- queue the first Layer 1 reduced-proxy sweep only after the local path exists

## Current State
- accepted lower-layer source exists:
  - standalone hard-sigmoid block proposal `prop_l1_terminal_hardsigmoid_block_v1`
- no integrated `nm1` hard-sigmoid implementation or remote evaluation has been queued yet

## Next Step
- implement bounded integrated `nm1` hard-sigmoid vec support and seed the first reduced-proxy sweep request
