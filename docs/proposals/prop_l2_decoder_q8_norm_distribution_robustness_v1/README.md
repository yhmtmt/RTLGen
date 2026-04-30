# Decoder q8/bf16 Normalization Distribution Robustness

Proposal workspace for `prop_l2_decoder_q8_norm_distribution_robustness_v1`.

This job runs the q8 normalization frontier grid on the broader decoder
distribution dataset, using merged PPA evidence for q8 reciprocal, q8 exact, and
bf16 reciprocal normalization. The goal is to check whether the prompt-stress
frontier remains quality-safe when prompt/logit distributions change.
