# Analysis Report

Pending evaluator results for `l2_decoder_pwl_survivor_distribution_v1`.

The expected interpretation is:

- exact-safe q12/unquantized PWL: promote survivor rows to RTL/PPA calibration
- top-k-safe but not exact-safe q12 PWL: inspect category misses and margins
- q12 PWL broad failure: return to PWL curve or precision design before hardware
