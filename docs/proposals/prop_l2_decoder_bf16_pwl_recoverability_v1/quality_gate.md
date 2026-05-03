# Quality Gate

Acceptance for this exploratory job is a completed margin report with:

- exact next-token and top-k counts for bf16/PWL
- per-miss reference rank in candidate top-k
- per-miss score gap needed to restore reference top-1
- comparison against correct-sample margin distribution
- a recommendation on whether to run bf16/PWL-aware training or QAT

This is not training proof; it only decides whether training is the next
reasonable experiment.
