# Design Brief

## Proposal
- `proposal_id`: `prop_l1_npu_nm1_sigmoid_vec_enable_v1`
- `title`: `NPU nm1 sigmoid vec enable`
- `abstraction_layer`: `architecture_block`

## Problem
- this proposal sits at the generalized `architecture_block` layer: it is larger than a reusable sigmoid block, but still a reduced integrated proof target below workload-level architecture evaluation
- accepted standalone sigmoid physical evidence is not sufficient for Layer 2
  sigmoid evaluation because campaign physical provenance comes from the
  hardened `nm1` NPU block
- current `nm1` NPU configs enable vec ops `add/mul/relu` only

## Hypothesis
- bounded int8 sigmoid can be integrated into the fixed `nm1` vec path and
  physically characterized without reopening broader architecture questions

## Evaluation Scope
- direct comparison set:
  - one sigmoid-enabled `nm1` design/config variant
  - one focused Layer 1 physical sweep
- excluded:
  - Layer 2 campaigns
  - broad vec-op family support
  - `nm1` vs `nm2`

## Candidate Direction
- add bounded sigmoid support to the NPU vec-op path and descriptor contract
- generate a sigmoid-enabled `npu_fp16_cpp_nm1_*` variant
- keep the existing full-top `npu_fp16_cpp_nm1_sigmoidcmp` target only as an
  integrated legality/prefilter checkpoint
- characterize a reduced integrated proxy physically on Nangate45 first:
  `npu_fp16_cpp_nm1_sigmoidproxy`
- keep early-stage `architecture_block` evaluation hierarchy-preserving:
  no `mode_compare`, `flat_nomacro`, or `SYNTH_HIERARCHICAL=0` sweeps on
  `npu_top` until a smaller bounded hotspot justifies a later selective
  flattening pass

## Direction Gate
- status: approved
- approved_by: user
- approved_utc: 2026-03-19T13:10:00Z
- note: This is required before queuing the Layer 2 activation-family
  measurement item.
