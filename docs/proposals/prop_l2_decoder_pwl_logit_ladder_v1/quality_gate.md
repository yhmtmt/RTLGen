# Quality Gate

The evaluation should:

- regenerate the six-sample focus reference and candidate manifests
- run the `decoder_pwl_logit_sensitivity_ladder_v1` rough grid
- report exact next-token and top-k preservation for each precision row
- explicitly separate focus misses from control misses
- conclude whether the failure mechanism is core PWL approximation, softmax
  input/weight precision, logit precision, normalization precision, or mixed

Acceptance is a complete focused ladder artifact. It should not claim broad
distribution robustness for any recovered row.
