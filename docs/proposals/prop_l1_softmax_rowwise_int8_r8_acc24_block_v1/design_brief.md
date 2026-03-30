# Design Brief

- proposal_id: `prop_l1_softmax_rowwise_int8_r8_acc24_block_v1`
- title: `Softmax rowwise int8 r8 acc24 block`

## Scope
- bounded standalone int8 softmax rowwise block only
- row width fixed at 8
- accumulation width fixed at 24

## Goal
- obtain one accepted Nangate45 physical measurement for a unique canonical-path circuit_block item
- use it as a live proof that worker-local completion plus maintenance-loop reconciliation still behave correctly after the service split
