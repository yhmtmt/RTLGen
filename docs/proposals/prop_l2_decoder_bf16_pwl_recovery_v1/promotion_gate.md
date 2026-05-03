# Promotion Gate

Promote the bf16/PWL recovery path only if:

- logit tie-breaking recovers all baseline bf16/PWL exact-next misses
- no new next-token regressions appear on distribution v2
- top-k containment remains complete
