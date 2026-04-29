# Implementation Summary

- Extend `npu/eval/run_llm_decoder_onnx_candidate.py` with software-emulated
  fp-like quantization formats:
  - `fp16`
  - `bf16`
  - `fp8_e5m2`
  - `fp8_e4m3`
- Add backend config fields for fp-like quantization at logits, softmax inputs,
  softmax weights, reciprocal normalization, and final probabilities.
- Extend `npu/eval/sweep_llm_decoder_candidate_quality.py` with
  `--rough-grid decoder_probability_fp_formats_v1`.
- Add `decoder_probability_fp_sensitivity` evidence generation to the L2 task
  generator.

## Local Preview

The local preview over the pinned tiny decoder benchmark produced 17 templates.
The exact, fp16, bf16, and fp-like PWL paths preserved `1.0` next-token/top-k
quality. The fp8 probes exposed rough cliffs: `logits_fp8_e5m2` and
`prob_fp8_e5m2` missed `math_two_plus_two`, while `prob_fp8_e4m3` underflowed
too aggressively and missed all samples. This preview verifies artifact shape
and dynamic-range behavior before evaluator execution.
