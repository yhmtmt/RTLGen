# Implementation Summary

- Added `estimate_llm_decoder_bf16_recoverability.py` to quantify bf16/PWL
  score gaps for exact-next misses.
- Registered `decoder_bf16_pwl_recoverability` in the Layer 2 task generator.
- Added proposal docs and tests for the report and generated task manifest.
