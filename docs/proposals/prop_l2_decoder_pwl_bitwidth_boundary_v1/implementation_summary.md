# Implementation Summary

- Added the `decoder_pwl_bitwidth_boundary_v1` rough grid with q10/q11/q12/q13
  exact-logit and PWL exact-normalization rows.
- Added `summarize_llm_decoder_pwl_bitwidth_boundary.py` to report the minimum
  exact-safe and top-k-safe integer PWL bit widths.
- Registered `decoder_pwl_bitwidth_boundary` in the Layer 2 task generator.
