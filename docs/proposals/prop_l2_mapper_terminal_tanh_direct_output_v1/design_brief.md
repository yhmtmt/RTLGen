# Design Brief

## Proposal
- `proposal_id`: `prop_l2_mapper_terminal_tanh_direct_output_v1`
- `title`: `Terminal tanh direct output`

## Problem
- bounded terminal `tanh` now has accepted lower-layer grounding:
  - standalone `int8` tanh block
  - integrated `nm1_tanhproxy` architecture-block source
- but there is no Layer 2 direct-output evidence yet for `tanh`

## Hypothesis
- terminal `Tanh` vec-op tails on fixed `nm1` should benefit from writing directly to `Y_DRAM` instead of staging through activation SRAM, similar to the accepted sigmoid result

## Evaluation Scope
- direct comparison set:
  - one bounded tanh-first `measurement_only` baseline
  - one dependency-gated paired direct-output candidate on the same suite
- evaluation modes:
  - `measurement_only` first
  - `paired_comparison` second
- dependency order:
  - `l2_prop_l2_mapper_terminal_tanh_direct_output_v1_nm1_fused_r1` depends on merged/materialized baseline `l2_prop_l2_mapper_terminal_tanh_direct_output_v1_nm1_measurement_r1`
- excluded first-stage comparisons:
  - broader nonlinear-family ranking beyond tanh
  - full `npu_top` claims beyond the accepted reduced tanh proxy grounding

## Knowledge Inputs
- accepted lower-layer tanh evidence from `prop_l1_terminal_tanh_block_v1` and `prop_l1_npu_nm1_tanh_vec_enable_v1`
- accepted sigmoid direct-output evidence from `prop_l2_mapper_terminal_activation_family_v1`

## Candidate Direction
- add bounded terminal `Tanh` mapper lowering
- generate a small tanh-first ONNX suite
- run the same staged baseline-then-paired workflow used for sigmoid

## Direction Gate
- status: approved
- approved_by: developer_agent
- approved_utc: 2026-03-24T13:10:00Z
- note: accepted lower-layer tanh grounding exists, so the next bounded question is the Layer 2 direct-output comparison itself
