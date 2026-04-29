# Decoder q8 Normalization Frontier

- source_sweep: `runs/datasets/llm_decoder_eval_tiny_v1/decoder_quality_sweep__l2_decoder_q8_normalization_frontier_v1.json`
- decision: `q8_reciprocal_candidate_survived`
- selected_candidate: `grid_approx_pwl_in_q8_w_q8_norm_recip_q10`
- reason: grid_approx_pwl_in_q8_w_q8_norm_recip_q10 preserved the exact prompt-stress gate with lower modeled normalization cost than q8 exact normalization. It should be costed against the bf16 anchor next.

## Quality And Normalization Cost

| template | role | gate | next-token | top-k | norm mode | recip bits | norm cost |
|---|---|---|---:|---:|---|---:|---:|
| `grid_approx_pwl_in_q8_w_q8_norm_recip_q10` | `q8_reciprocal_candidate` | `exact_safe_survivor` | 24/24 | 24/24 | `reciprocal_quantized` | 10 | 17.500 |
| `grid_approx_pwl_in_q8_w_q8_norm_recip_q12` | `q8_reciprocal_candidate` | `exact_safe_survivor` | 24/24 | 24/24 | `reciprocal_quantized` | 12 | 19.000 |
| `grid_approx_pwl_in_q8_w_q8_norm_recip_q14` | `q8_reciprocal_candidate` | `exact_safe_survivor` | 24/24 | 24/24 | `reciprocal_quantized` | 14 | 20.500 |
| `grid_approx_pwl_bf16_path` | `bf16_primary_anchor` | `exact_safe_survivor` | 24/24 | 24/24 | `reciprocal_float` |  | 22.000 |
| `grid_approx_pwl_in_q8_w_q8_norm_recip_q16` | `q8_reciprocal_candidate` | `exact_safe_survivor` | 24/24 | 24/24 | `reciprocal_quantized` | 16 | 22.000 |
| `grid_approx_pwl_in_q8_w_q8_norm_exact` | `q8_exact_normalization_baseline` | `exact_safe_survivor` | 24/24 | 24/24 | `exact` |  | 52.000 |

## Blocked Rows

- none

## Next Step

- If a q8 reciprocal row survives, compare it against bf16 reciprocal PWL with an RTL/OpenROAD-oriented block estimate.
- If no q8 reciprocal row survives, keep q8 exact normalization only as a quality baseline and move the implementation frontier to bf16 reciprocal PWL.
