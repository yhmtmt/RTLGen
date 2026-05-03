# Decoder bf16/PWL Exact-Next Recoverability

Proposal workspace for `prop_l2_decoder_bf16_pwl_recoverability_v1`.

This job measures whether the bf16 reciprocal PWL exact-next misses are small
rank-2 margin shifts. It is a screen for whether a bf16/PWL-aware training or
QAT experiment is worth running.
