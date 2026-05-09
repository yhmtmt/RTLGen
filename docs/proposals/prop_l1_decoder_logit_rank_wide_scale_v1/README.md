# Decoder Logit Rank Wide Scaling

This proposal extends the merged Layer 1 decoder logit-rank scaling point from
row-16/row-32 to row-64/row-128.

The target is measurement only. The result should provide measured Nangate45 PPA
for the current L2 streaming frontier widths, replacing the scaled-proxy data
used for `w64` and `w128` candidates.

Requested item:

- `l1_decoder_logit_rank_wide_scale_v1`
- `l1_decoder_logit_rank_r128_k1_pin_perimeter_bound_v1`

Requested configs:

- `runs/designs/activations/logit_rank_r64_l16_k1_wrapper/config_logit_rank_r64_l16_k1.json`
- `runs/designs/activations/logit_rank_r64_l16_k4_wrapper/config_logit_rank_r64_l16_k4.json`
- `runs/designs/activations/logit_rank_r128_l16_k1_wrapper/config_logit_rank_r128_l16_k1.json`
- `runs/designs/activations/logit_rank_r128_l16_k4_wrapper/config_logit_rank_r128_l16_k4.json`

Pin-perimeter diagnostic:

- `l1_decoder_logit_rank_wide_scale_macro_pins_v2` showed that
  `logit_rank_r128_l16_k1_wrapper` still fails at OpenROAD `3_2_place_iop`
  after dense macro-pin placement is enabled.
- The failing PPL-0024 report says 2072 pins require `2320.64um` die
  perimeter. For a square diagnostic block, the minimum side bound is
  `ceil(2320.64 / 4) = 581um`.
- `runs/campaigns/activations/logit_rank_scale/sweeps/nangate45_r128_k1_pin_perimeter_bound.json`
  evaluates a below-bound control at `540um`, the computed bound at `581um`,
  and a margin point at `640um`.
- The resulting die area is artificial perimeter padding. Use the sweep to
  separate pin-capacity failure from later placement/timing/routing behavior,
  not to rank `r128/k1` area against utilization-derived PPA rows.
