# Decoder PWL Failure Diagnosis

- `proposal_id`: `prop_l2_decoder_pwl_failure_diagnosis_v1`
- `item_id`: `l2_decoder_pwl_failure_diagnosis_v1`
- abstraction: `decoder_pwl_failure_diagnosis`

The broad v2 q8/bf16 normalization result found two shared exact-token misses:

- `dist2_arith_three_plus_five`
- `dist2_sequence_months`

Every PWL row preserved top-k, and q8 exact-normalization missed the same two
samples as q8 reciprocal and bf16 reciprocal. That points away from reciprocal
bit width as the immediate blocker.

This job reads the merged broad-v2 sweep and emits a focused JSON and Markdown
diagnosis. It compares exact-reference proxy output against the bf16 PWL path,
q8 PWL exact-normalization path, and q8 PWL reciprocal q10 path for the failing
samples plus a small control set.

Expected output:

- `decoder_pwl_failure_diagnosis__l2_decoder_pwl_failure_diagnosis_v1.json`
- `decoder_pwl_failure_diagnosis__l2_decoder_pwl_failure_diagnosis_v1.md`
