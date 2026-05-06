# Decoder Logit Rank Wide Scaling

This proposal extends the merged Layer 1 decoder logit-rank scaling point from
row-16/row-32 to row-64/row-128.

The target is measurement only. The result should provide measured Nangate45 PPA
for the current L2 streaming frontier widths, replacing the scaled-proxy data
used for `w64` and `w128` candidates.

Requested item:

- `l1_decoder_logit_rank_wide_scale_v1`

Requested configs:

- `runs/designs/activations/logit_rank_r64_l16_k1_wrapper/config_logit_rank_r64_l16_k1.json`
- `runs/designs/activations/logit_rank_r64_l16_k4_wrapper/config_logit_rank_r64_l16_k4.json`
- `runs/designs/activations/logit_rank_r128_l16_k1_wrapper/config_logit_rank_r128_l16_k1.json`
- `runs/designs/activations/logit_rank_r128_l16_k4_wrapper/config_logit_rank_r128_l16_k4.json`
