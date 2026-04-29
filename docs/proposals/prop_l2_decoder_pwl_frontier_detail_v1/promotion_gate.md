# Promotion Gate

Promote only as planning evidence unless a later job adds RTL/OpenROAD results.

The desired promotion outcome is a narrowed next implementation step:

- primary anchor: `grid_approx_pwl_bf16_path`
- alternate frontier: `grid_approx_pwl_in_q8_w_q8_norm_exact`
- explicit blocker to investigate: q8 exact normalization
