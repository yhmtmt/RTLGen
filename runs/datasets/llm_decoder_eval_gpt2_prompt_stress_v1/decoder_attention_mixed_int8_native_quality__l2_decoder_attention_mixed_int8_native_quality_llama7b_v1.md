# Native-Checkpoint Mixed/Int8 Attention Shadow Quality

- model_id: `mistralai/Mistral-7B-v0.1`
- decision: `mixed_int8_native_attention_shadow_hold`
- attention_head_count: `32`
- kv_head_count: `8`
- gqa_group_size: `4.0`
- expected_gqa_group_size: `4`

## Candidate

- q_bits: `8`
- k_bits: `8`
- v_bits: `8`
- score_bits: `8`
- weight_bits: `8`
- softmax_mode: `rtl_recip_lut_q8`

## Candidate Metrics

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
