# Quality Gate

The evaluation should:

- read the merged broad v2 sweep artifact
- compare exact-reference proxy, bf16 PWL, q8 PWL exact-normalization, and q8
  PWL reciprocal q10 rows
- report the two shared exact-token miss samples with exact and candidate top-k
  context
- include control samples that remained exact-safe
- conclude whether the likely blocker is shared PWL/logit-margin sensitivity,
  normalization precision, or mixed evidence

Acceptance is a complete diagnostic artifact. It does not need to choose the
final decoder probability format.
