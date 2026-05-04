# Decoder bf16/PWL Recovery

- source_sweep: `runs/datasets/llm_decoder_eval_gpt2_trained_v1/decoder_quality_sweep__l2_decoder_gpt2_quality_v1.json`
- decision: `baseline_exact_safe`
- exact_safe_after_recovery: `True`
- recovered_count: 0
- regression_count: 0
- recommended_next_step: Treat bf16/PWL as exact-safe on this screen without relying on the logit tie-breaker; keep the tie-break row as a ranking-stability guard for broader prompts or larger checkpoints.

## Mechanism

This is a narrow QAT/calibration proxy. It does not update weights; it checks whether the bf16/PWL exact-next losses are pure equal-score ranking losses that a tiny logit-preserving calibration could recover.

## Quality

| template | next-token | top-k | mismatches |
|---|---:|---:|---|
| `grid_approx_pwl_bf16_path` | 24/24 | 24/24 |  |
| `grid_approx_pwl_bf16_path_logit_tiebreak` | 24/24 | 24/24 |  |

- recovered_sample_ids: 
- regression_sample_ids:
