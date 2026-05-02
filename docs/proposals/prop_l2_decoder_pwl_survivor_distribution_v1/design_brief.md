# Decoder PWL Survivor Distribution

- `proposal_id`: `prop_l2_decoder_pwl_survivor_distribution_v1`
- `item_id`: `l2_decoder_pwl_survivor_distribution_v1`
- abstraction: `decoder_pwl_survivor_distribution`

The focused ladder isolated the failure boundary at softmax input/weight or
logit precision under small margins. q12 PWL and unquantized PWL recovered the
focus samples; q8 and bf16 did not.

This job moves from six focus samples to the expanded v2 distribution set. It
uses a trimmed grid that keeps:

- exact q12/q10/q8 and fp16/bf16 controls
- unquantized PWL exact normalization
- PWL fp16/bf16 exact normalization
- PWL q12/q10/q8 exact normalization

Expected output:

- `decoder_quality_sweep__l2_decoder_pwl_survivor_distribution_v1.json`
- `decoder_pwl_survivor_distribution__l2_decoder_pwl_survivor_distribution_v1.json`
- `decoder_pwl_survivor_distribution__l2_decoder_pwl_survivor_distribution_v1.md`
