# Decoder bf16/PWL Recovery

- source_sweep: `runs/datasets/llm_decoder_eval_trained_tiny_v1/decoder_quality_sweep__l2_decoder_trained_tiny_quality_v1.json`
- decision: `tie_break_recovery_sufficient`
- exact_safe_after_recovery: `True`
- recovered_count: 1
- regression_count: 0
- recommended_next_step: Treat bf16/PWL as the immediate low-cost frontier and follow with a hardware-friendly score-tie ranking check before full QAT infrastructure.

## Mechanism

This is a narrow QAT/calibration proxy. It does not update weights; it checks whether the bf16/PWL exact-next losses are pure equal-score ranking losses that a tiny logit-preserving calibration could recover.

## Quality

| template | next-token | top-k | mismatches |
|---|---:|---:|---|
| `grid_approx_pwl_bf16_path` | 23/24 | 23/24 | `trained_color_sky` |
| `grid_approx_pwl_bf16_path_logit_tiebreak` | 24/24 | 24/24 |  |

- recovered_sample_ids: `trained_color_sky`
- regression_sample_ids:
