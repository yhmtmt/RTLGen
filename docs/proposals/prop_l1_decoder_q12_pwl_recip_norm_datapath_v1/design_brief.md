# Design Brief

## Proposal
- `proposal_id`: `prop_l1_decoder_q12_pwl_recip_norm_datapath_v1`
- `title`: `Decoder q12 PWL reciprocal-normalization datapath`
- `layer`: `layer1`
- `kind`: `circuit_block`

## Problem

The q12 PWL exact-normalization datapath produced accepted physical metrics, but
the result was dominated by a wide exact divider: roughly 58.7 ns, 480.9k um^2,
and 29.1 mW at the selected timing row. That makes it hard to tell whether q12
PWL exp is inherently too costly or whether exact normalization is the blocker.

## Candidate Direction

Measure q12 PWL row-wise softmax with `normalization_mode=reciprocal_quantized`
using q10/q12/q14/q16 reciprocal precision. The denominator lookup uses
`reciprocal_lut_bucket_shift=8` to keep the q12 sum envelope bounded in hardware.

This is measurement-only. It does not claim quality equivalence to the q12 PWL
exact-normalization survivor.

## Evaluation Scope

Run one L1 measurement-only sweep over four Nangate45 configs:

- `softmax_rowwise_q12_pwl_r8_acc28_recip_q10_bucket8`
- `softmax_rowwise_q12_pwl_r8_acc28_recip_q12_bucket8`
- `softmax_rowwise_q12_pwl_r8_acc28_recip_q14_bucket8`
- `softmax_rowwise_q12_pwl_r8_acc28_recip_q16_bucket8`

All rows hold `row_elems=8`, `input_frac_bits=8`, `weight_bits=12`,
`accum_bits=28`, `output_scale=4095`, and `reciprocal_lut_bucket_shift=8`.

## Exclusions

- Full-vocabulary dynamic quantizer hardware.
- Full decoder memory/control/system PPA.
- Prompt-stress or broad-distribution quality claims for reciprocal
  normalization.

## Knowledge Inputs
- `docs/proposals/prop_l1_decoder_q12_pwl_softmax_datapath_v1/analysis_report.md`
- `runs/designs/activations/softmax_rowwise_q12_pwl_r8_acc28_wrapper/metrics.csv`
- `docs/proposals/prop_l1_decoder_q8_recip_norm_datapath_v1/analysis_report.md`
- `docs/proposals/prop_l1_decoder_bf16_recip_norm_datapath_v1/analysis_report.md`

## Direction Gate
- status: approved
- approved_by: developer_agent
- approved_utc: 2026-05-02T10:55:00Z
- note: Immediate follow-up to isolate exact-divider cost from q12 PWL-exp cost.
