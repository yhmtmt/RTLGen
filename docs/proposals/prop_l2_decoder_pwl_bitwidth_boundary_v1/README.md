# Decoder PWL Integer Bit-Width Boundary

Proposal workspace for `prop_l2_decoder_pwl_bitwidth_boundary_v1`.

This job narrows the integer PWL precision boundary after q12 proved exact-safe
on the expanded v2 prompt distribution but expensive in Layer 1 PPA. It checks
whether q11 preserves exact next-token/top-k behavior before scheduling another
hardware calibration point.
