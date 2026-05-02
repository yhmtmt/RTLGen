# Implementation Summary

## Proposal
- `proposal_id`: `prop_l1_decoder_q12_pwl_softmax_datapath_v1`
- title: `Decoder q12 PWL softmax datapath calibration`

## Scope
- Added `impl=pwl_exp` support to RTLGen `softmax_rowwise`.
- Added q12 fixed-point input/weight controls for the row-wise softmax emitter.
- Added a matching Python reference path and RTL simulation coverage.
- Added the q12 PWL row-8 config and Nangate45 high-util sweep metadata.
- Did not add full dynamic symmetric quantizer hardware.

## Files Changed
- `src/rtlgen/config.hpp`
- `src/rtlgen/config.cpp`
- `src/rtlgen/rtl_operations.cpp`
- `scripts/softmax_rowwise_ref.py`
- `tests/test_softmax_rowwise.sh`
- `tests/softmax_rowwise_q12_pwl_tb.v`
- `runs/designs/activations/softmax_rowwise_q12_pwl_r8_acc28_wrapper/config_softmax_rowwise_q12_pwl_r8_acc28.json`
- `runs/campaigns/activations/softmax_rowwise_q12_pwl/sweeps/nangate45_highutil.json`

## Local Validation
- `cmake --build build --target rtlgen`
- `bash tests/test_softmax_rowwise.sh`
- generated and compiled `softmax_rowwise_q12_pwl_r8_acc28.v` with `iverilog -g2012`
- `python3 scripts/validate_runs.py --skip_eval_queue`
- `git diff --check`

## Evaluation Request
- requested item: `l1_decoder_q12_pwl_softmax_datapath_v1`
- task type: `l1_sweep`
- mode: `measurement_only`
- compare against q8 reciprocal and bf16 normalization datapath measurements using separate timing, power, and area axes.

## Risks
- The exact divider may dominate the first measurement.
- This is a fixed-point datapath proxy and excludes dynamic quantizer cost.
- The current quality evidence is benchmark-distribution dependent.
