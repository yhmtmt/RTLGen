# Implementation Summary

- Extend `npu/eval/sweep_llm_decoder_candidate_quality.py` with
  `--rough-grid decoder_probability_broad_v1`.
- Generate coarse candidate backend configs from existing exact and approximate
  decoder templates instead of checking in many permanent model-contract
  templates.
- Record per-template quality, tensor drift rollups, and sample IDs where
  next-token or top-k matching fails.
- Add `decoder_probability_sensitivity` evidence generation to the L2 task
  generator.

## Local Preview

The local preview over the pinned tiny decoder benchmark produced a mixed map:
several exact/q8/q6/PWL points preserved `1.0`, while q4 and final probability
quantization points exposed quality cliffs. This preview is used only to confirm
the artifact shape before evaluator execution.
