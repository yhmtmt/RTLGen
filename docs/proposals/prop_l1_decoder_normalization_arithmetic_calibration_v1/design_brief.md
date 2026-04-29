# Design Brief

- `proposal_id`: `prop_l1_decoder_normalization_arithmetic_calibration_v1`
- `title`: `Decoder normalization arithmetic calibration`
- `layer`: `l1`
- `kind`: `circuit`

## Context

The decoder q8 normalization frontier selected
`grid_approx_pwl_in_q8_w_q8_norm_recip_q10` because it preserved the
prompt-stress exact next-token and top-k gate while scoring lower than exact
normalization in the planning proxy. That score is a hand-written heuristic,
not a research-derived or physically calibrated model.

RTLGen exists to close this gap. The next step is to measure the integer
arithmetic primitives that the q8 reciprocal path depends on before fitting any
calibrated normalization-cost model.

## Calibration Scope

Run two L1 OpenROAD measurement-only sweeps on Nangate45:

- `l1_decoder_norm_q8_recip_mult_calibration_v1`: unsigned multiplier wrappers
  for 8/16/32-bit datapath envelopes.
- `l1_decoder_norm_accumulator_adder_calibration_v1`: unsigned 16/32/64-bit
  adders for normalization sum and accumulator envelopes.

This scope intentionally does not claim full decoder-softmax PPA. It measures
available RTLGen primitive blocks and records the unsupported blocks as gaps:

- exact normalization still needs a divider or reciprocal-generation block;
- bf16 reciprocal normalization still needs a bf16-compatible reciprocal and
  multiply integration point;
- table lookup, rounding, control, and row-level softmax integration remain
  outside this primitive calibration job.

## Expected Use

The merged metrics should replace the current uncalibrated multiplier/adder
terms in the decoder planning scripts. If the measurements contradict the q10
heuristic ordering, the next q8 frontier decision should be updated before any
architecture promotion.
