# Quality Gate

## Proposal
- `proposal_id`: `prop_l1_decoder_q12_pwl_softmax_datapath_v1`
- `title`: `Decoder q12 PWL softmax datapath calibration`

## Why This Gate Is Required
- `softmax_rowwise` now supports a second approximation implementation.
- q8 shift-exp and reciprocal-normalization behavior must remain unchanged.
- q12 PWL reference outputs must match generated RTL for checked rows.

## Reference
- baseline_ref: `tests/test_softmax_rowwise.sh`
- reference_ref: `scripts/softmax_rowwise_ref.py`

## Checks
- existing q8 exact and q8 reciprocal tests pass unchanged
- q12 PWL reference row `[0, -512, -1024, -2048]` emits `[3549, 480, 65, 1]`
- q12 PWL generated RTL simulation matches the Python reference rows

## Local Commands
- `cmake --build build --target rtlgen`
- `bash tests/test_softmax_rowwise.sh`
- `python3 scripts/validate_runs.py --skip_eval_queue`

## Result
- status: passed_local
- note: Local build, q8/q12 softmax regression, q12 RTL compile, and runs validation passed before PR submission.
