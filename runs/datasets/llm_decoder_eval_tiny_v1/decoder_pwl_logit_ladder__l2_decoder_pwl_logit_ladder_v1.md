# Decoder PWL Logit Sensitivity Ladder

- source_sweep: `runs/datasets/llm_decoder_eval_tiny_v1/decoder_quality_sweep__l2_decoder_pwl_logit_ladder_v1.json`
- decision: `softmax_input_weight_precision_margin_sensitivity`
- summary: The unquantized PWL row and q12 PWL row preserve both focus samples, while q8 PWL flips both. Exact-softmax q10/q8 and bf16 variants also flip margin-sensitive focus samples. The immediate blocker is low-precision softmax input/weight or logit representation under tiny margins, not the PWL curve itself or reciprocal normalization.
- recommended_next_step: Promote q12 or fp16-style PWL rows to the next broad distribution check and estimate their hardware cost before accepting q8/bf16 exact-next behavior.

## Template Summary

| template | family | next-token | top-k | focus misses | control misses |
|---|---|---:|---:|---|---|
| `candidate_onnx_softmax_exact` | exact_reference_proxy | 6/6 | 6/6 | none | none |
| `grid_exact_logits_q12` | exact_softmax_variant | 6/6 | 6/6 | none | none |
| `grid_exact_logits_q10` | exact_softmax_variant | 5/6 | 6/6 | dist2_arith_three_plus_five | none |
| `grid_exact_logits_q8` | exact_softmax_variant | 4/6 | 6/6 | dist2_arith_three_plus_five, dist2_sequence_months | none |
| `grid_exact_logits_q6` | exact_softmax_variant | 4/6 | 6/6 | dist2_arith_three_plus_five, dist2_sequence_months | none |
| `grid_exact_softmax_fp16_path` | exact_softmax_variant | 6/6 | 6/6 | none | none |
| `grid_exact_softmax_bf16_path` | exact_softmax_variant | 5/6 | 6/6 | dist2_arith_three_plus_five | none |
| `grid_approx_pwl_float_norm_exact` | pwl | 6/6 | 6/6 | none | none |
| `grid_approx_pwl_fp16_norm_exact` | pwl | 5/6 | 6/6 | dist2_arith_three_plus_five | none |
| `grid_approx_pwl_bf16_norm_exact` | pwl | 4/6 | 6/6 | dist2_arith_three_plus_five, dist2_sequence_months | none |
| `grid_approx_pwl_bf16_path` | pwl | 4/6 | 6/6 | dist2_arith_three_plus_five, dist2_sequence_months | none |
| `grid_approx_pwl_in_q12_w_q12_norm_exact` | pwl | 6/6 | 6/6 | none | none |
| `grid_approx_pwl_in_q10_w_q10_norm_exact` | pwl | 5/6 | 6/6 | dist2_arith_three_plus_five | none |
| `grid_approx_pwl_in_q8_w_q8_norm_exact` | pwl | 4/6 | 6/6 | dist2_arith_three_plus_five, dist2_sequence_months | none |
| `grid_approx_pwl_in_q6_w_q6_norm_exact` | pwl | 3/6 | 6/6 | dist2_arith_three_plus_five, dist2_sequence_months | dist2_sequence_weekdays |
| `grid_approx_pwl_in_q8_w_fp_norm_exact` | pwl | 4/6 | 6/6 | dist2_arith_three_plus_five, dist2_sequence_months | none |
| `grid_approx_pwl_in_fp_w_q8_norm_exact` | pwl | 4/6 | 6/6 | dist2_arith_three_plus_five, dist2_sequence_months | none |
| `grid_approx_pwl_in_q8_w_q8_norm_recip_q10` | pwl | 4/6 | 6/6 | dist2_arith_three_plus_five, dist2_sequence_months | none |
| `grid_approx_pwl_in_q8_w_q8_norm_recip_q12` | pwl | 4/6 | 6/6 | dist2_arith_three_plus_five, dist2_sequence_months | none |

## Focus Samples

### `dist2_arith_three_plus_five`

- prompt: `3 + 5 =`
- exact next: ` footsteps` (27146)
- `grid_exact_logits_q10`: next ` =` (796), exact_rank_in_candidate_topk=2, topk_contains=1
- `grid_exact_logits_q8`: next ` =` (796), exact_rank_in_candidate_topk=2, topk_contains=1
- `grid_exact_logits_q6`: next ` =` (796), exact_rank_in_candidate_topk=2, topk_contains=1
- `grid_exact_softmax_bf16_path`: next ` =` (796), exact_rank_in_candidate_topk=2, topk_contains=1
- `grid_approx_pwl_fp16_norm_exact`: next ` =` (796), exact_rank_in_candidate_topk=2, topk_contains=1
- `grid_approx_pwl_bf16_norm_exact`: next ` =` (796), exact_rank_in_candidate_topk=2, topk_contains=1
- `grid_approx_pwl_bf16_path`: next ` =` (796), exact_rank_in_candidate_topk=2, topk_contains=1
- `grid_approx_pwl_in_q10_w_q10_norm_exact`: next ` =` (796), exact_rank_in_candidate_topk=2, topk_contains=1
- `grid_approx_pwl_in_q8_w_q8_norm_exact`: next ` =` (796), exact_rank_in_candidate_topk=2, topk_contains=1
- `grid_approx_pwl_in_q6_w_q6_norm_exact`: next ` =` (796), exact_rank_in_candidate_topk=2, topk_contains=1
- `grid_approx_pwl_in_q8_w_fp_norm_exact`: next ` =` (796), exact_rank_in_candidate_topk=2, topk_contains=1
- `grid_approx_pwl_in_fp_w_q8_norm_exact`: next ` =` (796), exact_rank_in_candidate_topk=2, topk_contains=1
- `grid_approx_pwl_in_q8_w_q8_norm_recip_q10`: next ` =` (796), exact_rank_in_candidate_topk=2, topk_contains=1
- `grid_approx_pwl_in_q8_w_q8_norm_recip_q12`: next ` =` (796), exact_rank_in_candidate_topk=2, topk_contains=1

### `dist2_sequence_months`

- prompt: `January, February, March,`
- exact next: ` Drinking` (43963)
- `grid_exact_logits_q8`: next `,` (11), exact_rank_in_candidate_topk=2, topk_contains=1
- `grid_exact_logits_q6`: next `,` (11), exact_rank_in_candidate_topk=2, topk_contains=1
- `grid_approx_pwl_bf16_norm_exact`: next `,` (11), exact_rank_in_candidate_topk=2, topk_contains=1
- `grid_approx_pwl_bf16_path`: next `,` (11), exact_rank_in_candidate_topk=2, topk_contains=1
- `grid_approx_pwl_in_q8_w_q8_norm_exact`: next `,` (11), exact_rank_in_candidate_topk=2, topk_contains=1
- `grid_approx_pwl_in_q6_w_q6_norm_exact`: next `,` (11), exact_rank_in_candidate_topk=2, topk_contains=1
- `grid_approx_pwl_in_q8_w_fp_norm_exact`: next `,` (11), exact_rank_in_candidate_topk=2, topk_contains=1
- `grid_approx_pwl_in_fp_w_q8_norm_exact`: next `,` (11), exact_rank_in_candidate_topk=2, topk_contains=1
- `grid_approx_pwl_in_q8_w_q8_norm_recip_q10`: next `,` (11), exact_rank_in_candidate_topk=2, topk_contains=1
- `grid_approx_pwl_in_q8_w_q8_norm_recip_q12`: next `,` (11), exact_rank_in_candidate_topk=2, topk_contains=1
