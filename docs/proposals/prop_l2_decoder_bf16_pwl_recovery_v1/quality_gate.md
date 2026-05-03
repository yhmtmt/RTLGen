# Quality Gate

Acceptance for this exploratory recovery job is a completed report with:

- baseline bf16/PWL next-token and top-k counts
- logit-tiebreak bf16/PWL next-token and top-k counts
- recovered sample IDs and regression sample IDs
- a decision on whether tie-breaking is sufficient or full QAT remains needed

This is a calibration proxy. It does not claim trained-weight recovery.
