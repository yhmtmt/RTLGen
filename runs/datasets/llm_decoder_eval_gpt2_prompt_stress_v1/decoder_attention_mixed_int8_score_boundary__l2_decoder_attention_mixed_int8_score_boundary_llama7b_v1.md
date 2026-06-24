# Native-Checkpoint Mixed/Int8 Attention Shadow Quality

- model_id: `mistralai/Mistral-7B-v0.1`
- decision: `mixed_int8_native_attention_shadow_hold`
- best_candidate: `score10_float` (mixed_int8_native_attention_shadow_hold)
- attention_head_count: `32`
- kv_head_count: `8`
- gqa_group_size: `4.0`
- expected_gqa_group_size: `4`

## Candidates

| candidate_id | q_bits | k_bits | v_bits | score_bits | weight_bits | softmax_mode | top1_match | topk_contains | mean_cosine | mean_kl | decision |
|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|---|
| score10_float | 8 | 8 | 8 | 10 | 16 | float_quantized | 0.687500 | 1.000000 | 0.976450 | 0.429103 | mixed_int8_native_attention_shadow_hold |
| score12_float | 8 | 8 | 8 | 12 | 16 | float_quantized | 0.687500 | 1.000000 | 0.976236 | 0.425982 | mixed_int8_native_attention_shadow_hold |
| score14_float | 8 | 8 | 8 | 14 | 16 | float_quantized | 0.687500 | 1.000000 | 0.976444 | 0.428338 | mixed_int8_native_attention_shadow_hold |
| score16_float | 8 | 8 | 8 | 16 | 16 | float_quantized | 0.687500 | 1.000000 | 0.976363 | 0.427910 | mixed_int8_native_attention_shadow_hold |
| score10_rtl_exact | 8 | 8 | 8 | 10 | 8 | rtl_exact | 0.562500 | 0.750000 | 0.940594 | 0.934051 | mixed_int8_native_attention_shadow_hold |
| score12_rtl_exact | 8 | 8 | 8 | 12 | 8 | rtl_exact | 0.562500 | 0.750000 | 0.938852 | 0.988033 | mixed_int8_native_attention_shadow_hold |
| score14_rtl_exact | 8 | 8 | 8 | 14 | 8 | rtl_exact | 0.562500 | 0.750000 | 0.939497 | 0.987099 | mixed_int8_native_attention_shadow_hold |
| score16_rtl_exact | 8 | 8 | 8 | 16 | 8 | rtl_exact | 0.562500 | 0.750000 | 0.939312 | 0.985517 | mixed_int8_native_attention_shadow_hold |

## Primary Candidate Metrics

| comparisons | top1_match | topk_contains | mean_cosine | mean_kl | min_margin | max_delta |
|---:|---:|---:|---:|---:|---:|---:|
| 16 | 0.562500 | 0.750000 | 0.938852 | 0.988033 | 0.000000 | 10.398438 |

- decision: `mixed_int8_native_attention_shadow_hold`
- next_step: Hold this attention-shadow candidate until safer quantization is proven with a real checkpoint run or broader model sampling.

## Blockers

- attention-shadow top-rank drift is too large for quality-gate promotion

## Cautions

- probability KL is above the mixed/int8 attention shadow comfort band
- average logit cosine dropped below the mixed/int8 attention shadow caution line

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
