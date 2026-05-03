# Decoder bf16/PWL Recoverability

- source_sweep: `runs/datasets/llm_decoder_eval_tiny_v1/decoder_quality_sweep__l2_decoder_q8_norm_distribution_broad_v2.json`
- template: `grid_approx_pwl_bf16_path`
- decision: `recoverable_margin_shift`
- next-token: 46/48
- top-k: 48/48
- summary: Recoverability is estimated from the score gap required to move the exact-reference token back to top-1 in the bf16/PWL candidate output. This is not training proof; it is a margin screen for whether a QAT/fine-tuning experiment is worth running.
- recommended_next_step: Prototype bf16/PWL-aware fine-tuning or QAT before spending more exact-safe integer PPA effort.

## Correct-Sample Margins

| count | min | p25 | median | p90 | max |
|---:|---:|---:|---:|---:|---:|
| 46 | 1.2665987e-07 | 7.6554716e-07 | 3.3155084e-06 | 7.3928386e-06 | 1.2207776e-05 |

## Miss Recovery Gaps

| sample | category | rank | wrong token | reference token | gap | class |
|---|---|---:|---|---|---:|---|
| `dist2_arith_three_plus_five` | `arithmetic_short` | 2 | ` =` | ` footsteps` | 0 | `easy_rank2_below_median_margin` |
| `dist2_sequence_months` | `list_continuation` | 2 | `,` | ` Drinking` | 0 | `easy_rank2_below_median_margin` |
