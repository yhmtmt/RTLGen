# Quality Gate

The frontier-detail job must preserve the inherited prompt-stress quality gate:

- `grid_approx_pwl_bf16_path` has 24/24 next-token matches and 24/24 top-k containment.
- `grid_approx_pwl_in_q8_w_q8_norm_exact` has 24/24 next-token matches and 24/24 top-k containment.

The job should not promote a candidate if either row loses exact-safe status in the source sweep.
