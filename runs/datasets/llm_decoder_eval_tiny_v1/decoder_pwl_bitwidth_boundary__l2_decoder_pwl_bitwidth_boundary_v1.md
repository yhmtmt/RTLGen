# Decoder PWL Bit-Width Boundary

- source_sweep: `runs/datasets/llm_decoder_eval_tiny_v1/decoder_quality_sweep__l2_decoder_pwl_bitwidth_boundary_v1.json`
- sample_file: `runs/datasets/llm_decoder_eval_tiny_v1/samples_distribution_v2.jsonl`
- decision: `q12_remains_integer_exact_floor`
- minimum_exact_safe_bits: `12`
- minimum_topk_safe_bits: `10`
- summary: The boundary sweep narrows the integer PWL precision floor after q12 proved exact-safe but expensive. It compares q10/q11/q12/q13 PWL exact-normalization rows against the unquantized PWL control and the measured bf16 reciprocal hardware anchor on the same expanded v2 prompt distribution.
- recommended_next_step: Keep q12 as the integer exact-safe floor and prefer bf16/q8 top-k frontier unless exact next-token is required.

## Template Summary

| template | family | bits | next-token | top-k | gate | miss categories |
|---|---|---:|---:|---:|---|---|
| `candidate_onnx_softmax_exact` | `reference` |  | 48/48 | 48/48 | `exact_safe` | none |
| `grid_exact_logits_q13` | `exact_softmax_logit_control` | 13 | 48/48 | 48/48 | `exact_safe` | none |
| `grid_exact_logits_q12` | `exact_softmax_logit_control` | 12 | 48/48 | 48/48 | `exact_safe` | none |
| `grid_exact_logits_q11` | `exact_softmax_logit_control` | 11 | 48/48 | 48/48 | `exact_safe` | none |
| `grid_exact_logits_q10` | `exact_softmax_logit_control` | 10 | 47/48 | 48/48 | `topk_safe_only` | arithmetic_short:1 |
| `grid_approx_pwl_float_norm_exact` | `unquantized_pwl_control` |  | 48/48 | 48/48 | `exact_safe` | none |
| `grid_approx_pwl_in_q13_w_q13_norm_exact` | `pwl_integer_boundary` | 13 | 48/48 | 48/48 | `exact_safe` | none |
| `grid_approx_pwl_in_q12_w_q12_norm_exact` | `pwl_integer_boundary` | 12 | 48/48 | 48/48 | `exact_safe` | none |
| `grid_approx_pwl_in_q11_w_q11_norm_exact` | `pwl_integer_boundary` | 11 | 47/48 | 48/48 | `topk_safe_only` | arithmetic_short:1 |
| `grid_approx_pwl_in_q10_w_q10_norm_exact` | `pwl_integer_boundary` | 10 | 47/48 | 48/48 | `topk_safe_only` | arithmetic_short:1 |
| `grid_approx_pwl_bf16_path` | `bf16_hardware_anchor` |  | 46/48 | 48/48 | `topk_safe_only` | arithmetic_short:1, list_continuation:1 |

## Exact-Safe Integer Rows

- q12: `grid_approx_pwl_in_q12_w_q12_norm_exact`
- q13: `grid_approx_pwl_in_q13_w_q13_norm_exact`

## Miss Details

### `grid_exact_logits_q10`

- `dist2_arith_three_plus_five` (arithmetic_short)

### `grid_approx_pwl_in_q11_w_q11_norm_exact`

- `dist2_arith_three_plus_five` (arithmetic_short)

### `grid_approx_pwl_in_q10_w_q10_norm_exact`

- `dist2_arith_three_plus_five` (arithmetic_short)

### `grid_approx_pwl_bf16_path`

- `dist2_arith_three_plus_five` (arithmetic_short)
- `dist2_sequence_months` (list_continuation)
