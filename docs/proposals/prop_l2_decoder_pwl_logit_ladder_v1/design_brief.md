# Decoder PWL/Logit Sensitivity Ladder

- `proposal_id`: `prop_l2_decoder_pwl_logit_ladder_v1`
- `item_id`: `l2_decoder_pwl_logit_ladder_v1`
- abstraction: `decoder_pwl_logit_sensitivity_ladder`

The previous diagnosis showed the same exact-token misses across bf16 PWL, q8
PWL exact-normalization, and q8 PWL reciprocal-normalization rows. That ruled
out reciprocal precision as the immediate explanation.

This job tests the two failing samples plus four nearby controls. The ladder
compares exact-softmax logit precision, exact-softmax fp16/bf16 softmax
input/weight precision, unquantized PWL, PWL q12/q10/q8/q6 input/weight
precision, and q8 PWL reciprocal normalization.

Expected output:

- `decoder_quality_sweep__l2_decoder_pwl_logit_ladder_v1.json`
- `decoder_pwl_logit_ladder__l2_decoder_pwl_logit_ladder_v1.json`
- `decoder_pwl_logit_ladder__l2_decoder_pwl_logit_ladder_v1.md`
