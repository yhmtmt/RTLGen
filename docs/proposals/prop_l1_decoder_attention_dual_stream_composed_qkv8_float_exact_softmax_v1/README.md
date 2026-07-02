# Composed qkv8 Float/Exact Softmax Wrapper

This proposal captures the next abstraction-removal step for the Llama7B
mixed/int8 attention frontier.

The current quality-backed candidate is `qkv8_float_exact`, with `score32_float`
also held by the native quality gate. The measured score32 exact-divider,
score32 reciprocal-LUT, q20/q24 PWL, and seqdiv composed wrappers are useful
fixed-point diagnostics, but they are not the quality-backed frontier after the
broad native quality gate. The `npu_fp16_cpp_nm*_softmaxcmp` rows are measured
hardware proxy rows, but they are `npu_top` configurations and do not embody the
q8/k8/v8 dual-stream composed attention wrapper.

The next physical job should therefore be blocked until the RTL generator has a
distinct composed-wrapper softmax mode for the quality-backed semantics. It
must not alias `qkv8_float_exact` to the existing integer `exact_div`,
`recip_lut`, or PWL implementations.

Minimum implementation requirements:

- Add an explicit semantic profile in the composed wrapper config, for example
  `semantic_profile=qkv8_float_exact` or `semantic_profile=score32_float`.
- Define the conversion boundary from q8/k8 score accumulation into the
  floating or near-exact softmax input.
- Define the probability representation used to multiply v8 values.
- Update the composed-wrapper guard so that this proposal cannot accidentally
  consume fixed-point/PWL or `npu_top` proxy metrics.
- Queue a single bounded L1 PPA run only after generator and guard support are
  available and the remote evaluator checkout is clean.

The dependent L2 recost should use the L1 metrics from that wrapper and mark the
result quality-backed by the existing `qkv8_float_exact`/`score32_float`
quality evidence.
