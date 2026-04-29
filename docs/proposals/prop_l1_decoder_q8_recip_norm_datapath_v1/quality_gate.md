# Quality Gate

## Proposal
- `proposal_id`: `prop_l1_decoder_q8_recip_norm_datapath_v1`
- `title`: `Decoder q8 reciprocal normalization datapath`

## Checks

- RTLGen must continue to emit the existing exact row-wise int8 softmax block.
- `normalization_mode=reciprocal_quantized` must emit no `/ sum_weights`
  divider in the generated Verilog.
- The q10 reciprocal reference and generated RTL must match the checked row
  examples in `tests/test_softmax_rowwise.sh`.
- The Layer-1 evaluation is measurement-only; it should not change decoder
  prompt-stress quality decisions.

## Local Commands

- `cmake --build build -j2`
- `bash tests/test_softmax_rowwise.sh`
- `python3 scripts/validate_runs.py --skip_eval_queue`

## Result
- status: passed_local
- note: Local build, softmax regression, dry-run sweep, and runs validation passed before PR submission.
