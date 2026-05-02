# Quality Gate

## Proposal
- `proposal_id`: `prop_l1_decoder_q12_pwl_recip_norm_datapath_v1`
- `title`: `Decoder q12 PWL reciprocal-normalization datapath`

## Why This Gate Is Required
- q12 PWL reciprocal normalization is a new approximation point relative to the exact q12 PWL survivor.
- The first gate checks RTL/reference consistency only; decoder quality needs a later Layer-2 evaluation if PPA is promising.

## Reference
- baseline_ref: `tests/test_softmax_rowwise.sh`
- reference_ref: `scripts/softmax_rowwise_ref.py`

## Checks
- existing q8 exact and q8 reciprocal tests pass unchanged
- q12 PWL exact tests pass unchanged
- q12 PWL q12 reciprocal bucket8 reference row `[0, -512, -1024, -2048]` emits `[3447, 466, 63, 1]`
- generated q12 PWL reciprocal RTL emits no `/ sum_weights` divider

## Local Commands
- `cmake --build build --target rtlgen`
- `bash tests/test_softmax_rowwise.sh`
- `python3 scripts/validate_runs.py --skip_eval_queue`

## Result
- status: passed_local
- note: Local build, q8/q12 softmax regression, q12 reciprocal RTL compile, and runs validation passed before PR submission.
