# llm_decoder_attention_mixed_int8_score_margin_audit_llama7b_v1

- decision: `score_margin_audit_narrow_margin_hold`
- decision_counts: `{'score_margin_audit_pass': 1, 'score_margin_audit_narrow_margin_hold': 5, 'score_margin_audit_systematic_hold': 0, 'score_margin_audit_unknown': 0}`
- primary_candidate_id: `score32_float`
- candidate_count: `6`
- recommended_next_step: `The misses are concentrated in narrow-margin regions; keep this recovery path blocked until bounded top-k and follow-up scoring checks show stable high-margin behavior.`

## Candidates

| candidate_id | audit_status | top1_match | topk_contains | mean_cosine | mean_kl | max_delta | miss_count | miss_topk | miss_margin | miss_kl | miss_cosine | narrow_miss | bucketed_misses |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| score32_float | score_margin_audit_narrow_margin_hold | 0.968750 | 1.000000 | 0.999903 | 0.001412 | 0.531250 | 2 | 1.000000 | 0.125000 | 0.002997 | 0.999901 | 2 | 0_0.5:2, 0_5_1.0:0, 1.0_2.0:0, 2.0_4.0:0, >=4.0:0, negative:0 |
| qkv8_float_exact | score_margin_audit_pass | 1.000000 | 1.000000 | 0.999899 | 0.001243 | 0.527344 | 0 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0 | 0_0.5:0, 0_5_1.0:0, 1.0_2.0:0, 2.0_4.0:0, >=4.0:0, negative:0 |
| qkv8_q20_pwl_recip_q20_bucket8 | score_margin_audit_narrow_margin_hold | 0.968750 | 1.000000 | 0.999089 | 0.012515 | 2.187500 | 2 | 1.000000 | 0.187500 | 0.025779 | 0.998599 | 2 | 0_0.5:2, 0_5_1.0:0, 1.0_2.0:0, 2.0_4.0:0, >=4.0:0, negative:0 |
| score24_float | score_margin_audit_narrow_margin_hold | 0.968750 | 1.000000 | 0.999903 | 0.001412 | 0.531250 | 2 | 1.000000 | 0.125000 | 0.002997 | 0.999901 | 2 | 0_0.5:2, 0_5_1.0:0, 1.0_2.0:0, 2.0_4.0:0, >=4.0:0, negative:0 |
| score28_float | score_margin_audit_narrow_margin_hold | 0.968750 | 1.000000 | 0.999903 | 0.001412 | 0.531250 | 2 | 1.000000 | 0.125000 | 0.002997 | 0.999901 | 2 | 0_0.5:2, 0_5_1.0:0, 1.0_2.0:0, 2.0_4.0:0, >=4.0:0, negative:0 |
| qkv8_q16_pwl_recip_q16_bucket8 | score_margin_audit_narrow_margin_hold | 0.953125 | 1.000000 | 0.999090 | 0.012878 | 2.687500 | 3 | 1.000000 | 0.250000 | 0.038775 | 0.998389 | 3 | 0_0.5:3, 0_5_1.0:0, 1.0_2.0:0, 2.0_4.0:0, >=4.0:0, negative:0 |
