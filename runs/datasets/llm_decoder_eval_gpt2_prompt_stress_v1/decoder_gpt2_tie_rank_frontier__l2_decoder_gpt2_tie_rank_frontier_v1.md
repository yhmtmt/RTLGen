# Decoder bf16/PWL Tie-Rank Frontier

- source_recovery: `runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_gpt2_prompt_stress__l2_decoder_gpt2_prompt_stress_v1.json`
- decision: `hardware_recovery_plausible`
- selected_candidate: `grid_approx_pwl_bf16_path_logit_tiebreak`
- reason: The GPT-2 prompt-stress misses are recovered by logit tie-rank, no regressions are present, and both bf16 reciprocal normalization and score tie-rank have merged Nangate45 physical metrics.

## Quality Gate

- baseline: 94/96 next-token, 96/96 top-k
- recovery: 96/96 next-token, 96/96 top-k
- recovered_sample_ids: `gpt2_stress_geo_australia_capital, gpt2_stress_math_four_times_five`
- regression_sample_ids: `none`

## Component PPA

| path | critical_path_ns | die_area | total_power_mw |
|---|---:|---:|---:|
| recovered bf16 reciprocal + score tie-rank | 7.5794 | 57476.735425 | 0.01005 |

## Incremental Cost Versus bf16 Reciprocal

| metric | absolute | relative % |
|---|---:|---:|
| critical_path_ns | 3.2925 | 76.804 |
| die_area | 6786.4644 | 13.388 |
| total_power_mw | 0.00526 | 109.812 |

## Next Step

- Use this as a hardware-plausibility gate for bf16/PWL score-tie recovery, not as full-array proof.
- If larger-model or larger-array prompt stress breaks this gate, move to QAT or richer calibration.
