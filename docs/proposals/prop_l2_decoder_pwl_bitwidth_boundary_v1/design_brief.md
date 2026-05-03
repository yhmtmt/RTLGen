# Decoder PWL Integer Bit-Width Boundary

- `proposal_id`: `prop_l2_decoder_pwl_bitwidth_boundary_v1`
- `item_id`: `l2_decoder_pwl_bitwidth_boundary_v1`
- abstraction: `decoder_pwl_bitwidth_boundary`

Current evidence puts the measured hardware frontier at bf16/q8 reciprocal PWL
for PPA, while q12 PWL is the integer exact-safe quality point. The q12 datapath
cost is high enough that the immediate frontier should check the missing
integer boundary before more PPA work.

This Layer 2 job runs the expanded v2 prompt distribution with:

- exact-softmax q10/q11/q12/q13 logit controls
- PWL q10/q11/q12/q13 exact-normalization rows
- unquantized PWL exact-normalization control
- bf16 reciprocal PWL anchor

Expected output:

- `decoder_quality_sweep__l2_decoder_pwl_bitwidth_boundary_v1.json`
- `decoder_pwl_bitwidth_boundary__l2_decoder_pwl_bitwidth_boundary_v1.json`
- `decoder_pwl_bitwidth_boundary__l2_decoder_pwl_bitwidth_boundary_v1.md`
