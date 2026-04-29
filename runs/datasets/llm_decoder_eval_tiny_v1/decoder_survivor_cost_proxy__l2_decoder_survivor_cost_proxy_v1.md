# Decoder Survivor Cost Proxy

- source_sweep: `runs/datasets/llm_decoder_eval_tiny_v1/decoder_quality_sweep__l2_decoder_survivor_prompt_stress_v1.json`
- recommendation: `grid_approx_pwl_bf16_path`
- reason: grid_approx_pwl_bf16_path passed exact prompt-stress quality and has the lowest relative cost among exact-safe survivors in this proxy model.

## Cost Model

This is a relative planning proxy for decoder softmax/probability-path implementation cost. It weights exact exp paths above PWL paths and lower-width datapaths below fp-style datapaths. It is not RTL, OpenROAD PPA, or final hardware acceptance.

| rank | template | gate | next-token | top-k | relative cost | softmax path |
|---:|---|---|---:|---:|---:|---|
| 1 | `grid_approx_pwl_bf16_path` | `exact_safe_survivor` | 24/24 | 24/24 | 52.000 | `pwl_lut_interpolate` |
| 2 | `grid_approx_pwl_in_q8_w_q8_norm_exact` | `exact_safe_survivor` | 24/24 | 24/24 | 58.000 | `pwl_lut_interpolate` |
| 3 | `grid_logits_q8` | `exact_safe_survivor` | 24/24 | 24/24 | 138.000 | `exact_exp` |
| 4 | `grid_prob_bf16` | `exact_safe_survivor` | 24/24 | 24/24 | 142.000 | `exact_exp` |
| 5 | `grid_prob_fp16` | `exact_safe_survivor` | 24/24 | 24/24 | 142.000 | `exact_exp` |
| 6 | `candidate_onnx_softmax_exact` | `exact_safe_survivor` | 24/24 | 24/24 | 144.000 | `exact_exp` |
| 7 | `grid_approx_pwl_in_q6_w_q6_norm_recip_q10` | `topk_safe_not_exact` | 22/24 | 24/24 | 44.500 | `pwl_lut_interpolate` |
| 8 | `grid_logits_q6` | `topk_safe_not_exact` | 22/24 | 24/24 | 137.500 | `exact_exp` |
| 9 | `grid_logits_q4` | `topk_safe_not_exact` | 20/24 | 24/24 | 137.000 | `exact_exp` |
| 10 | `grid_prob_fp8_e5m2` | `blocked_quality` | 13/24 | 17/24 | 141.000 | `exact_exp` |

## Blocked Or Non-Exact Rows

- `grid_approx_pwl_in_q6_w_q6_norm_recip_q10`: gate `topk_safe_not_exact`, next misses `stress_code_json, stress_dialogue_thanks`, top-k misses `none`
- `grid_logits_q6`: gate `topk_safe_not_exact`, next misses `stress_code_json, stress_dialogue_thanks`, top-k misses `none`
- `grid_logits_q4`: gate `topk_safe_not_exact`, next misses `stress_code_json, stress_dialogue_thanks, stress_markdown, stress_symbolic_math`, top-k misses `none`
- `grid_prob_fp8_e5m2`: gate `blocked_quality`, next misses `stress_ambiguous_preposition, stress_arithmetic_add, stress_arithmetic_subtract, stress_code_json, stress_dialogue_thanks, stress_long_latency, stress_markdown, stress_punctuation_question, stress_punctuation_sentence, stress_symbolic_math, stress_units`, top-k misses `stress_arithmetic_add, stress_arithmetic_subtract, stress_dialogue_thanks, stress_markdown, stress_punctuation_sentence, stress_symbolic_math, stress_units`
