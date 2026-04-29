# Design Brief

## Proposal
- `proposal_id`: `prop_l1_decoder_q8_recip_norm_datapath_v1`
- `title`: `Decoder q8 reciprocal normalization datapath`
- `layer`: `layer1`
- `kind`: `circuit_block`

## Problem

The decoder q8 normalization frontier selected q10 reciprocal normalization on
quality and heuristic planning cost. PR #283 then calibrated the multiplier and
adder primitive terms, but showed that q10/q12/q14/q16 are physically tied under
the same primitive envelope. The missing evidence is the integrated
normalization datapath: reciprocal generation, reciprocal multiply, rounding,
and row-level softmax wiring.

The current RTLGen row-wise int8 softmax block uses a Verilog `/ sum_weights`
divider for exact normalization. That is not the q8 reciprocal architecture
under investigation.

## Candidate Direction

Add a divider-free `softmax_rowwise` normalization mode:

- `normalization_mode: reciprocal_quantized`
- `reciprocal_bits: 10/12/14/16`
- `reciprocal_lut_bucket_shift: 4`

The emitted RTL uses a denominator-indexed reciprocal lookup table and a
multiply/shift normalization path. This keeps the architecture aligned with the
decoder q8 reciprocal frontier and gives OpenROAD an integrated block to
measure. The first retry uses a bucketed reciprocal lookup to avoid Yosys
inferring a memory larger than the OpenROAD synth prefilter allows.

## Evaluation Scope

Run one L1 measurement-only sweep over four Nangate45 configs:

- `softmax_rowwise_int8_r8_acc24_recip_q10`
- `softmax_rowwise_int8_r8_acc24_recip_q12`
- `softmax_rowwise_int8_r8_acc24_recip_q14`
- `softmax_rowwise_int8_r8_acc24_recip_q16`

All rows keep `row_elems=8`, `max_shift=7`, `accum_bits=24`, and
`output_scale=127` so the primary variable is reciprocal precision. The
reciprocal denominator bucket size is held constant across rows.

## Exclusions

- This does not measure bf16 reciprocal or multiply/convert datapaths.
- This does not claim full decoder-softmax system PPA.
- This does not change the Layer-2 prompt-stress quality gate.

## Knowledge Inputs

- `docs/proposals/prop_l1_decoder_normalization_arithmetic_calibration_v1/analysis_report.md`
- `runs/datasets/llm_decoder_eval_tiny_v1/decoder_norm_ppa_calibration__prop_l1_decoder_normalization_arithmetic_calibration_v1.md`
- `docs/proposals/prop_l2_decoder_q8_normalization_frontier_v1/analysis_report.md`

## Direction Gate

- status: approved
- approved_by: developer_agent
- approved_utc: 2026-04-29T00:00:00Z
- note: Immediate frontier follow-up after primitive calibration.
