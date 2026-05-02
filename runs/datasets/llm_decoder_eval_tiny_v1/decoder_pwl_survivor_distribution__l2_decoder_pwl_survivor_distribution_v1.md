# Decoder PWL Survivor Distribution

- source_sweep: `runs/datasets/llm_decoder_eval_tiny_v1/decoder_quality_sweep__l2_decoder_pwl_survivor_distribution_v1.json`
- sample_file: `runs/datasets/llm_decoder_eval_tiny_v1/samples_distribution_v2.jsonl`
- decision: `q12_pwl_broad_safe_fp16_borderline`
- summary: This broad distribution check reuses the expanded v2 prompt set to test whether the focused PWL/logit survivor rows remain exact-safe outside the six-sample ladder. q10/q8 and bf16 rows remain in the grid as negative precision controls, while exact fp16/q12 rows keep logit-format effects visible.
- recommended_next_step: Promote q12 PWL to RTL/PPA calibration and inspect fp16 PWL misses before treating it as a survivor.

## Template Summary

| template | role | next-token | top-k | gate | miss categories |
|---|---|---:|---:|---|---|
| `candidate_onnx_softmax_exact` | `reference_proxy` | 48/48 | 48/48 | `exact_safe_survivor` | none |
| `grid_exact_logits_q12` | `exact_softmax_control` | 48/48 | 48/48 | `exact_safe_survivor` | none |
| `grid_exact_logits_q10` | `exact_softmax_control` | 47/48 | 48/48 | `topk_safe_not_exact` | arithmetic_short:1 |
| `grid_exact_logits_q8` | `exact_softmax_control` | 46/48 | 48/48 | `topk_safe_not_exact` | arithmetic_short:1, list_continuation:1 |
| `grid_exact_softmax_fp16_path` | `exact_softmax_control` | 48/48 | 48/48 | `exact_safe_survivor` | none |
| `grid_exact_softmax_bf16_path` | `exact_softmax_control` | 47/48 | 48/48 | `topk_safe_not_exact` | arithmetic_short:1 |
| `grid_approx_pwl_float_norm_exact` | `primary_survivor_candidate` | 48/48 | 48/48 | `exact_safe_survivor` | none |
| `grid_approx_pwl_fp16_norm_exact` | `precision_control` | 47/48 | 48/48 | `topk_safe_not_exact` | arithmetic_short:1 |
| `grid_approx_pwl_bf16_norm_exact` | `precision_control` | 46/48 | 48/48 | `topk_safe_not_exact` | arithmetic_short:1, list_continuation:1 |
| `grid_approx_pwl_in_q12_w_q12_norm_exact` | `primary_survivor_candidate` | 48/48 | 48/48 | `exact_safe_survivor` | none |
| `grid_approx_pwl_in_q10_w_q10_norm_exact` | `precision_control` | 47/48 | 48/48 | `topk_safe_not_exact` | arithmetic_short:1 |
| `grid_approx_pwl_in_q8_w_q8_norm_exact` | `precision_control` | 46/48 | 48/48 | `topk_safe_not_exact` | arithmetic_short:1, list_continuation:1 |

## Exact-Safe Survivors

- `grid_approx_pwl_float_norm_exact`
- `grid_approx_pwl_in_q12_w_q12_norm_exact`

## Miss Details

### `grid_exact_logits_q10`

- `dist2_arith_three_plus_five` (arithmetic_short)

### `grid_exact_logits_q8`

- `dist2_arith_three_plus_five` (arithmetic_short)
- `dist2_sequence_months` (list_continuation)

### `grid_exact_softmax_bf16_path`

- `dist2_arith_three_plus_five` (arithmetic_short)

### `grid_approx_pwl_fp16_norm_exact`

- `dist2_arith_three_plus_five` (arithmetic_short)

### `grid_approx_pwl_bf16_norm_exact`

- `dist2_arith_three_plus_five` (arithmetic_short)
- `dist2_sequence_months` (list_continuation)

### `grid_approx_pwl_in_q10_w_q10_norm_exact`

- `dist2_arith_three_plus_five` (arithmetic_short)

### `grid_approx_pwl_in_q8_w_q8_norm_exact`

- `dist2_arith_three_plus_five` (arithmetic_short)
- `dist2_sequence_months` (list_continuation)
