# LLM Decoder PWL Frontier Detail

## Goal
Break down the immediate decoder softmax frontier after the survivor cost proxy:

- `grid_approx_pwl_bf16_path`
- `grid_approx_pwl_in_q8_w_q8_norm_exact`

Both rows passed the prompt-stress next-token and top-k gates. The next decision is not another broad sweep; it is identifying which implementation risk dominates the close PWL frontier.

## Scope
This proposal adds a focused estimator that reports:

- PWL table bits
- interpolation multiplier and accumulator widths
- normalization implementation path
- format bridge cost
- integration-risk classification

The estimator is planning evidence only. It is not RTL, OpenROAD PPA, or final hardware acceptance.
