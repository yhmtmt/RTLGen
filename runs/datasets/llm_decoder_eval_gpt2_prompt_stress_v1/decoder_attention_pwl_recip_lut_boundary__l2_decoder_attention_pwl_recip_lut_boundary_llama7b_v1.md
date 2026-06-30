# Attention PWL Reciprocal-LUT Boundary

- decision: `compact_reciprocal_required_for_widest_points`
- candidate_count: `3`
- warning_cases: `8192`
- blocking_cases: `65536`

## Candidates

| candidate_id | score_bits | weight_bits | recip_bits | bucket_shift | cases | rom_bits | verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| qkv8_q12_pwl_recip_q12_bucket8 | 12 | 12 | 12 | 8 | 128 | 3072 | direct_lut_ppa_reasonable |
| qkv8_q20_pwl_recip_q20_bucket8 | 20 | 20 | 20 | 8 | 32768 | 1310720 | boundary_probe_only |
| qkv8_q24_pwl_recip_q24_bucket8 | 24 | 24 | 24 | 8 | 524288 | 25165824 | requires_compact_reciprocal_before_ppa |

## Notes

- Case counts are generated-Verilog reciprocal denominator cases for the current direct-LUT PWL implementation.
- This is a synthesis-risk guardrail, not a PPA result.
