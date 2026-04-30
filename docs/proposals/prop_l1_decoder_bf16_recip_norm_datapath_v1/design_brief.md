# Design Brief

## Proposal
- `proposal_id`: `prop_l1_decoder_bf16_recip_norm_datapath_v1`
- `title`: `Decoder bf16 reciprocal normalization datapath`

## Problem
The decoder quantization outline still treated bf16 reciprocal normalization as
an unmeasured hardware gap. The q8 reciprocal-normalization datapath already
has integrated L1 PPA, so comparing q8 and bf16 without a bf16 measurement
would mix measured and heuristic costs.

## Hypothesis
A row-wise packed-bf16 reciprocal-normalization block can be measured as a
standalone circuit block, providing enough PPA evidence to replace the bf16
normalization placeholder in the next frontier report.

## Evaluation Scope
- `l1_decoder_bf16_recip_norm_datapath_v1_r2`
- platform: Nangate45
- mode: `measurement_only`
- abstraction: `circuit_block`
- config: `runs/designs/activations/bf16_recip_norm_r8_wrapper/config_bf16_recip_norm_r8.json`
- sweep: `runs/campaigns/activations/bf16_recip_norm/sweeps/nangate45_highutil.json`

## Exclusions
- No model-quality rerun is part of this L1 item.
- No full decoder integration PPA is claimed.
- No exact IEEE bf16 exception support is claimed; the RTL clamps unsupported
  cases for measurement.

## Direction Gate
- status: satisfied
- note: PR #300 added the datapath and PR #303 enabled the reciprocal LUT
  synthesis envelope required for the accepted r2 run.
