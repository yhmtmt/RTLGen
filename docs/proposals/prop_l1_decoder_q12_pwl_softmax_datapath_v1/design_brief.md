# Design Brief

## Proposal
- `proposal_id`: `prop_l1_decoder_q12_pwl_softmax_datapath_v1`
- `title`: `Decoder q12 PWL softmax datapath calibration`
- `layer`: `layer1`
- `kind`: `circuit_block`

## Problem

The decoder PWL survivor distribution found q12 PWL exact normalization safe on
the current tiny decoder benchmark, but the existing RTLGen row-wise softmax
block only measured the older q8 shift-exp approximation. A cost comparison
against q8 exact, q8 reciprocal, or bf16 normalization needs a hardware point
that actually emits the q12 PWL-exp datapath.

## Candidate Direction

Add a `softmax_rowwise` `impl=pwl_exp` mode with fixed-point q12 logits,
q12 PWL weights, and exact normalization. The PWL anchors match the decoder
software approximation at shifted logits 0, -2, -4, and -8.

This first hardware point intentionally excludes the full dynamic symmetric
quantizer used by the software sweep. It is a row-wise datapath PPA proxy, not
an end-to-end decoder-softmax implementation.

## Evaluation Scope

Run one L1 measurement-only Nangate45 sweep:

- `softmax_rowwise_q12_pwl_r8_acc28`
- `row_elems=8`
- `input_frac_bits=8`
- `weight_bits=12`
- `output_scale=4095`
- `normalization_mode=exact`

The result should be compared against existing q8 reciprocal and bf16
normalization datapath results on separate timing, power, and area axes.

## Exclusions

- Full-vocabulary dynamic quantizer hardware.
- q12 PWL reciprocal-normalization approximation.
- Full decoder memory/control/system PPA.
- New prompt-stress quality thresholds.

## Knowledge Inputs
- `runs/datasets/llm_decoder_eval_tiny_v1/decoder_pwl_survivor_distribution__l2_decoder_pwl_survivor_distribution_v1.md`
- `docs/proposals/prop_l1_decoder_q8_recip_norm_datapath_v1/analysis_report.md`
- `docs/proposals/prop_l1_decoder_bf16_recip_norm_datapath_v1/analysis_report.md`

## Direction Gate
- status: approved
- approved_by: developer_agent
- approved_utc: 2026-05-02T05:45:00Z
- note: Immediate frontier follow-up after q12 PWL survived the broad decoder distribution check.
