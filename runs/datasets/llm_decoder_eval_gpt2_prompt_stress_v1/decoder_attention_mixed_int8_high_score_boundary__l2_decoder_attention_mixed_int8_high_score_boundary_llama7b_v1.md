# Native-Checkpoint Mixed/Int8 Attention Shadow Quality

- model_id: `mistralai/Mistral-7B-v0.1`
- decision: `mixed_int8_native_attention_shadow_pass`
- best_candidate: `score24_float` (mixed_int8_native_attention_shadow_pass)
- attention_head_count: `32`
- kv_head_count: `8`
- gqa_group_size: `4.0`
- expected_gqa_group_size: `4`

## Candidates

| candidate_id | q_bits | k_bits | v_bits | score_bits | weight_bits | softmax_mode | top1_match | topk_contains | mean_cosine | mean_kl | decision |
|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|---|
| score18_float | 8 | 8 | 8 | 18 | 16 | float_quantized | 0.687500 | 1.000000 | 0.976402 | 0.430227 | mixed_int8_native_attention_shadow_hold |
| score20_float | 8 | 8 | 8 | 20 | 16 | float_quantized | 0.687500 | 1.000000 | 0.976310 | 0.431272 | mixed_int8_native_attention_shadow_hold |
| score22_float | 8 | 8 | 8 | 22 | 16 | float_quantized | 0.687500 | 1.000000 | 0.976235 | 0.429326 | mixed_int8_native_attention_shadow_hold |
| score24_float | 8 | 8 | 8 | 24 | 16 | float_quantized | 1.000000 | 1.000000 | 0.999959 | 0.000579 | mixed_int8_native_attention_shadow_pass |
| score18_rtl_exact | 8 | 8 | 8 | 18 | 8 | rtl_exact | 0.562500 | 0.750000 | 0.939312 | 0.985517 | mixed_int8_native_attention_shadow_hold |
| score20_rtl_exact | 8 | 8 | 8 | 20 | 8 | rtl_exact | 0.562500 | 0.750000 | 0.939312 | 0.985517 | mixed_int8_native_attention_shadow_hold |
| score22_rtl_exact | 8 | 8 | 8 | 22 | 8 | rtl_exact | 0.562500 | 0.750000 | 0.939312 | 0.985517 | mixed_int8_native_attention_shadow_hold |
| score24_rtl_exact | 8 | 8 | 8 | 24 | 8 | rtl_exact | 0.687500 | 1.000000 | 0.967328 | 0.434194 | mixed_int8_native_attention_shadow_hold |
| qkv8_float_exact | 8 | 8 | 8 | 24 | 16 | float_exact | 1.000000 | 1.000000 | 0.999959 | 0.000529 | mixed_int8_native_attention_shadow_pass |

## Primary Candidate Metrics

| comparisons | top1_match | topk_contains | mean_cosine | mean_kl | min_margin | max_delta |
|---:|---:|---:|---:|---:|---:|---:|
| 16 | 1.000000 | 1.000000 | 0.999959 | 0.000579 | 0.000000 | 0.437500 |

- decision: `mixed_int8_native_attention_shadow_pass`
- next_step: Proceed to broader mixed/int8 attention native-checkpoint checks before frontier scheduling.

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
