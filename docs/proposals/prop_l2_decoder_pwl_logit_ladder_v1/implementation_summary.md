# Implementation Summary

- Added a six-sample PWL failure focus manifest using the two broad-v2 shared
  misses and four nearby arithmetic/list controls.
- Added the `decoder_pwl_logit_sensitivity_ladder_v1` rough grid to the decoder
  sweep tool.
- Added `summarize_llm_decoder_pwl_logit_ladder.py` to produce JSON/Markdown
  mechanism diagnosis from the ladder sweep.
- Added a Layer-2 task-generator abstraction,
  `decoder_pwl_logit_sensitivity_ladder`, with unit coverage.
