# Quality-Backed Composed Softmax Contract

This contract keeps the next Llama7B mixed/int8 PPA job aligned with the
quality evidence. It is intentionally stricter than the existing fixed-point
diagnostic wrappers.

## Current Evidence

- `qkv8_float_exact` is the only broad native attention-shadow passing
  candidate in
  `runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_broad_native_quality__l2_decoder_attention_mixed_int8_broad_native_quality_llama7b_v1_r2.json`.
- `score32_float` passed the bounded generation/NLL gate in
  `runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_generation_quality__l2_decoder_attention_mixed_int8_generation_quality_llama7b_v1_r3.json`,
  but it is not a measured composed hardware datapath.
- `score32_w16_rtl_exact` failed the generation-quality gate in
  `runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_score32_w16_rtl_exact_generation_quality__l2_decoder_attention_mixed_int8_score32_w16_rtl_exact_generation_quality_llama7b_v1.json`.
  Therefore a W16 integer-probability exact-divider row must remain diagnostic
  unless a matching quality gate passes later.

## Required Composed Hardware Semantics

A quality-backed composed wrapper must include all of these inside
`attention_dual_stream_composed`, not as an `npu_top` proxy row:

- q8/k8 score production and v8 value consumption in the composed wrapper.
- An explicit score conversion boundary:
  - `qkv8_float_exact`: score is converted to a floating representation before
    row softmax. The probability representation must also remain floating, or
    the quantized probability replacement must have its own quality gate.
  - `score32_float`: score is quantized to signed fixed-point S32 using the
    native evaluator's score boundary, then the row softmax is still true
    exponential softmax over that dequantized score. A W16 output weight is not
    equivalent to this candidate unless separately quality-backed.
- Row max, exponential approximation or implementation, row sum, reciprocal or
  divider, and probability-by-v8 multiply must all be part of the measured RTL
  boundary.
- The generated manifest must record:
  - `semantic_profile`
  - `quality_source_candidate_id`
  - score representation and fractional scale
  - probability representation
  - exp implementation family
  - divider or reciprocal implementation family

## Non-Substitutable Rows

These rows can inform cost and timing trends, but cannot rank the
quality-backed frontier:

- `score32_w16_exact_div`
- `score32_w16_recip_lut_q16`
- `q12_pwl_recip_lut`
- `q20_pwl_recip_lut`
- `q20_pwl_recip_div`
- `q20_pwl_recip_seqdiv`
- `q24_pwl_recip_div`
- `q24_pwl_recip_seqdiv`
- `npu_fp16_cpp_nm*_softmaxcmp`

The first eight are fixed-point/PWL diagnostic composed wrappers. The
`npu_fp16_cpp_nm*_softmaxcmp` rows are `npu_top` proxy rows and do not embody
the q8/k8/v8 composed attention wrapper.

## Next Implementable Target

The next implementation should not reuse `softmax_impl=exact_div`,
`recip_lut`, or any PWL implementation with a quality-backed semantic profile.
It should introduce a distinct composed softmax implementation, for example a
range-reduced exp datapath plus exact divider or sequential divider, and pair it
with a native quality candidate that matches the same output probability
representation.

The first PPA job should remain blocked until both are true:

- the generator emits the distinct implementation and manifest fields above;
- the matching native quality/equivalence gate passes for that exact score and
  probability representation.
