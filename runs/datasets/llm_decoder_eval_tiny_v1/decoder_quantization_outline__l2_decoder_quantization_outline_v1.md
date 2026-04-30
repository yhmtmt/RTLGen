# Decoder Quantization Outline

- fp_sweep: `runs/datasets/llm_decoder_eval_tiny_v1/decoder_quality_sweep__l2_decoder_fp_probability_format_sweep_v1.json`
- distribution_sweep: `runs/datasets/llm_decoder_eval_tiny_v1/decoder_quality_sweep__l2_decoder_distribution_robustness_v1.json`
- q8_norm_frontier: `runs/datasets/llm_decoder_eval_tiny_v1/decoder_q8_norm_frontier__l2_decoder_q8_normalization_frontier_v1.json`

## Interpretation

- bf16/fp16 probability and reciprocal software paths preserve next-token and top-k on the current fp-format and distribution sweeps.
- fixed q8 probability output storage is blocked on the distribution robustness sweep, while q8/q6 logit quantization remains exact-safe there.
- fp8 probability storage is not a current frontier candidate: e5m2 drops samples and e4m3 is blocked in both sweeps.
- q8 reciprocal and bf16 reciprocal normalization now have measured integrated PPA for the current row-8 Nangate45 datapath framing.

## Comparable Dimensions

### Approximate PWL Probability Path

- scope: `within_dimension_only`; rows: 5; exact-safe: 5; top-k-only: 0; blocked: 0

| source | template | descriptor | gate | next-token | top-k | misses |
|---|---|---|---|---:|---:|---|
| `distribution` | `grid_approx_pwl_bf16_path` | input=bf16, weight=bf16, recip=bf16, norm=reciprocal_float | `exact_safe` | 12/12 | 12/12 |  |
| `distribution` | `grid_approx_pwl_in_q6_w_q6_norm_recip_q10` | input_q6, weight_q6, recip_q10, norm=reciprocal_quantized | `exact_safe` | 12/12 | 12/12 |  |
| `distribution` | `grid_approx_pwl_in_q8_w_q8_norm_exact` | input_q8, weight_q8 | `exact_safe` | 12/12 | 12/12 |  |
| `fp_format` | `grid_approx_pwl_bf16_path` | input=bf16, weight=bf16, recip=bf16, norm=reciprocal_float | `exact_safe` | 5/5 | 5/5 |  |
| `fp_format` | `grid_approx_pwl_fp16_path` | input=fp16, weight=fp16, recip=fp16, norm=reciprocal_float | `exact_safe` | 5/5 | 5/5 |  |

### Logit Format

- scope: `within_dimension_only`; rows: 7; exact-safe: 5; top-k-only: 2; blocked: 0

| source | template | descriptor | gate | next-token | top-k | misses |
|---|---|---|---|---:|---:|---|
| `distribution` | `grid_logits_q6` | logit_q6 | `exact_safe` | 12/12 | 12/12 |  |
| `distribution` | `grid_logits_q8` | logit_q8 | `exact_safe` | 12/12 | 12/12 |  |
| `fp_format` | `grid_logits_bf16` | logit=bf16 | `exact_safe` | 5/5 | 5/5 |  |
| `fp_format` | `grid_logits_fp16` | logit=fp16 | `exact_safe` | 5/5 | 5/5 |  |
| `fp_format` | `grid_logits_fp8_e4m3` | logit=fp8_e4m3 | `exact_safe` | 5/5 | 5/5 |  |
| `distribution` | `grid_logits_q4` | logit_q4 | `topk_safe_only` | 11/12 | 12/12 | dist_math_symbolic |
| `fp_format` | `grid_logits_fp8_e5m2` | logit=fp8_e5m2 | `topk_safe_only` | 4/5 | 5/5 | math_two_plus_two |

### Normalization Reciprocal Format

- scope: `within_dimension_only`; rows: 2; exact-safe: 2; top-k-only: 0; blocked: 0

| source | template | descriptor | gate | next-token | top-k | misses |
|---|---|---|---|---:|---:|---|
| `fp_format` | `grid_norm_recip_bf16` | recip=bf16, norm=reciprocal_float | `exact_safe` | 5/5 | 5/5 |  |
| `fp_format` | `grid_norm_recip_fp16` | recip=fp16, norm=reciprocal_float | `exact_safe` | 5/5 | 5/5 |  |

### Probability Output Format

- scope: `within_dimension_only`; rows: 9; exact-safe: 4; top-k-only: 0; blocked: 5

| source | template | descriptor | gate | next-token | top-k | misses |
|---|---|---|---|---:|---:|---|
| `distribution` | `grid_prob_bf16` | prob=bf16 | `exact_safe` | 12/12 | 12/12 |  |
| `distribution` | `grid_prob_fp16` | prob=fp16 | `exact_safe` | 12/12 | 12/12 |  |
| `fp_format` | `grid_prob_bf16` | prob=bf16 | `exact_safe` | 5/5 | 5/5 |  |
| `fp_format` | `grid_prob_fp16` | prob=fp16 | `exact_safe` | 5/5 | 5/5 |  |
| `distribution` | `grid_prob_fp8_e4m3` | prob=fp8_e4m3 | `blocked` | 0/12 | 0/12 | dist_ambiguous_article, dist_code_like, dist_commonsense_color, dist_dialogue, dist_geo_capital_short, dist_list_continuation, dist_long_context, dist_math_symbolic, dist_punctuation, dist_quote_midphrase, dist_repetition, dist_weekday_calendar |
| `distribution` | `grid_prob_fp8_e5m2` | prob=fp8_e5m2 | `blocked` | 10/12 | 10/12 | dist_math_symbolic, dist_punctuation |
| `distribution` | `grid_prob_q8` | prob_q8 | `blocked` | 0/12 | 0/12 | dist_ambiguous_article, dist_code_like, dist_commonsense_color, dist_dialogue, dist_geo_capital_short, dist_list_continuation, dist_long_context, dist_math_symbolic, dist_punctuation, dist_quote_midphrase, dist_repetition, dist_weekday_calendar |
| `fp_format` | `grid_prob_fp8_e4m3` | prob=fp8_e4m3 | `blocked` | 0/5 | 0/5 | color_banana, geo_france_capital, math_two_plus_two, quote_complete, weekday_after_monday |
| `fp_format` | `grid_prob_fp8_e5m2` | prob=fp8_e5m2 | `blocked` | 4/5 | 4/5 | math_two_plus_two |

### Softmax Input Format

- scope: `within_dimension_only`; rows: 2; exact-safe: 2; top-k-only: 0; blocked: 0

| source | template | descriptor | gate | next-token | top-k | misses |
|---|---|---|---|---:|---:|---|
| `fp_format` | `grid_softmax_input_bf16` | input=bf16 | `exact_safe` | 5/5 | 5/5 |  |
| `fp_format` | `grid_softmax_input_fp16` | input=fp16 | `exact_safe` | 5/5 | 5/5 |  |

### Softmax Weight Format

- scope: `within_dimension_only`; rows: 2; exact-safe: 2; top-k-only: 0; blocked: 0

| source | template | descriptor | gate | next-token | top-k | misses |
|---|---|---|---|---:|---:|---|
| `fp_format` | `grid_softmax_weight_bf16` | weight=bf16 | `exact_safe` | 5/5 | 5/5 |  |
| `fp_format` | `grid_softmax_weight_fp16` | weight=fp16 | `exact_safe` | 5/5 | 5/5 |  |

### Reference

- scope: `within_dimension_only`; rows: 2; exact-safe: 2; top-k-only: 0; blocked: 0

| source | template | descriptor | gate | next-token | top-k | misses |
|---|---|---|---|---:|---:|---|
| `distribution` | `candidate_onnx_softmax_exact` | reference | `exact_safe` | 12/12 | 12/12 |  |
| `fp_format` | `candidate_onnx_softmax_exact` | reference | `exact_safe` | 5/5 | 5/5 |  |

## Measured Q8 Normalization PPA

- `grid_approx_pwl_bf16_path` rank 1 via `measured_bf16_reciprocal_datapath_ppa`: critical_path_ns=4.2869, die_area=50690.271025, total_power_mw=0.00479
- `grid_approx_pwl_in_q8_w_q8_norm_recip_q10` rank 2 via `measured_q8_reciprocal_datapath_ppa`: critical_path_ns=5.6126, die_area=39776.3136, total_power_mw=0.00463
- `grid_approx_pwl_in_q8_w_q8_norm_recip_q12` rank 3 via `measured_q8_reciprocal_datapath_ppa`: critical_path_ns=5.7554, die_area=52118.607025, total_power_mw=0.014
- `grid_approx_pwl_in_q8_w_q8_norm_recip_q14` rank 4 via `measured_q8_reciprocal_datapath_ppa`: critical_path_ns=5.7617, die_area=52360.880625, total_power_mw=0.00637
- `grid_approx_pwl_in_q8_w_q8_norm_recip_q16` rank 5 via `measured_q8_reciprocal_datapath_ppa`: critical_path_ns=5.814, die_area=45315.765625, total_power_mw=0.0321
- `grid_approx_pwl_in_q8_w_q8_norm_exact` rank 6 via `measured_q8_exact_datapath_ppa`: critical_path_ns=20.2712, die_area=105898.1764, total_power_mw=1.11

## Next Step

- Use the measured q8 reciprocal and bf16 reciprocal datapaths as the immediate hardware frontier.
- Broaden distribution coverage before treating these exact-safe rows as generally robust across weights and prompts.
