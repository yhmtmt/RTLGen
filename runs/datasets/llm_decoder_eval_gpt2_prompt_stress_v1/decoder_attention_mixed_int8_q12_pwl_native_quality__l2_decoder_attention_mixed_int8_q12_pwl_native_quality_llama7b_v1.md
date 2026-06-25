# Native-Checkpoint Mixed/Int8 Attention Shadow Quality

- model_id: `mistralai/Mistral-7B-v0.1`
- decision: `mixed_int8_native_attention_shadow_hold`
- best_candidate: `qkv8_float_exact` (mixed_int8_native_attention_shadow_pass)
- attention_head_count: `32`
- kv_head_count: `8`
- gqa_group_size: `4.0`
- expected_gqa_group_size: `4`

## Candidates

| candidate_id | q_bits | k_bits | v_bits | score_bits | weight_bits | softmax_mode | top1_match | topk_contains | mean_cosine | mean_kl | decision |
|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|---|
| qkv8_float_exact | 8 | 8 | 8 | 24 | 16 | float_exact | 1.000000 | 1.000000 | 0.999899 | 0.001243 | mixed_int8_native_attention_shadow_pass |
| qkv8_score24_float | 8 | 8 | 8 | 24 | 16 | float_quantized | 0.968750 | 1.000000 | 0.999903 | 0.001412 | mixed_int8_native_attention_shadow_hold |
| qkv8_score24_rtl_exact | 8 | 8 | 8 | 24 | 8 | rtl_exact | 0.593750 | 0.796875 | 0.946173 | 1.050531 | mixed_int8_native_attention_shadow_hold |
| qkv8_q12_pwl_recip_q12_bucket8 | 8 | 8 | 8 | 12 | 12 | pwl_recip_lut_q12_bucket8 | 0.968750 | 1.000000 | 0.998607 | 0.014237 | mixed_int8_native_attention_shadow_hold |

## Primary Candidate Metrics

| comparisons | top1_match | topk_contains | mean_cosine | mean_kl | min_margin | max_delta |
|---:|---:|---:|---:|---:|---:|---:|
| 64 | 0.968750 | 1.000000 | 0.998607 | 0.014237 | 0.000000 | 5.250000 |

- decision: `mixed_int8_native_attention_shadow_hold`
- next_step: Hold this attention-shadow candidate until safer quantization is proven with a real checkpoint run or broader model sampling.

## Blockers

- attention-shadow top-rank drift is too large for quality-gate promotion

## Assumptions

- This is a native-checkpoint attention-shadow gate, not a full QAT or perplexity study.
- Teacher-forced next-token inputs isolate attention-path ranking drift from decoding-policy variance.
- Only Llama-style q/k/v projection + attention-softmax control is patched (QKV quantization + RTL-style int8 softmax).
- Q/K/V quantization and RTL softmax are applied in an in-process attention shadow, not reflected in training-time weights.

## Thresholds

- top1_match_min: `0.99`
- topk_contains_min: `0.995`
- mean_probability_kl_caution_above: `0.02`
- mean_logit_cosine_caution_below: `0.998`
- attention_shadow_only: `True`
- not_full_perplexity_gate: `True`
