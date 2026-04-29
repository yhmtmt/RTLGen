# LLM Decoder q8 Normalization Frontier

## Goal
Test the q8-specific blocker isolated by the PWL frontier detail job: exact normalization.

The job compares:

- `grid_approx_pwl_bf16_path`
- `grid_approx_pwl_in_q8_w_q8_norm_exact`
- `grid_approx_pwl_in_q8_w_q8_norm_recip_q10`
- `grid_approx_pwl_in_q8_w_q8_norm_recip_q12`
- `grid_approx_pwl_in_q8_w_q8_norm_recip_q14`
- `grid_approx_pwl_in_q8_w_q8_norm_recip_q16`

## Scope
This is a prompt-stress quality and planning-cost check. It does not claim real RTL/OpenROAD PPA.
