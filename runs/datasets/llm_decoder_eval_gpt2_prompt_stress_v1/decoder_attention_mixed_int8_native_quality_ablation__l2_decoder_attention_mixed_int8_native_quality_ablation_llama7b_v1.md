# Native-Checkpoint Mixed/Int8 Attention Shadow Quality

- model_id: `mistralai/Mistral-7B-v0.1`
- decision: `mixed_int8_native_attention_shadow_hold`
- best_candidate: `qkv8_float_softmax` (mixed_int8_native_attention_shadow_pass)
- attention_head_count: `32`
- kv_head_count: `8`
- gqa_group_size: `4.0`
- expected_gqa_group_size: `4`

## Candidates

| candidate_id | q_bits | k_bits | v_bits | score_bits | weight_bits | softmax_mode | top1_match | topk_contains | mean_cosine | mean_kl | decision |
|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|---|
| qkv8_float_softmax | 8 | 8 | 8 | 24 | 16 | float_quantized | 1.000000 | 1.000000 | 0.999959 | 0.000579 | mixed_int8_native_attention_shadow_pass |
| qkv8_score8_float_softmax | 8 | 8 | 8 | 8 | 16 | float_quantized | 0.687500 | 1.000000 | 0.975774 | 0.426622 | mixed_int8_native_attention_shadow_hold |
| qkv8_score8_rtl_exact | 8 | 8 | 8 | 8 | 8 | rtl_exact | 0.625000 | 0.812500 | 0.944779 | 0.919486 | mixed_int8_native_attention_shadow_hold |
| qkv8_score8_rtl_recip_q8 | 8 | 8 | 8 | 8 | 8 | rtl_recip_lut_q8 | 0.625000 | 0.750000 | 0.943892 | 1.013942 | mixed_int8_native_attention_shadow_hold |

## Primary Candidate Metrics

| comparisons | top1_match | topk_contains | mean_cosine | mean_kl | min_margin | max_delta |
|---:|---:|---:|---:|---:|---:|---:|
| 16 | 0.625000 | 0.750000 | 0.943892 | 1.013942 | 0.000000 | 10.125000 |

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
