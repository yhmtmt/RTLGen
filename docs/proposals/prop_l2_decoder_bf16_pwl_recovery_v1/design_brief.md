# Design Brief

- `proposal_id`: `prop_l2_decoder_bf16_pwl_recovery_v1`
- `item_id`: `l2_decoder_bf16_pwl_recovery_v1`
- abstraction: `decoder_bf16_pwl_recovery`

The prior recoverability job found two bf16/PWL exact-next misses, both with
the reference token still rank 2 and a zero score gap. This job tests the
smallest useful recovery mechanism: keep the bf16/PWL score path unchanged and
use the post-logit value only as a deterministic tie-breaker when scores are
exactly equal.

Expected artifacts:

- `decoder_quality_sweep__l2_decoder_bf16_pwl_recovery_v1.json`
- `decoder_bf16_pwl_recovery__l2_decoder_bf16_pwl_recovery_v1.json`
- `decoder_bf16_pwl_recovery__l2_decoder_bf16_pwl_recovery_v1.md`
