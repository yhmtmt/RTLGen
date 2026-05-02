# Implementation Summary

## Proposal
- `proposal_id`: `prop_l1_decoder_q12_pwl_recip_norm_datapath_v1`
- title: `Decoder q12 PWL reciprocal-normalization datapath`

## Scope
- Added q10/q12/q14/q16 q12 PWL reciprocal-normalization configs.
- Added the Nangate45 high-util sweep metadata.
- Extended the q12 PWL softmax regression to cover reciprocal normalization.
- Did not add a Layer-2 quality check for reciprocal normalization yet.

## Files Changed
- `tests/softmax_rowwise_q12_pwl_tb.v`
- `tests/test_softmax_rowwise.sh`
- `runs/designs/activations/softmax_rowwise_q12_pwl_r8_acc28_recip_q*_bucket8_wrapper/`
- `runs/campaigns/activations/softmax_rowwise_q12_pwl_recip_norm/sweeps/nangate45_highutil.json`
- `docs/proposals/prop_l1_decoder_q12_pwl_recip_norm_datapath_v1/`

## Local Validation
- `cmake --build build --target rtlgen`
- `bash tests/test_softmax_rowwise.sh`
- generated and compiled all four q12 PWL reciprocal configs with `iverilog -g2012`
- `python3 scripts/validate_runs.py --skip_eval_queue`
- `git diff --check`

## Evaluation Request
- requested item: `l1_decoder_q12_pwl_recip_norm_datapath_v1`
- task type: `l1_sweep`
- mode: `measurement_only`
- compare against q12 PWL exact normalization, q8 reciprocal normalization, and bf16 reciprocal normalization on separate PPA axes.

## Risks
- Reciprocal normalization changes numerical behavior relative to the exact q12 PWL survivor.
- Bucket shift 8 is hardware-feasible but still needs later quality validation.
- Single-row block PPA excludes full decoder memory/control cost.
