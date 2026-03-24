# Implementation Summary

## Proposal
- `proposal_id`: `prop_l1_terminal_tanh_block_v1`
- `title`: `Terminal int8 tanh block`

## Scope
- proposal seeded only
- no RTL, sweep, or eval artifacts exist yet
- intended first pass mirrors the accepted sigmoid path:
  - bounded `int8` `pwl` block
  - local smoke validation
  - one remote physical sweep

## Planned Files
- expected implementation direction:
  - `src/rtlgen/rtl_operations.cpp` if a small `pwl` extension is needed
  - `examples/config_activation_tanh_int8.json`
  - `tests/activation_tanh_int_tb.v`
  - `tests/test_activation_tanh_int.sh`
  - `runs/designs/activations/terminal_tanh_int8_pwl_wrapper/*`
  - `runs/designs/activations/sweeps/nangate45_terminal_tanh_int8_pwl_v1.json`

## Local Validation Plan
- rebuild or reuse local `rtlgen`
- validate the new `int8` tanh `pwl` smoke test on representative signed inputs and saturation points
- confirm monotonicity and boundedness of the emitted RTL

## Evaluation Request
- next step:
  - implement the bounded tanh block and smoke checks
  - generate the first DB-backed Layer 1 sweep item for Nangate45
  - inspect `metrics.csv` rows and pick the accepted tanh seed
  - then decide whether an integrated `nm1` tanh-enable follow-on should be seeded immediately

## Risks
- the first bounded int8 tanh implementation path may be too costly or inaccurate
- later integrated use may still require interface adjustments
- later `fp16`-pipeline use may require a separate conversion or native-fp16 follow-on
