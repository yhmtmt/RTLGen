# Decoder distilgpt2 Prompt-Stress Gate

- `proposal_id`: `prop_l2_decoder_distilgpt2_prompt_stress_v1`
- `item_id`: `l2_decoder_distilgpt2_prompt_stress_v1`
- abstraction: `decoder_distilgpt2_prompt_stress`

## Motivation

The first distilgpt2 gate reported `baseline_exact_safe` for bf16/PWL on a
24-prompt screen. That is useful frontier evidence, but approximation behavior
depends on prompt distribution, entropy, and top-1/top-2 margin. Before moving
to GPT-2 scale, training recovery, or larger-array conclusions, the same
checkpoint should be stressed with a broader prompt set.

## Evaluation Shape

This job materializes `distilgpt2` locally in the evaluator workspace, writes a
separate prompt-stress dataset manifest, generates fresh reference/candidate
traces, runs `decoder_bf16_pwl_scale_probe_v1`, and summarizes the bf16/PWL
baseline and logit tie-break rows.

The committed result must include:

- `decoder_quality_sweep__l2_decoder_distilgpt2_prompt_stress_v1.json`
- `decoder_distilgpt2_prompt_stress__l2_decoder_distilgpt2_prompt_stress_v1.json`
- `decoder_distilgpt2_prompt_stress__l2_decoder_distilgpt2_prompt_stress_v1.md`

## Interpretation

Passing this job still does not prove model-family-wide robustness. It only
checks whether the current distilgpt2 exact-safe result survives a broader
prompt/input distribution. Failures should be analyzed by category and
logit-margin regime before hardware narrowing.
