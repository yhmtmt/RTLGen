# Decoder bf16/PWL Recovery

- source_sweep: `runs/datasets/llm_decoder_eval_tiny_v1/decoder_quality_sweep__l2_decoder_bf16_pwl_recovery_v1.json`
- decision: `tie_break_recovery_sufficient`
- exact_safe_after_recovery: `True`
- recovered_count: 2
- regression_count: 0
- recommended_next_step: Treat bf16/PWL as the immediate low-cost frontier and follow with a hardware-friendly score-tie ranking check before full QAT infrastructure.

## Mechanism

This is a narrow QAT/calibration proxy. It does not update weights; it checks whether the bf16/PWL exact-next losses are pure equal-score ranking losses that a tiny logit-preserving calibration could recover.

## Quality

| template | next-token | top-k | mismatches |
|---|---:|---:|---|
| `grid_approx_pwl_bf16_path` | 46/48 | 48/48 | `dist2_arith_three_plus_five`, `dist2_sequence_months` |
| `grid_approx_pwl_bf16_path_logit_tiebreak` | 48/48 | 48/48 |  |

- recovered_sample_ids: `dist2_arith_three_plus_five`, `dist2_sequence_months`
- regression_sample_ids:
