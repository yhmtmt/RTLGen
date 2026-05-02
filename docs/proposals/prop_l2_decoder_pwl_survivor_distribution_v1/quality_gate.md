# Quality Gate

The evaluation should:

- regenerate the expanded v2 distribution reference and candidate manifests
- run the `decoder_pwl_survivor_distribution_v1` rough grid
- report exact next-token and top-k preservation for every row
- group exact-token misses by prompt category
- identify whether q12/unquantized/fp16-style PWL rows are broad exact-safe

Acceptance is a complete broad-distribution quality artifact. Hardware
acceptance still requires a follow-up RTL/PPA calibration for any survivor.
