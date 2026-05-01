# Decoder PWL Failure Diagnosis

- source_sweep: `runs/datasets/llm_decoder_eval_tiny_v1/decoder_quality_sweep__l2_decoder_q8_norm_distribution_broad_v2.json`
- decision: `shared_pwl_softmax_or_logit_margin_sensitivity`
- summary: The same exact-token misses appear across bf16 reciprocal, q8 exact normalization, and q8 reciprocal q10. Normalization precision is unlikely to be the root cause.
- recommended_next_step: Run a focused PWL/logit sensitivity ladder on the failing arithmetic and sequence samples, with exact top-k retained as the broad gate and exact next-token treated as a margin stress signal.

## Template Summary

| template | next-token | top-k | misses |
|---|---:|---:|---|
| `candidate_onnx_softmax_exact` | 48/48 | 48/48 | none |
| `grid_approx_pwl_bf16_path` | 46/48 | 48/48 | dist2_arith_three_plus_five, dist2_sequence_months |
| `grid_approx_pwl_in_q8_w_q8_norm_exact` | 46/48 | 48/48 | dist2_arith_three_plus_five, dist2_sequence_months |
| `grid_approx_pwl_in_q8_w_q8_norm_recip_q10` | 46/48 | 48/48 | dist2_arith_three_plus_five, dist2_sequence_months |

## Focus Samples

### `dist2_arith_three_plus_five`

- category: `arithmetic_short`
- prompt: `3 + 5 =`
- exact next: ` footsteps` (27146)
- `grid_approx_pwl_bf16_path`: next ` =` (796), exact_rank_in_candidate_topk=2, next_match=0, topk_contains=1, candidate-minus-exact-score=0
- `grid_approx_pwl_in_q8_w_q8_norm_exact`: next ` =` (796), exact_rank_in_candidate_topk=2, next_match=0, topk_contains=1, candidate-minus-exact-score=0
- `grid_approx_pwl_in_q8_w_q8_norm_recip_q10`: next ` =` (796), exact_rank_in_candidate_topk=2, next_match=0, topk_contains=1, candidate-minus-exact-score=0

### `dist2_sequence_months`

- category: `list_continuation`
- prompt: `January, February, March,`
- exact next: ` Drinking` (43963)
- `grid_approx_pwl_bf16_path`: next `,` (11), exact_rank_in_candidate_topk=2, next_match=0, topk_contains=1, candidate-minus-exact-score=0
- `grid_approx_pwl_in_q8_w_q8_norm_exact`: next `,` (11), exact_rank_in_candidate_topk=2, next_match=0, topk_contains=1, candidate-minus-exact-score=0
- `grid_approx_pwl_in_q8_w_q8_norm_recip_q10`: next `,` (11), exact_rank_in_candidate_topk=2, next_match=0, topk_contains=1, candidate-minus-exact-score=0

## Control Samples

- `dist2_arith_two_plus_two` (arithmetic_short): exact ` indigenous`
- `dist2_arith_six_times_two` (arithmetic_short): exact ` =`
- `dist2_sequence_numbers` (list_continuation): exact `,`
- `dist2_sequence_weekdays` (list_continuation): exact ` Drinking`
