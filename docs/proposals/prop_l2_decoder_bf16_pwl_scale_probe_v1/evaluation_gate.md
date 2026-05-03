# Evaluation Gate

Pass criteria:

- `grid_approx_pwl_bf16_path_logit_tiebreak` has no next-token mismatches.
- `grid_approx_pwl_bf16_path_logit_tiebreak` has no top-k misses.
- Any remaining bf16/PWL baseline misses are recovered without regressions.
- q12 and q8 controls are retained in the sweep output for interpretation.

If the recovered bf16 row fails, do not promote the tie-rank path as broadly
robust. Move to larger-model diagnosis or train-aware recovery before further
datapath spending.
