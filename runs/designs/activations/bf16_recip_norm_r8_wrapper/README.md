# bf16 Reciprocal Normalization r8

This design is a Layer 1 PPA proxy for the missing bf16 normalization cost in the decoder frontier.

The block accepts eight packed IEEE bf16 lanes. Positive finite lanes are converted to a fixed-point
Q format, summed, multiplied by a bucketed reciprocal lookup, clamped to `[0, 1]`, and converted back
to bf16. Negative values, subnormals, NaNs, and infinities are intentionally clamped because the block
is meant to measure the reciprocal-normalization datapath rather than full IEEE exception handling.
