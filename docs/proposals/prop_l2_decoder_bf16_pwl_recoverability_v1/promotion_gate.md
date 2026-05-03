# Promotion Gate

- promote a training/QAT job only if misses are top-k contained and the required
  score gaps are small relative to normal correct-sample margins
- otherwise keep q12 exact-safe hardware as the exact-next fallback and continue
  using bf16/q8 reciprocal as the practical PPA frontier
