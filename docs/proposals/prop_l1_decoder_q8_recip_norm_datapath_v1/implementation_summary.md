# Implementation Summary

## Proposal
- `proposal_id`: `prop_l1_decoder_q8_recip_norm_datapath_v1`
- title: `Decoder q8 reciprocal normalization datapath`

## Scope
- Added `normalization_mode` and `reciprocal_bits` options to RTLGen
  `softmax_rowwise`.
- Preserved the existing exact divider mode as the default.
- Added `reciprocal_quantized` emission using a bucketed denominator-indexed
  reciprocal lookup and multiply/shift normalization path.
- Added q10/q12/q14/q16 row-wise int8 r8 acc24 configs for L1 measurement.

## Files Changed
- `src/rtlgen/config.hpp`
- `src/rtlgen/config.cpp`
- `src/rtlgen/rtl_operations.cpp`
- `scripts/softmax_rowwise_ref.py`
- `tests/test_softmax_rowwise.sh`
- `runs/designs/activations/softmax_rowwise_int8_r8_acc24_recip_q*_wrapper/`
- `runs/campaigns/activations/softmax_rowwise_int8_recip_norm/sweeps/nangate45_highutil.json`

## Local Validation
- `cmake --build build -j2`
- `bash tests/test_softmax_rowwise.sh`
- `python3 scripts/validate_runs.py --skip_eval_queue`
- `./build/test_onnx && ./build/test_boolexp && ./build/test_adder && ./build/test_multiplier`
- `python3 scripts/run_sweep.py ... --dry_run`

## Evaluation Request
- requested item: `l1_decoder_q8_recip_norm_datapath_v1`
- task type: `l1_sweep`
- mode: `measurement_only`
- compare q10/q12/q14/q16 integrated reciprocal-normalization blocks on Nangate45.

## Risks
- The reciprocal lookup table may dominate area for this row envelope.
- The bucketed denominator lookup changes numerical behavior relative to the
  earlier exact reciprocal software quality rows.
- This remains a row-wise block measurement, not full decoder-system PPA.
- bf16 reciprocal/multiply datapaths remain unmeasured.
