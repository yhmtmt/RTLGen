# Decoder bf16/PWL Exact-Next Recoverability

- `proposal_id`: `prop_l2_decoder_bf16_pwl_recoverability_v1`
- `item_id`: `l2_decoder_bf16_pwl_recoverability_v1`
- abstraction: `decoder_bf16_pwl_recoverability`

bf16 reciprocal PWL is still the practical PPA frontier, but it is exact-next
46/48 on the expanded v2 set. Both misses preserve top-k, so the next question
is whether exact-next recovery requires only small top-1 margin movement.

This job reads the existing broad-v2 bf16/PWL sweep and reports:

- reference token rank in the bf16/PWL candidate top-k
- score gap between the selected wrong token and the reference token
- normal correct-sample top1/top2 margin distribution
- an easy/moderate/hard recoverability class for each miss

Expected output:

- `decoder_bf16_pwl_recoverability__l2_decoder_bf16_pwl_recoverability_v1.json`
- `decoder_bf16_pwl_recoverability__l2_decoder_bf16_pwl_recoverability_v1.md`
