# Native-Checkpoint Mixed/Int8 Score32 Generation Quality

- model_id: `mistralai/Mistral-7B-v0.1`
- decision: `mixed_int8_generation_quality_pass`
- next_step: Candidate passed the bounded generation-quality gate; route this score configuration into the native-checkpoint quality evidence stream.

## Candidate Summaries

| candidate_id | status | teacher_forced_nll_delta_mean | cand_ref_prob | free_run_match | first_div_step_mean |
|---|---|---:|---:|---:|---:|
| score32_float | mixed_int8_generation_quality_pass | 0.002328 | 0.448872 | 0.843750 | 6.625000 |
| qkv8_float_exact | mixed_int8_generation_quality_pass | -0.000049 | 0.449037 | 1.000000 | 8.000000 |
| score32_w16_rtl_exact | mixed_int8_generation_quality_hold | 1.533711 | 0.251913 | 0.078125 | 0.500000 |
| qkv8_q20_pwl_recip_q20_bucket8 | mixed_int8_generation_quality_pass | 0.012834 | 0.444754 | 0.875000 | 7.000000 |
| qkv8_q24_pwl_recip_q24_bucket8 | mixed_int8_generation_quality_pass | 0.018410 | 0.441994 | 0.875000 | 7.000000 |

## Prompt Divergence

| candidate_id | prompt_index | first_divergence_step | match_count | steps |
|---|---:|---:|---:|---:|
| score32_float | 0 | 8 | 8 | 8 |
| score32_float | 1 | 8 | 8 | 8 |
| score32_float | 2 | 5 | 5 | 8 |
| score32_float | 3 | 0 | 1 | 8 |
| score32_float | 4 | 8 | 8 | 8 |
| score32_float | 5 | 8 | 8 | 8 |
| score32_float | 6 | 8 | 8 | 8 |
| score32_float | 7 | 8 | 8 | 8 |
| qkv8_float_exact | 0 | 8 | 8 | 8 |
| qkv8_float_exact | 1 | 8 | 8 | 8 |
| qkv8_float_exact | 2 | 8 | 8 | 8 |
| qkv8_float_exact | 3 | 8 | 8 | 8 |
| qkv8_float_exact | 4 | 8 | 8 | 8 |
| qkv8_float_exact | 5 | 8 | 8 | 8 |
| qkv8_float_exact | 6 | 8 | 8 | 8 |
| qkv8_float_exact | 7 | 8 | 8 | 8 |
| score32_w16_rtl_exact | 0 | 0 | 0 | 8 |
| score32_w16_rtl_exact | 1 | 0 | 0 | 8 |
| score32_w16_rtl_exact | 2 | 1 | 1 | 8 |
| score32_w16_rtl_exact | 3 | 0 | 0 | 8 |
| score32_w16_rtl_exact | 4 | 1 | 1 | 8 |
| score32_w16_rtl_exact | 5 | 1 | 2 | 8 |
| score32_w16_rtl_exact | 6 | 0 | 0 | 8 |
| score32_w16_rtl_exact | 7 | 1 | 1 | 8 |
| qkv8_q20_pwl_recip_q20_bucket8 | 0 | 8 | 8 | 8 |
| qkv8_q20_pwl_recip_q20_bucket8 | 1 | 8 | 8 | 8 |
| qkv8_q20_pwl_recip_q20_bucket8 | 2 | 1 | 1 | 8 |
| qkv8_q20_pwl_recip_q20_bucket8 | 3 | 7 | 7 | 8 |
| qkv8_q20_pwl_recip_q20_bucket8 | 4 | 8 | 8 | 8 |
| qkv8_q20_pwl_recip_q20_bucket8 | 5 | 8 | 8 | 8 |
| qkv8_q20_pwl_recip_q20_bucket8 | 6 | 8 | 8 | 8 |
| qkv8_q20_pwl_recip_q20_bucket8 | 7 | 8 | 8 | 8 |
| qkv8_q24_pwl_recip_q24_bucket8 | 0 | 8 | 8 | 8 |
| qkv8_q24_pwl_recip_q24_bucket8 | 1 | 8 | 8 | 8 |
| qkv8_q24_pwl_recip_q24_bucket8 | 2 | 1 | 1 | 8 |
| qkv8_q24_pwl_recip_q24_bucket8 | 3 | 7 | 7 | 8 |
| qkv8_q24_pwl_recip_q24_bucket8 | 4 | 8 | 8 | 8 |
| qkv8_q24_pwl_recip_q24_bucket8 | 5 | 8 | 8 | 8 |
| qkv8_q24_pwl_recip_q24_bucket8 | 6 | 8 | 8 | 8 |
| qkv8_q24_pwl_recip_q24_bucket8 | 7 | 8 | 8 | 8 |

## Assumptions

- Teacher-forced rows compare against a non-quantized reference model.
- Candidate applies LLaMA-style q/k/v projection quantization plus softmax approximation.
- Decision thresholds are conservative for score32-vs-reference drift in a bounded prompt sample.
